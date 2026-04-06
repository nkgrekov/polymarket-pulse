#!/usr/bin/env python3
import argparse
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


SQL_PUBLIC_OBJECTS = """
select
  n.nspname as schema_name,
  c.relname as object_name,
  c.relkind,
  coalesce(c.relrowsecurity, false) as rls_enabled,
  coalesce(c.relforcerowsecurity, false) as rls_forced,
  coalesce(c.reloptions::text, '') as reloptions
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public'
  and c.relkind in ('r', 'v', 'm')
order by c.relkind, c.relname;
"""


SQL_PUBLIC_GRANTS = """
select
  table_schema,
  table_name,
  grantee,
  privilege_type
from information_schema.role_table_grants
where table_schema = 'public'
  and grantee in ('anon', 'authenticated', 'service_role', 'postgres')
order by table_name, grantee, privilege_type;
"""


PRIORITY_CLOSE = {
    "watchlist",
    "watchlist_markets",
    "watchlist_snapshot_latest",
    "watchlist_alerts_latest",
    "alerts_latest",
    "alerts_inbox_latest",
    "v_watchlist_tokens",
    "v_watchlist_movers_1h",
    "portfolio_snapshot_latest",
}

PRIORITY_KEEP_PUBLIC = {
    "top_movers_latest",
    "top_movers_1h",
    "global_bucket_latest",
    "buckets_latest",
    "snapshot_health",
    "hot_ingest_health_latest",
}


def bullet(label: str, value: str) -> str:
    return f"- {label}: **{value}**"


def classify_object(name: str) -> str:
    if name in PRIORITY_CLOSE:
        return "close-first"
    if name in PRIORITY_KEEP_PUBLIC:
        return "keep-public-review-grants"
    return "review"


def priority_findings(anon_objects: int, auth_objects: int) -> list[str]:
    if anon_objects == 0 and auth_objects == 0:
        return [
            "- `anon` and `authenticated` no longer have grants on the audited `public` relations in this snapshot.",
            "- the remaining risk is structural rather than grant-based:",
            "  - legacy public tables still have RLS disabled",
            "  - Supabase Security Advisor can still complain about view semantics in `public`",
            "- `public.watchlist_markets` remains suspicious legacy drift because it exists live in the database but is not clearly managed in current repo migrations.",
            "- the next security work should focus on legacy drift cleanup and whether any remaining public views need `security_invoker = true` or a schema move.",
        ]
    return [
        "- `anon` and `authenticated` currently have broad grants on many `public` views and tables, not just read-only analytics surfaces.",
        "- legacy watchlist / alert relations in `public` are the highest-risk objects because they look user-specific yet sit in the public schema with open grants.",
        "- `SECURITY DEFINER`-style advisor noise matters more here because underlying grants are also too broad.",
        "- `public.watchlist_markets` is especially suspicious because it is live in the database but not managed in current repo migrations.",
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Supabase public schema security posture.")
    parser.add_argument("--output", default="docs/supabase_public_security_latest.md")
    args = parser.parse_args()

    pg = os.environ.get("PG_CONN", "")
    if not pg:
        raise SystemExit("PG_CONN is required")

    with psycopg.connect(pg) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(SQL_PUBLIC_OBJECTS)
            objects = cur.fetchall()
            cur.execute(SQL_PUBLIC_GRANTS)
            grants = cur.fetchall()

    grants_by_object: dict[str, list[dict]] = defaultdict(list)
    for row in grants:
        grants_by_object[row["table_name"]].append(row)

    now = datetime.now(timezone.utc).isoformat()
    lines: list[str] = [
        f"# Supabase Public Security Snapshot ({now})",
        "",
        "Source:",
        "",
        "- `pg_class` / `pg_namespace` for public relations",
        "- `information_schema.role_table_grants` for public grants",
        "",
        "## Summary",
        "",
    ]

    public_objects = len(objects)
    anon_objects = len({row["table_name"] for row in grants if row["grantee"] == "anon"})
    auth_objects = len({row["table_name"] for row in grants if row["grantee"] == "authenticated"})
    rls_disabled_tables = [
        row for row in objects if row["relkind"] == "r" and not row["rls_enabled"]
    ]
    lines.extend(
        [
            bullet("public_objects", str(public_objects)),
            bullet("objects_granted_to_anon", str(anon_objects)),
            bullet("objects_granted_to_authenticated", str(auth_objects)),
            bullet("rls_disabled_public_tables", str(len(rls_disabled_tables))),
            "",
            "## Priority Findings",
            "",
        ]
    )
    lines.extend(priority_findings(anon_objects, auth_objects))
    lines.extend(
        [
            "",
            "## Object Inventory",
            "",
        ]
    )

    for row in objects:
        name = row["object_name"]
        relkind = row["relkind"]
        kind = {"r": "table", "v": "view", "m": "materialized_view"}.get(relkind, relkind)
        rel_grants = grants_by_object.get(name, [])
        grant_summary = ", ".join(
            f"{g['grantee']}:{g['privilege_type']}" for g in rel_grants if g["grantee"] in {"anon", "authenticated"}
        ) or "none"
        lines.extend(
            [
                f"### `public.{name}`",
                bullet("kind", kind),
                bullet("classification", classify_object(name)),
                bullet("rls_enabled", str(bool(row["rls_enabled"])).lower()),
                bullet("rls_forced", str(bool(row["rls_forced"])).lower()),
                bullet("reloptions", row["reloptions"] or "none"),
                bullet("anon/authenticated grants", grant_summary),
                "",
            ]
        )

    close_first = sorted([row["object_name"] for row in objects if classify_object(row["object_name"]) == "close-first"])
    keep_public = sorted([row["object_name"] for row in objects if classify_object(row["object_name"]) == "keep-public-review-grants"])
    review = sorted([row["object_name"] for row in objects if classify_object(row["object_name"]) == "review"])

    lines.extend(
        [
            "## Recommended Buckets",
            "",
            "### Close First",
            "",
        ]
    )
    lines.extend([f"- `public.{name}`" for name in close_first] or ["- none"])
    lines.extend(
        [
            "",
            "### Keep Public, But Tighten",
            "",
        ]
    )
    lines.extend([f"- `public.{name}`" for name in keep_public] or ["- none"])
    lines.extend(
        [
            "",
            "### Review Manually",
            "",
        ]
    )
    lines.extend([f"- `public.{name}`" for name in review] or ["- none"])
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This snapshot is intentionally grant-focused. It does not change any runtime permissions by itself.",
            "- `SECURITY DEFINER` advisories become materially important when `anon` / `authenticated` also have open grants.",
            "- Use this report to drive additive revoke / schema-hardening migrations, not ad-hoc dashboard clicks.",
            "",
        ]
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
