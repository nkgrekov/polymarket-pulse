import os
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


def render_digest_email(*, items_html: str, unsub_url: str, stats_line: str) -> str:
    return f"""
    <div style="margin:0;padding:24px;background:#0d0f0e;color:#e8ede9;font-family:'JetBrains Mono','SFMono-Regular',Consolas,monospace;">
      <div style="max-width:680px;margin:0 auto;background:#131714;border:1px solid #1e2520;border-radius:16px;padding:28px;">
        <div style="color:#6b7a6e;font-size:12px;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:14px;">Polymarket Pulse // daily digest</div>
        <h1 style="margin:0 0 14px;font-size:28px;line-height:1.05;color:#e8ede9;">Your markets, without the dashboard crawl.</h1>
        <p style="margin:0 0 18px;font-size:14px;line-height:1.65;color:#8fa88f;">This digest is your backup view of what actually moved. For live action, Telegram is still the primary loop.</p>
        <p style="margin:0 0 18px;color:#6b7a6e;font-size:12px;line-height:1.6;">{stats_line}</p>
        <div style="font-size:14px;line-height:1.65;color:#e8ede9;">{items_html}</div>
        <p style="margin:24px 0 0;">
          <a href="{PULSE_BOT_URL}" style="display:inline-block;background:#00ff88;color:#0a0c0b;text-decoration:none;font-weight:700;border-radius:12px;padding:13px 18px;">Open Telegram Bot</a>
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
                    select market_id, alert_type, abs_delta, bucket
                    from bot.alert_events
                    where user_id = %s
                      and created_at >= %s
                    order by abs_delta desc nulls last
                    limit 10
                    """,
                    (user_id, since),
                )
                rows = cur.fetchall()
                if not rows:
                    continue

                lines = []
                for market_id, alert_type, abs_delta, bucket in rows:
                    lines.append(
                        "<li style=\"margin:0 0 10px;\">"
                        f"<strong>{alert_type}</strong> · {market_id}<br />"
                        f"<span style=\"color:#8fa88f;\">Δ={abs_delta} · {bucket}</span>"
                        "</li>"
                    )

                unsub_url = f"{APP_BASE_URL}/unsubscribe?token={confirm_token}" if confirm_token else APP_BASE_URL
                stats_line = f"{len(rows)} alert candidate(s) from the last 24 hours."
                html = render_digest_email(
                    items_html="<ul style=\"padding-left:18px;margin:0;\">" + "".join(lines) + "</ul>",
                    unsub_url=unsub_url,
                    stats_line=stats_line,
                )
                send_email(email, "Polymarket Pulse daily digest", html)

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
