import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

import psycopg
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, EmailStr

load_dotenv()

PG_CONN = os.environ.get("PG_CONN", "")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8000")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "Polymarket Pulse <onboarding@resend.dev>")

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"

app = FastAPI(title="Polymarket Pulse Site API")


class WaitlistRequest(BaseModel):
    email: EmailStr
    source: str = "site"


def send_email(to_email: str, subject: str, html: str) -> None:
    if not RESEND_API_KEY:
        return

    payload = {
        "from": RESEND_FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html,
    }
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=15,
    )
    if resp.status_code >= 300:
        raise HTTPException(status_code=502, detail=f"Resend error: {resp.text[:200]}")


def upsert_waitlist(email: str, source: str) -> str:
    if not PG_CONN:
        raise HTTPException(status_code=500, detail="PG_CONN is not configured")

    token = secrets.token_urlsafe(24)
    with psycopg.connect(PG_CONN, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '8000ms'")
            cur.execute(
                """
                insert into app.email_subscribers (email, source, confirm_token)
                values (%s, %s, %s)
                on conflict (email) do update
                set source = excluded.source,
                    confirm_token = excluded.confirm_token,
                    updated_at = now()
                returning confirm_token
                """,
                (email.lower().strip(), source, token),
            )
            saved = cur.fetchone()[0]
        conn.commit()
    return saved


@app.get("/healthz")
def healthz() -> JSONResponse:
    return JSONResponse({"ok": True, "ts": datetime.now(timezone.utc).isoformat()})


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse((WEB_DIR / "index.html").read_text(encoding="utf-8"))


@app.get("/privacy", response_class=HTMLResponse)
def privacy() -> HTMLResponse:
    return HTMLResponse((WEB_DIR / "privacy.html").read_text(encoding="utf-8"))


@app.get("/terms", response_class=HTMLResponse)
def terms() -> HTMLResponse:
    return HTMLResponse((WEB_DIR / "terms.html").read_text(encoding="utf-8"))


@app.post("/api/waitlist")
def waitlist(data: WaitlistRequest) -> JSONResponse:
    token = upsert_waitlist(data.email, data.source)
    confirm_link = f"{APP_BASE_URL.rstrip('/')}/confirm?token={token}"

    html = (
        "<h2>Confirm your email</h2>"
        "<p>Click to confirm your subscription to Polymarket Pulse updates:</p>"
        f"<p><a href=\"{confirm_link}\">Confirm email</a></p>"
    )
    send_email(data.email, "Confirm your Polymarket Pulse subscription", html)
    return JSONResponse({"ok": True, "message": "Confirmation email sent"})


@app.get("/confirm", response_class=HTMLResponse)
def confirm(token: str) -> HTMLResponse:
    if not PG_CONN:
        raise HTTPException(status_code=500, detail="PG_CONN is not configured")

    with psycopg.connect(PG_CONN, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '8000ms'")
            cur.execute(
                """
                update app.email_subscribers
                set confirmed_at = coalesce(confirmed_at, now()),
                    updated_at = now()
                where confirm_token = %s
                  and unsubscribed_at is null
                returning email
                """,
                (token,),
            )
            row = cur.fetchone()
        conn.commit()

    if not row:
        return HTMLResponse("<h3>Invalid or expired confirmation token.</h3>", status_code=400)

    email = row[0]
    unsub = f"{APP_BASE_URL.rstrip('/')}/unsubscribe?token={token}"
    send_email(
        email,
        "Welcome to Polymarket Pulse",
        "<h2>Welcome</h2><p>You are confirmed for daily digest updates.</p>"
        f"<p><a href=\"{unsub}\">Unsubscribe</a></p>",
    )
    return HTMLResponse("<h3>Email confirmed. Daily digest is enabled.</h3>")


@app.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe(token: str) -> HTMLResponse:
    if not PG_CONN:
        raise HTTPException(status_code=500, detail="PG_CONN is not configured")

    with psycopg.connect(PG_CONN, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '8000ms'")
            cur.execute(
                """
                update app.email_subscribers
                set unsubscribed_at = now(),
                    updated_at = now()
                where confirm_token = %s
                  and unsubscribed_at is null
                returning email
                """,
                (token,),
            )
            row = cur.fetchone()
        conn.commit()

    if not row:
        return HTMLResponse("<h3>Token not found or already unsubscribed.</h3>", status_code=400)

    return HTMLResponse("<h3>You have been unsubscribed.</h3>")
