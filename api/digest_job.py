import os
import html
from datetime import datetime, timedelta, timezone

import psycopg
import requests
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

load_dotenv()

PG_CONN = os.environ.get("PG_CONN", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "Polymarket Pulse <onboarding@resend.dev>")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "https://polymarketpulse.app").rstrip("/")
PULSE_BOT_URL = "https://t.me/polymarket_pulse_bot?start=email_digest"


def send_email(to_email: str, subject: str, html: str) -> None:
    if not RESEND_API_KEY:
        return
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": RESEND_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html,
        },
        timeout=15,
    )
    resp.raise_for_status()


def render_digest_email(
    *,
    items_html: str,
    unsub_url: str,
    stats_line: str,
    kicker_line: str,
    cta_label: str,
    coverage_line: str,
    next_step_line: str,
) -> str:
    return f"""
    <div style="margin:0;padding:24px;background:#0d0f0e;color:#e8ede9;font-family:'JetBrains Mono','SFMono-Regular',Consolas,monospace;">
      <div style="max-width:680px;margin:0 auto;background:#131714;border:1px solid #1e2520;border-radius:16px;padding:28px;">
        <div style="color:#6b7a6e;font-size:12px;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:14px;">Polymarket Pulse // daily digest</div>
        <h1 style="margin:0 0 14px;font-size:28px;line-height:1.05;color:#e8ede9;">Your markets, without the dashboard crawl.</h1>
        <p style="margin:0 0 18px;font-size:14px;line-height:1.65;color:#8fa88f;">This digest is your backup view of what actually moved. For live action, Telegram is still the primary loop.</p>
        <p style="margin:0 0 10px;color:#6b7a6e;font-size:12px;line-height:1.6;">{stats_line}</p>
        <p style="margin:0 0 18px;color:#8fa88f;font-size:13px;line-height:1.6;">{kicker_line}</p>
        <div style="margin:0 0 18px;padding:14px 16px;background:#101411;border:1px solid #1e2520;border-radius:12px;">
          <div style="color:#6b7a6e;font-size:11px;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;">Watchlist coverage</div>
          <p style="margin:0 0 8px;color:#e8ede9;font-size:13px;line-height:1.6;">{coverage_line}</p>
          <p style="margin:0;color:#8fa88f;font-size:12px;line-height:1.6;">{next_step_line}</p>
        </div>
        <div style="font-size:14px;line-height:1.65;color:#e8ede9;">{items_html}</div>
        <p style="margin:24px 0 0;">
          <a href="{PULSE_BOT_URL}" style="display:inline-block;background:#00ff88;color:#0a0c0b;text-decoration:none;font-weight:700;border-radius:12px;padding:13px 18px;">{cta_label}</a>
        </p>
        <p style="margin:18px 0 0;color:#6b7a6e;font-size:12px;line-height:1.6;">Telegram is for the live signal loop. Email stays as backup for digest and updates.</p>
        <p style="margin:18px 0 0;color:#8fa88f;font-size:12px;line-height:1.6;"><a href="{unsub_url}" style="color:#8fa88f;">Unsubscribe</a></p>
      </div>
    </div>
    """


