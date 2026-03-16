import argparse
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


def resolve_pg_conn() -> str:
    pg = os.environ.get("PG_CONN")
    if pg:
        return pg
    for env_path in ("bot/.env", "trader_bot/.env"):
        path = Path(env_path)
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("PG_CONN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("PG_CONN not found in env, bot/.env, or trader_bot/.env")


def main() -> None:
    parser = argparse.ArgumentParser(description="List trader signer sessions for operator review.")
    parser.add_argument(
        "--statuses",
        default="new,opened,signed",
        help="Comma-separated statuses to include. Default: new,opened,signed",
    )
    parser.add_argument("--limit", type=int, default=20, help="Max rows to show")
    args = parser.parse_args()

    statuses = [s.strip() for s in args.statuses.split(",") if s.strip()]
    if not statuses:
        raise RuntimeError("At least one status must be provided")

    pg_conn = resolve_pg_conn()
    with psycopg.connect(pg_conn, connect_timeout=10, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '10000ms'")
            cur.execute(
                """
                select
                  ss.session_token,
                  ss.status,
                  ss.created_at,
                  ss.expires_at,
                  ss.verified_at,
                  wl.wallet_address,
                  wl.status as wallet_status,
                  wl.signer_kind,
                  a.user_id
                from trade.signer_sessions ss
                join trade.wallet_links wl on wl.id = ss.wallet_link_id
                join trade.accounts a on a.id = ss.account_id
                where ss.status = any(%s::text[])
                order by
                  case ss.status
                    when 'signed' then 1
                    when 'opened' then 2
                    when 'new' then 3
                    else 9
                  end,
                  ss.created_at desc
                limit %s
                """,
                (statuses, args.limit),
            )
            rows = cur.fetchall()

    if not rows:
        print("no signer sessions found")
        return

    for row in rows:
        print("---")
        print(f"session_token={row['session_token']}")
        print(f"status={row['status']}")
        print(f"wallet={row['wallet_address']}")
        print(f"wallet_status={row['wallet_status']}")
        print(f"signer_kind={row['signer_kind']}")
        print(f"user_id={row['user_id']}")
        print(f"created_at={row['created_at']}")
        print(f"expires_at={row['expires_at']}")
        print(f"verified_at={row['verified_at']}")


if __name__ == "__main__":
    main()
