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


def main() -> None:
    if not PG_CONN:
        raise RuntimeError("PG_CONN is required")

    since = datetime.now(timezone.utc) - timedelta(days=1)

    with psycopg.connect(PG_CONN, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '12000ms'")
            cur.execute(
                """
                select id, email, user_id
                from app.email_subscribers
                where confirmed_at is not null
                  and unsubscribed_at is null
                order by id
                """
            )
            subscribers = cur.fetchall()

            sent = 0
            for sub_id, email, user_id in subscribers:
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
                    lines.append(f"<li>{alert_type}: {market_id} | Δ={abs_delta} | {bucket}</li>")

                html = "<h2>Your daily digest</h2><ul>" + "".join(lines) + "</ul>"
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