def main() -> None:
    if not PG_CONN:
        raise RuntimeError("PG_CONN is required")

    since = datetime.now(timezone.utc) - timedelta(days=1)

    with psycopg.connect(PG_CONN, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '12000ms'")
            cur.execute(
                """
                select id, email, user_id, confirm_token
                from app.email_subscribers
                where confirmed_at is not null
                  and unsubscribed_at is null
                order by id
                """
            )
            subscribers = cur.fetchall()

            sent = 0
            for sub_id, email, user_id, confirm_token in subscribers:
                if user_id is None:
                    continue

                cur.execute(
                    """
                select
                  ae.market_id,
                  ae.alert_type,
                  ae.abs_delta,
                  ae.bucket,
                  coalesce(m.question, ae.market_id) as market_label
                    from bot.alert_events ae
                    left join public.markets m on m.market_id = ae.market_id
                    where ae.user_id = %s
                      and ae.created_at >= %s
                    order by ae.abs_delta desc nulls last
                    limit 10
                    """,
                    (user_id, since),
                )
                rows = cur.fetchall()
                if not rows:
                    continue

                cur.execute(
                    """
                    with total_wl as (
                      select count(*)::int as total_count
                      from bot.watchlist
                      where user_id = %s
                    ), ready_wl as (
                      select count(*)::int as ready_count
                      from bot.watchlist_snapshot_latest
                      where user_id = %s
                    ), closed_wl as (
                      select count(*)::int as closed_count
                      from bot.watchlist w
                      join public.markets m on m.market_id = w.market_id
                      where w.user_id = %s
                        and coalesce(m.status, 'unknown') = 'closed'
                    ), settings as (
                      select threshold
                      from bot.user_settings
                      where user_id = %s
                    )
                    select
                      coalesce((select total_count from total_wl), 0),
                      coalesce((select ready_count from ready_wl), 0),
                      coalesce((select closed_count from closed_wl), 0),
                      coalesce((select threshold from settings), 0.03)
                    """,
                    (user_id, user_id, user_id, user_id),
                )
                total_watchlist, ready_watchlist, closed_watchlist, threshold = cur.fetchone()

                lines = []
                unique_markets = set()
                max_delta = None
                strongest_label = None
                for market_id, alert_type, abs_delta, bucket, market_label in rows:
                    unique_markets.add(str(market_id))
                    try:
                        abs_delta_val = float(abs_delta)
                    except Exception:
                        abs_delta_val = None
                    if abs_delta_val is not None:
                        if max_delta is None or abs_delta_val > max_delta:
                            max_delta = abs_delta_val
                            strongest_label = str(market_label)
                    alert_label = str(alert_type or "delta").replace("_", " ")
                    lines.append(
                        "<li style=\"margin:0 0 10px;\">"
                        f"<strong>{html.escape(str(market_label))}</strong><br />"
                        f"<span style=\"color:#8fa88f;\">{html.escape(alert_label)} · Δ={html.escape(str(abs_delta))} · {html.escape(str(bucket))}</span>"
                        "</li>"
                    )

                unsub_url = f"{APP_BASE_URL}/unsubscribe?token={confirm_token}" if confirm_token else APP_BASE_URL
                stats_line = f"{len(rows)} alert candidate(s) across {len(unique_markets)} market(s) from the last 24 hours."
                quiet_markets = max(int(total_watchlist) - len(unique_markets), 0)
                coverage_line = (
                    f"{ready_watchlist}/{total_watchlist} tracked market(s) have live last+prev coverage right now. "
                    f"{len(unique_markets)} market(s) actually crossed your threshold in this digest window."
                    if total_watchlist
                    else f"{len(unique_markets)} market(s) crossed your threshold in this digest window."
                )
                if int(closed_watchlist) > 0:
                    next_step_line = (
                        f"{closed_watchlist} tracked market(s) are already closed. Best next step: open Pulse in Telegram and replace those first."
                    )
                elif int(ready_watchlist) == 0 and int(total_watchlist) > 0:
                    next_step_line = (
                        "Your list has no live ready markets right now. Best next step: open Pulse in Telegram and swap in one stronger live market."
                    )
                elif quiet_markets > 0:
                    next_step_line = (
                        f"{quiet_markets} tracked market(s) stayed quiet in this window. That is normal. Use Telegram if you want to review the list or lower the threshold from {float(threshold):.3f}."
                    )
                else:
                    next_step_line = (
                        "This is a healthy backup pass. Use Telegram if you want to inspect the live watchlist feed instead of the recap."
                    )
                kicker_line = (
                    f"Strongest move in this backup pass: {html.escape(str(strongest_label))} at Δ={max_delta:.3f}. Open Telegram if you want the live loop, not the recap."
                    if max_delta is not None and strongest_label
                    else "Open Telegram if you want the live loop, not the recap."
                )
                html = render_digest_email(
                    items_html="<ul style=\"padding-left:18px;margin:0;\">" + "".join(lines) + "</ul>",
                    unsub_url=unsub_url,
                    stats_line=stats_line,
                    kicker_line=kicker_line,
                    cta_label="Resume in Telegram",
                    coverage_line=coverage_line,
                    next_step_line=next_step_line,
                )
                subject = (
                    f"Polymarket Pulse digest: {strongest_label}"
                    if strongest_label
                    else f"Polymarket Pulse daily digest: {len(rows)} alert candidate(s)"
                )
                send_email(email, subject, html)

                cur.execute(
                    """
                    insert into bot.sent_alerts_log (
                      channel, user_id, recipient, market_id, alert_type, bucket, payload
                    )
                    values (%s, %s, %s, %s, %s, %s, %s)
                    on conflict (channel, recipient, market_id, alert_type, bucket) do nothing
                    """,
                    (
                        "email",
                        user_id,
                        email,
                        None,
                        "daily_digest",
                        datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0),
                        Jsonb({"subscriber_id": sub_id, "alerts_count": len(rows)}),
                    ),
                )
                sent += 1

        conn.commit()

    print(f"digest_sent={sent}")


if __name__ == "__main__":
    main()
