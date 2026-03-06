import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urlencode

import psycopg
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel, EmailStr
from psycopg.types.json import Jsonb

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
    details: dict | None = None


class SiteEventRequest(BaseModel):
    event_type: str
    source: str = "site"
    details: dict | None = None


def detect_lang(request: Request, explicit: str | None = None) -> Literal["ru", "en"]:
    if explicit in {"ru", "en"}:
        return explicit

    q_lang = (request.query_params.get("lang") or "").strip().lower()
    if q_lang in {"ru", "en"}:
        return q_lang

    country_headers = [
        "cf-ipcountry",
        "x-vercel-ip-country",
        "x-geo-country",
        "x-country-code",
    ]
    for h in country_headers:
        country = (request.headers.get(h) or "").strip().upper()
        if country == "RU":
            return "ru"
        if country:
            return "en"

    accept_lang = (request.headers.get("accept-language") or "").lower()
    if "ru" in accept_lang:
        return "ru"
    return "en"


def load_page(base_name: str, lang: Literal["ru", "en"]) -> str:
    localized = WEB_DIR / f"{base_name}.{lang}.html"
    if localized.exists():
        return localized.read_text(encoding="utf-8")
    fallback = WEB_DIR / f"{base_name}.html"
    return fallback.read_text(encoding="utf-8")


def base_url() -> str:
    return APP_BASE_URL.rstrip("/")


def enrich_details(
    request: Request,
    details: dict | None = None,
    fallback_lang: str | None = None,
    fallback_placement: str | None = None,
) -> dict:
    payload = dict(details or {})
    qp = request.query_params

    for key in ("utm_source", "utm_medium", "utm_campaign"):
        if not payload.get(key):
            v = (qp.get(key) or "").strip()
            if v:
                payload[key] = v

    if not payload.get("placement") and fallback_placement:
        payload["placement"] = fallback_placement
    if not payload.get("placement"):
        placement_q = (qp.get("placement") or "").strip()
        if placement_q:
            payload["placement"] = placement_q

    if not payload.get("lang") and fallback_lang in {"ru", "en"}:
        payload["lang"] = fallback_lang

    return payload


def log_site_event(
    *,
    event_type: str,
    request: Request,
    lang: str,
    email: str | None = None,
    source: str | None = None,
    details: dict | None = None,
) -> None:
    if not PG_CONN:
        return
    try:
        with psycopg.connect(PG_CONN, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into app.site_events (
                      event_type, email, source, lang, path, user_agent, ip, details
                    )
                    values (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        event_type,
                        (email or "").strip().lower() or None,
                        source,
                        lang,
                        request.url.path,
                        request.headers.get("user-agent"),
                        request.client.host if request.client else None,
                        Jsonb(details or {}),
                    ),
                )
            conn.commit()
    except Exception:
        # analytics must never break user-facing flow
        return


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


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots() -> PlainTextResponse:
    return PlainTextResponse(
        "User-agent: *\nAllow: /\nSitemap: " + f"{base_url()}/sitemap.xml\n"
    )


@app.get("/sitemap.xml")
def sitemap() -> Response:
    u = base_url()
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{u}/</loc></url>\n"
        f"  <url><loc>{u}/privacy</loc></url>\n"
        f"  <url><loc>{u}/terms</loc></url>\n"
        "</urlset>\n"
    )
    return Response(content=content, media_type="application/xml")


@app.get("/og-card.svg")
def og_card() -> Response:
    p = WEB_DIR / "og-card.svg"
    if not p.exists():
        return Response(status_code=404)
    return Response(content=p.read_text(encoding="utf-8"), media_type="image/svg+xml")


@app.get("/favicon.svg")
def favicon_svg() -> Response:
    p = WEB_DIR / "favicon.svg"
    if not p.exists():
        return Response(status_code=404)
    return Response(content=p.read_text(encoding="utf-8"), media_type="image/svg+xml")


@app.get("/favicon.ico")
def favicon_ico() -> Response:
    # Serve SVG fallback for modern browsers that still request /favicon.ico.
    return favicon_svg()


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    lang = detect_lang(request)
    return HTMLResponse(load_page("index", lang))


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request) -> HTMLResponse:
    lang = detect_lang(request)
    return HTMLResponse(load_page("privacy", lang))


@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request) -> HTMLResponse:
    lang = detect_lang(request)
    return HTMLResponse(load_page("terms", lang))


