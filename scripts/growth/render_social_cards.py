#!/usr/bin/env python3
import argparse
import html
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

SQL_MOVERS = """
select market_id, question, delta_yes, yes_mid_prev, yes_mid_now, prev_bucket, last_bucket
from public.top_movers_latest
where delta_yes is not null
order by abs(delta_yes) desc nulls last
limit %s;
"""

SQL_BREAKOUT = """
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


def fmt_delta(v: Any) -> str:
    if v is None:
        return "n/a"
    return f"{float(v) * 100:+.1f}pp"


def delta_color(v: Any) -> str:
    if v is None:
        return "#8fa88f"
    return "#00ff88" if float(v) >= 0 else "#ff5d73"


def minutes_window(prev_bucket, last_bucket) -> str:
    if prev_bucket is None or last_bucket is None:
        return "live"
    mins = int((last_bucket - prev_bucket).total_seconds() // 60)
    return f"{max(mins, 1)}m"


def truncate(text: str | None, limit: int) -> str:
    raw = (text or "").strip()
    if len(raw) <= limit:
        return raw
    return raw[: limit - 1].rstrip() + "…"


def load_template(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def apply_tokens(svg: str, tokens: dict[str, str]) -> str:
    out = svg
    for k, v in tokens.items():
        out = out.replace("{{" + k + "}}", html.escape(v))
    return out


def maybe_render_png(svg_path: Path) -> Path | None:
    try:
        import cairosvg  # type: ignore
    except Exception:
        return None
    png_path = svg_path.with_suffix(".png")
    cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=1200, output_height=675)
    return png_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render branded social cards from live DB into local SVG files")
    parser.add_argument("--output-dir", default="assets/social/out", help="Where to write rendered cards")
    parser.add_argument("--report", default="docs/social_visuals_latest.md", help="Markdown report path")
    parser.add_argument("--movers", type=int, default=5, help="How many movers to read")
    args = parser.parse_args()

    pg = os.environ.get("PG_CONN", "")
    if not pg:
        raise SystemExit("PG_CONN is required")

    with psycopg.connect(pg, connect_timeout=10) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(SQL_MOVERS, (args.movers,))
            movers = cur.fetchall()
            cur.execute(SQL_BREAKOUT)
            breakout = cur.fetchone()

    if not movers:
        raise SystemExit("No movers available right now")

    base = Path(__file__).resolve().parents[2]
    tpl_dir = base / "assets" / "social"
    out_dir = base / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    top3_tpl = load_template(tpl_dir / "top3-template.svg")
    breakout_tpl = load_template(tpl_dir / "breakout-template.svg")
    weekly_tpl = load_template(tpl_dir / "weekly-recap-template.svg")

    m = (movers + [movers[-1], movers[-1], movers[-1]])[:3]
    top_tokens = {
        "HEADING": "Top 3 probability shifts",
        "Q1": truncate(m[0].get("question"), 52),
        "MOVE1": f"{fmt_pct(m[0].get('yes_mid_prev'))} → {fmt_pct(m[0].get('yes_mid_now'))}",
        "DELTA1": fmt_delta(m[0].get("delta_yes")),
        "DELTA1_COLOR": delta_color(m[0].get("delta_yes")),
        "Q2": truncate(m[1].get("question"), 52),
        "MOVE2": f"{fmt_pct(m[1].get('yes_mid_prev'))} → {fmt_pct(m[1].get('yes_mid_now'))}",
        "DELTA2": fmt_delta(m[1].get("delta_yes")),
        "DELTA2_COLOR": delta_color(m[1].get("delta_yes")),
        "Q3": truncate(m[2].get("question"), 52),
        "MOVE3": f"{fmt_pct(m[2].get('yes_mid_prev'))} → {fmt_pct(m[2].get('yes_mid_now'))}",
        "DELTA3": fmt_delta(m[2].get("delta_yes")),
        "DELTA3_COLOR": delta_color(m[2].get("delta_yes")),
    }

    br = breakout or {
        "question": m[0].get("question"),
        "market_id": m[0].get("market_id"),
        "delta_mid": m[0].get("delta_yes"),
        "mid_prev": m[0].get("yes_mid_prev"),
        "mid_now": m[0].get("yes_mid_now"),
        "prev_bucket": m[0].get("prev_bucket"),
        "last_bucket": m[0].get("last_bucket"),
    }
    br_tokens = {
        "HEADING": "Single market breakout",
        "QUESTION": truncate(br.get("question"), 72),
        "PREV": fmt_pct(br.get("mid_prev")),
        "NOW": fmt_pct(br.get("mid_now")),
        "DELTA": fmt_delta(br.get("delta_mid")),
        "DELTA_COLOR": delta_color(br.get("delta_mid")),
        "WINDOW": minutes_window(br.get("prev_bucket"), br.get("last_bucket")),
        "MARKET_ID": str(br.get("market_id") or "n/a"),
        "INSIGHT": "Signal over noise: move exceeded threshold.",
    }

    weekly_lines = [truncate((row.get("question") or "") + " " + fmt_delta(row.get("delta_yes")), 54) for row in movers[:5]]
    while len(weekly_lines) < 5:
        weekly_lines.append("No additional high-signal moves in this window")

    wk_tokens = {
        "HEADING": "This week in live markets",
        "L1": weekly_lines[0],
        "L2": weekly_lines[1],
        "L3": weekly_lines[2],
        "L4": weekly_lines[3],
        "L5": weekly_lines[4],
        "CTA": "Track full feed in Telegram: @polymarket_pulse_bot",
    }

    rendered = {
        "top3-latest.svg": apply_tokens(top3_tpl, top_tokens),
        "breakout-latest.svg": apply_tokens(breakout_tpl, br_tokens),
        "weekly-latest.svg": apply_tokens(weekly_tpl, wk_tokens),
    }

    results = []
    for filename, svg in rendered.items():
        path = out_dir / filename
        path.write_text(svg, encoding="utf-8")
        png_path = maybe_render_png(path)
        results.append((path, png_path))

    now = datetime.now(timezone.utc).isoformat()
    report_lines = [
        f"# Social Visuals ({now})",
        "",
        "Brand-styled local renders from `assets/social/*`.",
        "",
    ]
    for svg_path, png_path in results:
        report_lines.append(f"- svg: `{svg_path.as_posix()}`")
        if png_path:
            report_lines.append(f"- png: `{png_path.as_posix()}`")
        report_lines.append("")

    report_path = base / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(str(report_path))


if __name__ == "__main__":
    main()
