#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import request

import psycopg
from psycopg.rows import dict_row

SQL_MOVERS = """
select market_id, question, delta_yes, yes_mid_prev, yes_mid_now, prev_bucket, last_bucket
from public.top_movers_latest
where delta_yes is not null
order by abs(delta_yes) desc nulls last
limit %s;
"""

SQL_ALERT = """
select question, market_id, delta_mid, mid_prev, mid_now, prev_bucket, last_bucket, abs_delta
from bot.alerts_inbox_latest
where mid_prev is not null and mid_now is not null
order by abs_delta desc nulls last
limit 1;
"""


def fmt_pct(v: Any) -> str:
    if v is None:
        return "n/a"
    return f"{float(v) * 100:.1f}%"


def fmt_delta_pp(v: Any) -> str:
    if v is None:
        return "n/a"
    return f"{float(v) * 100:+.1f}pp"


def truncate(text: str, limit: int = 72) -> str:
    raw = (text or "").strip()
    if len(raw) <= limit:
        return raw
    return raw[: limit - 1].rstrip() + "…"


def mcp_call(mcp_url: str, api_key: str, method: str, params: dict[str, Any], req_id: int) -> dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": method,
        "params": params,
    }
    req = request.Request(
        mcp_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    if "error" in body:
        raise RuntimeError(f"MCP error: {body['error']}")
    return body


def create_image_via_mcp(
    mcp_url: str, api_key: str, template_uuid: str, layers: dict[str, Any], req_id: int
) -> dict[str, Any]:
    body = mcp_call(
        mcp_url,
        api_key,
        "tools/call",
        {"name": "create_image", "arguments": {"template_uuid": template_uuid, "layers": layers}},
        req_id=req_id,
    )
    content = body.get("result", {}).get("content", [])
    if not content:
        raise RuntimeError(f"Empty create_image response for template {template_uuid}")
    raw = content[0].get("text", "")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError(f"Unexpected create_image payload for template {template_uuid}: {raw[:240]}")
    return parsed


def build_assets(
    movers: list[dict[str, Any]],
    alert: dict[str, Any] | None,
) -> list[tuple[str, dict[str, Any]]]:
    top = movers[0] if movers else {}
    top_question = truncate(top.get("question") or "Top live mover")
    top_delta = fmt_delta_pp(top.get("delta_yes"))

    if alert:
        breakout_question = truncate(alert.get("question") or "Breakout market")
        breakout_delta = fmt_delta_pp(alert.get("delta_mid"))
    else:
        breakout_question = top_question
        breakout_delta = top_delta

    lines = []
    for row in movers[:3]:
        q = truncate(row.get("question") or "Unknown market", 56)
        lines.append(f"{q} {fmt_delta_pp(row.get('delta_yes'))}")
    weekly_text = " | ".join(lines) if lines else "No major movers in current window"

    return [
        (
            "top3",
            {
                "title": {"text": top_question},
                "number": {"text": top_delta},
            },
        ),
        (
            "breakout",
            {
                "speaker": {"text": "Polymarket Pulse"},
                "talk": {"text": f"{breakout_question} | {breakout_delta}"},
            },
        ),
        (
            "weekly",
            {
                "position": {"text": truncate(weekly_text, 92)},
                "company": {"text": "Polymarket Pulse"},
                "url": {"text": "polymarketpulse.app"},
            },
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate social visuals via Placid MCP templates")
    parser.add_argument("--output", default="docs/social_visuals_latest.md", help="Output markdown path")
    parser.add_argument("--movers", type=int, default=6, help="How many movers to read from DB")
    parser.add_argument("--template-top3", default="qpfepwdjvsuxv", help="Placid template UUID for top3 card")
    parser.add_argument("--template-breakout", default="1h9uyopu3rarv", help="Placid template UUID for breakout card")
    parser.add_argument("--template-weekly", default="m6nbvjbbyarrj", help="Placid template UUID for weekly card")
    parser.add_argument(
        "--placid-url",
        default=os.environ.get("PLACID_MCP_URL", ""),
        help="Placid MCP endpoint URL",
    )
    parser.add_argument(
        "--placid-key",
        default=os.environ.get("PLACID_API_KEY", ""),
        help="Placid MCP bearer key",
    )
    args = parser.parse_args()

    pg = os.environ.get("PG_CONN", "")
    if not pg:
        raise SystemExit("PG_CONN is required")
    if not args.placid_url:
        raise SystemExit("PLACID_MCP_URL or --placid-url is required")
    if not args.placid_key:
        raise SystemExit("PLACID_API_KEY or --placid-key is required")

    with psycopg.connect(pg, connect_timeout=10) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(SQL_MOVERS, (args.movers,))
            movers = cur.fetchall()
            cur.execute(SQL_ALERT)
            alert = cur.fetchone()

    assets = build_assets(movers, alert)
    template_map = {
        "top3": args.template_top3,
        "breakout": args.template_breakout,
        "weekly": args.template_weekly,
    }
    results: list[dict[str, Any]] = []
    req_id = 1
    for name, layers in assets:
        result = create_image_via_mcp(
            args.placid_url,
            args.placid_key,
            template_map[name],
            layers,
            req_id=req_id,
        )
        req_id += 1
        results.append({"asset": name, "template_uuid": template_map[name], "layers": layers, "result": result})

    now = datetime.now(timezone.utc).isoformat()
    out = [
        f"# Social Visuals ({now})",
        "",
        "Generated from live DB + Placid templates.",
        "",
    ]
    for item in results:
        res = item["result"]
        out += [
            f"## {item['asset']}",
            f"- template: `{item['template_uuid']}`",
            f"- image_id: `{res.get('id', 'n/a')}`",
            f"- status: `{res.get('status', 'n/a')}`",
            f"- url: {res.get('creative_url', 'n/a')}",
            f"- layers: `{json.dumps(item['layers'], ensure_ascii=False)}`",
            "",
        ]

    p = Path(args.output)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out), encoding="utf-8")
    print(str(p))


if __name__ == "__main__":
    main()