@app.post("/api/events")
def site_event(data: SiteEventRequest, request: Request) -> JSONResponse:
    req_lang = detect_lang(request)
    merged_details = enrich_details(request, data.details, fallback_lang=req_lang)
    detail_lang = merged_details.get("lang")
    event_lang = detail_lang if detail_lang in {"ru", "en"} else req_lang
    allowed = {"tg_click", "page_view"}
    event_type = (data.event_type or "").strip().lower()
    if event_type not in allowed:
        raise HTTPException(status_code=400, detail="unsupported event_type")

    log_site_event(
        event_type=event_type,
        request=request,
        lang=event_lang,
        source=(data.source or "site").strip()[:64] or "site",
        details=merged_details,
    )
    return JSONResponse({"ok": True})


@app.post("/api/waitlist")
def waitlist(data: WaitlistRequest, request: Request) -> JSONResponse:
    req_lang = detect_lang(request)
    source = data.source.strip() if data.source else "site"
    details = enrich_details(request, data.details, fallback_lang=req_lang, fallback_placement="waitlist_form")

    token = upsert_waitlist(data.email, source)
    confirm_q = {"token": token}
    for key in ("utm_source", "utm_medium", "utm_campaign", "placement", "lang"):
        value = details.get(key)
        if value:
            confirm_q[key] = value
    confirm_link = f"{base_url()}/confirm?{urlencode(confirm_q)}"
    log_site_event(
        event_type="waitlist_submit",
        request=request,
        lang=req_lang,
        email=data.email,
        source=source,
        details=details,
    )

    if req_lang == "ru":
        html = (
            "<h2>Подтвердите email</h2>"
            "<p>Нажмите, чтобы подтвердить подписку на обновления Polymarket Pulse:</p>"
            f"<p><a href=\"{confirm_link}\">Подтвердить email</a></p>"
        )
        subject = "Подтвердите подписку Polymarket Pulse"
        message = "Письмо для подтверждения отправлено"
    else:
        html = (
            "<h2>Confirm your email</h2>"
            "<p>Click to confirm your subscription to Polymarket Pulse updates:</p>"
            f"<p><a href=\"{confirm_link}\">Confirm email</a></p>"
        )
        subject = "Confirm your Polymarket Pulse subscription"
        message = "Confirmation email sent"

    try:
        send_email(data.email, subject, html)
    except Exception:
        return JSONResponse({"ok": True, "message": message + " (email queue delay possible)"})
    return JSONResponse({"ok": True, "message": message})


@app.get("/confirm", response_class=HTMLResponse)
def confirm(token: str, request: Request) -> HTMLResponse:
    req_lang = detect_lang(request)
    details = enrich_details(request, fallback_lang=req_lang, fallback_placement="email_confirm")
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
        log_site_event(
            event_type="confirm_failed",
            request=request,
            lang=req_lang,
            details={**details, "reason": "invalid_or_expired_token"},
        )
        if req_lang == "ru":
            return HTMLResponse("<h3>Токен недействителен или истёк.</h3>", status_code=400)
        return HTMLResponse("<h3>Invalid or expired confirmation token.</h3>", status_code=400)

    email = row[0]
    log_site_event(
        event_type="confirm_success",
        request=request,
        lang=req_lang,
        email=email,
        details=details,
    )
    unsub = f"{base_url()}/unsubscribe?token={token}"
    if req_lang == "ru":
        try:
            send_email(
                email,
                "Добро пожаловать в Polymarket Pulse",
                "<h2>Добро пожаловать</h2><p>Подписка подтверждена. Ежедневный дайджест включён.</p>"
                f"<p><a href=\"{unsub}\">Отписаться</a></p>",
            )
        except Exception:
            pass
        return HTMLResponse("<h3>Email подтверждён. Ежедневный дайджест включён.</h3>")
    try:
        send_email(
            email,
            "Welcome to Polymarket Pulse",
            "<h2>Welcome</h2><p>You are confirmed for daily digest updates.</p>"
            f"<p><a href=\"{unsub}\">Unsubscribe</a></p>",
        )
    except Exception:
        pass
    return HTMLResponse("<h3>Email confirmed. Daily digest is enabled.</h3>")


@app.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe(token: str, request: Request) -> HTMLResponse:
    req_lang = detect_lang(request)
    details = enrich_details(request, fallback_lang=req_lang, fallback_placement="email_unsubscribe")
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
        log_site_event(
            event_type="unsubscribe_failed",
            request=request,
            lang=req_lang,
            details={**details, "reason": "token_not_found_or_already_unsubscribed"},
        )
        if req_lang == "ru":
            return HTMLResponse("<h3>Токен не найден или уже отписан.</h3>", status_code=400)
        return HTMLResponse("<h3>Token not found or already unsubscribed.</h3>", status_code=400)

    log_site_event(
        event_type="unsubscribe_success",
        request=request,
        lang=req_lang,
        email=row[0],
        details=details,
    )
    if req_lang == "ru":
        return HTMLResponse("<h3>Вы успешно отписались.</h3>")
    return HTMLResponse("<h3>You have been unsubscribed.</h3>")
