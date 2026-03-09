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

SEO_PAGES: dict[str, dict[str, dict[str, str]]] = {
    "analytics": {
        "en": {
            "title": "Polymarket Analytics - Live Probability Signals | Polymarket Pulse",
            "description": "Polymarket analytics for real probability shifts: top movers, watchlist deltas, and signal-first alerts in Telegram.",
            "h1": "Polymarket analytics without dashboard overload.",
            "intro": "Track meaningful market moves and skip terminal noise. Get live deltas, not endless charts.",
            "k1": "Top movers in the latest live window",
            "k2": "Personal watchlist with threshold filtering",
            "k3": "Telegram-first alerts for faster reaction",
        },
        "ru": {
            "title": "Polymarket аналитика - live сигналы вероятностей | Polymarket Pulse",
            "description": "Аналитика Polymarket по реальным сдвигам вероятностей: top movers, watchlist-дельты и signal-first алерты в Telegram.",
            "h1": "Polymarket аналитика без перегруза дашбордами.",
            "intro": "Отслеживайте значимые движения рынка, а не шум терминала. Только live-дельты по делу.",
            "k1": "Top movers в последнем live-окне",
            "k2": "Персональный watchlist с порогом сигналов",
            "k3": "Telegram-first алерты для быстрой реакции",
        },
    },
    "dashboard": {
        "en": {
            "title": "Polymarket Dashboard Alternative - Signal Feed | Polymarket Pulse",
            "description": "A simple Polymarket dashboard alternative focused on live movers, watchlists, and actionable alerts.",
            "h1": "A dashboard alternative for normal users.",
            "intro": "No complex terminal required. Open Telegram and see what actually moved right now.",
            "k1": "One feed for movers, inbox, and watchlist",
            "k2": "Clear delta + time window for each signal",
            "k3": "Freemium model with upgrade path to Pro",
        },
        "ru": {
            "title": "Альтернатива Polymarket dashboard - signal feed | Polymarket Pulse",
            "description": "Простая альтернатива dashboard для Polymarket: live movers, watchlist и actionable алерты.",
            "h1": "Альтернатива dashboard для обычного пользователя.",
            "intro": "Без сложного терминала. Открываете Telegram и сразу видите, что реально сдвинулось.",
            "k1": "Одна лента для movers, inbox и watchlist",
            "k2": "Понятные delta + временное окно у каждого сигнала",
            "k3": "Freemium-модель и апгрейд до Pro",
        },
    },
    "signals": {
        "en": {
            "title": "Polymarket Signals - Live Alerts in Telegram | Polymarket Pulse",
            "description": "Get Polymarket signals based on real probability shifts. Configure threshold and receive clean Telegram alerts.",
            "h1": "Signals, not noise.",
            "intro": "Set your threshold, follow markets, and receive only meaningful moves in your inbox.",
            "k1": "Per-user threshold in bot settings",
            "k2": "Deduplicated alerts and daily free limits",
            "k3": "Fast onboarding in under 60 seconds",
        },
        "ru": {
            "title": "Polymarket Signals - live алерты в Telegram | Polymarket Pulse",
            "description": "Получайте сигналы Polymarket по реальным сдвигам вероятностей. Настройте порог и получайте чистые алерты в Telegram.",
            "h1": "Сигналы, а не шум.",
            "intro": "Выставляете порог, выбираете рынки и получаете только значимые движения в inbox.",
            "k1": "Персональный threshold в настройках бота",
            "k2": "Дедупликация алертов и дневные free-лимиты",
            "k3": "Онбординг меньше чем за 60 секунд",
        },
    },
    "telegram-bot": {
        "en": {
            "title": "Polymarket Telegram Bot - Live Movers and Watchlist Alerts",
            "description": "Use the Polymarket Pulse Telegram bot for top movers, watchlist tracking, and live probability alerts.",
            "h1": "Polymarket Telegram bot for live signals.",
            "intro": "Start with /movers, add one market to watchlist, and get alerts when probabilities shift.",
            "k1": "Core commands that fit in Telegram menu",
            "k2": "Inline menu for fast actions",
            "k3": "Multi-user profile with plan and limits",
        },
        "ru": {
            "title": "Polymarket Telegram bot - live movers и watchlist алерты",
            "description": "Используйте Telegram-бота Polymarket Pulse для top movers, отслеживания watchlist и live алертов вероятности.",
            "h1": "Polymarket Telegram-бот для live сигналов.",
            "intro": "Начните с /movers, добавьте один рынок в watchlist и получайте алерты при сдвиге вероятности.",
            "k1": "Core-команды, которые помещаются в меню Telegram",
            "k2": "Inline-меню для быстрых действий",
            "k3": "Мультиюзерный профиль с планом и лимитами",
        },
    },
    "top-movers": {
        "en": {
            "title": "Polymarket Top Movers - Live Probability Shifts",
            "description": "See Polymarket top movers by probability change and track market momentum via Telegram.",
            "h1": "Top movers in one tap.",
            "intro": "When the short window is flat, fallback logic surfaces the strongest 1h moves.",
            "k1": "Latest window movers with delta",
            "k2": "1h fallback when market is flat",
            "k3": "Direct add-to-watchlist flow",
        },
        "ru": {
            "title": "Polymarket Top Movers - live сдвиги вероятностей",
            "description": "Смотрите top movers в Polymarket по изменению вероятности и отслеживайте momentum через Telegram.",
            "h1": "Top movers в один тап.",
            "intro": "Если короткое окно плоское, fallback логика показывает самые сильные движения за 1 час.",
            "k1": "Movers по последнему окну с дельтой",
            "k2": "Fallback на 1h при плоском рынке",
            "k3": "Прямой сценарий добавления в watchlist",
        },
    },
    "watchlist-alerts": {
        "en": {
            "title": "Polymarket Watchlist Alerts - Custom Market Tracking",
            "description": "Create your Polymarket watchlist and get custom Telegram alerts when selected markets move.",
            "h1": "Watchlist alerts that stay actionable.",
            "intro": "Add the markets that matter to you and tune sensitivity with per-user threshold.",
            "k1": "Free plan: 3 markets and 20 alerts/day",
            "k2": "Pro plan: unlimited watchlist and alerts",
            "k3": "Clear /plan and /upgrade flow in Telegram",
        },
        "ru": {
            "title": "Polymarket Watchlist Alerts - кастомное отслеживание рынков",
            "description": "Соберите свой watchlist Polymarket и получайте кастомные Telegram-алерты, когда выбранные рынки двигаются.",
            "h1": "Watchlist-алерты, которые помогают действовать.",
            "intro": "Добавьте важные для вас рынки и настройте чувствительность персональным threshold.",
            "k1": "Free: 3 рынка и 20 алертов в день",
            "k2": "Pro: безлимит watchlist и алерты",
            "k3": "Понятный сценарий /plan и /upgrade в Telegram",
        },
    },
}


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


def render_seo_page(slug: str, lang: Literal["ru", "en"]) -> str:
    page = SEO_PAGES[slug][lang]
    page_label = slug.replace("-", " ").upper()
    home_q = "?lang=ru" if lang == "ru" else "?lang=en"
    alt_lang = "ru" if lang == "en" else "en"
    alt_q = "?lang=ru" if alt_lang == "ru" else "?lang=en"
    cta_text = "Open Telegram Bot" if lang == "en" else "Открыть Telegram-бота"
    cta_waitlist_text = "Join Email Waitlist" if lang == "en" else "Вступить в Email Waitlist"
    back_text = "Back to homepage" if lang == "en" else "На главную"
    links_head = "Related pages" if lang == "en" else "Связанные страницы"
    page_view_js_lang = "en" if lang == "en" else "ru"
    base = base_url()
    canonical_url = f"{base}/{slug}"
    lang_url = f"{base}/{slug}{home_q}"
    alt_lang_url = f"{base}/{slug}{alt_q}"
    x_default_url = f"{base}/{slug}?lang=en"
    og_image_url = f"{base}/og-card.svg"

    links = "".join(
        f'<a href="/{name}{home_q}">{SEO_PAGES[name][lang]["h1"]}</a>' for name in SEO_PAGES if name != slug
    )

    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{page["title"]}</title>
  <meta name="description" content="{page["description"]}" />
  <meta name="robots" content="index,follow" />
  <meta property="og:title" content="{page["title"]}" />
  <meta property="og:description" content="{page["description"]}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{canonical_url}" />
  <meta property="og:image" content="{og_image_url}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{page["title"]}" />
  <meta name="twitter:description" content="{page["description"]}" />
  <meta name="twitter:image" content="{og_image_url}" />
  <meta name="twitter:url" content="{canonical_url}" />
  <link rel="canonical" href="{canonical_url}" />
  <link rel="alternate" hreflang="{lang}" href="{lang_url}" />
  <link rel="alternate" hreflang="{alt_lang}" href="{alt_lang_url}" />
  <link rel="alternate" hreflang="x-default" href="{x_default_url}" />
  <link rel="icon" type="image/svg+xml" sizes="any" href="/favicon.svg" />
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
  <link rel="icon" type="image/png" sizes="48x48" href="/favicon-48x48.png" />
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
  <link rel="shortcut icon" href="/favicon.ico" />
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-J901VRQH4G"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-J901VRQH4G');
  </script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@500;600;700;800&display=swap');
    :root {{
      --bg: #0d0f0e;
      --bg-2: #0a0c0b;
      --panel: #131714;
      --line: #1e2520;
      --line-soft: #2a332b;
      --text: #e8ede9;
      --muted: #8fa88f;
      --muted-soft: #6b7a6e;
      --accent: #00ff88;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Syne", "Segoe UI", sans-serif;
      background:
        radial-gradient(1200px 800px at 85% -20%, rgba(0, 255, 136, 0.08) 0%, transparent 60%),
        linear-gradient(180deg, var(--bg-2) 0%, var(--bg) 60%, var(--bg-2) 100%);
      color: var(--text);
      min-height: 100vh;
    }}
    .wrap {{ width: min(1040px, calc(100% - 32px)); margin: 0 auto; padding: 24px 0 48px; }}
    .top {{
      display:flex; justify-content:space-between; align-items:center; gap: 12px;
      font-family:"Space Mono", monospace; font-size:12px; color: var(--muted);
    }}
    .top a {{
      color: var(--muted);
      text-decoration: none;
      border:1px solid var(--line-soft);
      border-radius:999px;
      padding:6px 10px;
    }}
    .top a:hover, .top a:focus-visible {{ border-color: var(--accent); color: var(--text); outline: none; }}
    .card {{
      margin-top: 16px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 24px;
    }}
    h1 {{
      margin: 0;
      line-height: 0.95;
      font-size: clamp(36px, 7vw, 72px);
      letter-spacing: -0.02em;
      text-transform: uppercase;
    }}
    .intro {{
      margin: 12px 0 0;
      color: var(--muted);
      font-size: clamp(15px, 2vw, 20px);
      line-height: 1.45;
      font-family: "Space Mono", monospace;
    }}
    .feature-rows {{
      margin-top: 16px;
      display: grid;
      gap: 10px;
    }}
    .feature-row {{
      border: 1px solid var(--line);
      border-radius: 12px;
      background: #131714;
      padding: 11px 12px;
      font-family: "Space Mono", monospace;
      color: var(--muted);
      font-size: 13px;
    }}
    .cta {{
      margin-top: 18px;
      display:inline-flex; align-items:center; justify-content:center;
      min-height: 48px; padding: 10px 16px; border-radius: 12px; text-decoration: none;
      font-family: "Space Mono", monospace; font-weight: 700;
      color: var(--bg-2); background: linear-gradient(180deg, #00ff88 0%, #00d874 100%);
      border: 1px solid var(--accent);
    }}
    .cta-secondary {{
      margin-top: 10px;
      margin-left: 8px;
      display:inline-flex; align-items:center; justify-content:center;
      min-height: 48px; padding: 10px 16px; border-radius: 12px; text-decoration: none;
      font-family: "Space Mono", monospace; font-weight: 700;
      color: var(--text); background: #131714;
      border: 1px solid var(--line-soft);
    }}
    .cta-secondary:hover, .cta-secondary:focus-visible {{ border-color: var(--accent); outline: none; }}
    .links-title {{
      margin: 18px 0 8px;
      color: var(--muted);
      font-family: "Space Mono", monospace;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.07em;
    }}
    .links {{
      margin-top: 0;
      display:grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
    }}
    .links a {{
      text-decoration: none;
      color: var(--muted);
      border:1px solid var(--line-soft);
      border-radius: 999px;
      padding: 9px 12px;
      background: #131714;
      font-family: "Space Mono", monospace;
      font-size:13px;
      text-align: center;
    }}
    .links a:hover, .links a:focus-visible {{ border-color: var(--accent); color: var(--text); outline: none; }}
    .back {{
      margin-top: 14px;
      display: inline-block;
      color: var(--muted-soft);
      text-decoration: underline;
      font-family: "Space Mono", monospace;
      font-size: 12px;
    }}
    .back:hover, .back:focus-visible {{ color: var(--text); outline: none; }}
    @media (max-width: 860px) {{ .links {{ grid-template-columns: 1fr 1fr; }} }}
    @media (max-width: 640px) {{
      .wrap {{ width: calc(100% - 20px); }}
      .card {{ padding: 16px; }}
      .links {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <span>POLYMARKET PULSE // {page_label}</span>
      <div>
        <a href="/{slug}{home_q}">{lang.upper()}</a>
        <a href="/{slug}{alt_q}">{alt_lang.upper()}</a>
      </div>
    </div>
    <article class="card">
      <h1>{page["h1"]}</h1>
      <p class="intro">{page["intro"]}</p>
      <div class="feature-rows">
        <div class="feature-row">{page["k1"]}</div>
        <div class="feature-row">{page["k2"]}</div>
        <div class="feature-row">{page["k3"]}</div>
      </div>
      <a id="tg-link" class="cta" href="https://t.me/polymarket_pulse_bot?start=seo_{slug}_{lang}" target="_blank" rel="noopener noreferrer">{cta_text} -></a>
      <a id="waitlist-link" class="cta-secondary" href="/{home_q}#waitlist-form">{cta_waitlist_text}</a>
      <p class="links-title">{links_head}</p>
      <div class="links" aria-label="{links_head}">
        {links}
      </div>
      <a class="back" href="/{home_q}">{back_text}</a>
    </article>
  </div>
  <script>
    async function trackEvent(eventType, details = {{}}) {{
      try {{
        await fetch('/api/events', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ event_type: eventType, source: 'site', details }}),
          keepalive: true
        }});
      }} catch (_) {{}}
    }}
    const p = new URLSearchParams(window.location.search);
    const details = {{
      lang: '{page_view_js_lang}',
      placement: 'seo_{slug}',
      utm_source: p.get('utm_source') || '',
      utm_medium: p.get('utm_medium') || '',
      utm_campaign: p.get('utm_campaign') || ''
    }};
    trackEvent('page_view', details);
    document.getElementById('tg-link')?.addEventListener('click', () => {{
      trackEvent('tg_click', details);
    }});
    document.getElementById('waitlist-link')?.addEventListener('click', () => {{
      trackEvent('waitlist_intent', {{ ...details, placement: 'seo_waitlist' }});
    }});
  </script>
</body>
</html>
"""


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
    extra_urls = "".join(
        f"  <url><loc>{u}/{slug}?lang=en</loc></url>\n"
        f"  <url><loc>{u}/{slug}?lang=ru</loc></url>\n"
        for slug in SEO_PAGES
    )
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{u}/?lang=en</loc></url>\n"
        f"  <url><loc>{u}/?lang=ru</loc></url>\n"
        f"  <url><loc>{u}/privacy?lang=en</loc></url>\n"
        f"  <url><loc>{u}/privacy?lang=ru</loc></url>\n"
        f"  <url><loc>{u}/terms?lang=en</loc></url>\n"
        f"  <url><loc>{u}/terms?lang=ru</loc></url>\n"
        f"{extra_urls}"
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
    p = WEB_DIR / "favicon.ico"
    if p.exists():
        return Response(content=p.read_bytes(), media_type="image/x-icon")
    # Fallback for environments where only SVG is present.
    return favicon_svg()


@app.get("/favicon-32x32.png")
def favicon_32() -> Response:
    p = WEB_DIR / "favicon-32x32.png"
    if not p.exists():
        return Response(status_code=404)
    return Response(content=p.read_bytes(), media_type="image/png")


@app.get("/favicon-48x48.png")
def favicon_48() -> Response:
    p = WEB_DIR / "favicon-48x48.png"
    if not p.exists():
        return Response(status_code=404)
    return Response(content=p.read_bytes(), media_type="image/png")


@app.get("/apple-touch-icon.png")
def apple_touch_icon() -> Response:
    p = WEB_DIR / "apple-touch-icon.png"
    if not p.exists():
        return Response(status_code=404)
    return Response(content=p.read_bytes(), media_type="image/png")


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


@app.get("/{slug}", response_class=HTMLResponse)
def seo_page(slug: str, request: Request) -> HTMLResponse:
    if slug not in SEO_PAGES:
        raise HTTPException(status_code=404, detail="Not found")
    lang = detect_lang(request)
    return HTMLResponse(render_seo_page(slug, lang))


@app.post("/api/events")
def site_event(data: SiteEventRequest, request: Request) -> JSONResponse:
    req_lang = detect_lang(request)
    merged_details = enrich_details(request, data.details, fallback_lang=req_lang)
    detail_lang = merged_details.get("lang")
    event_lang = detail_lang if detail_lang in {"ru", "en"} else req_lang
    allowed = {"tg_click", "page_view", "waitlist_intent"}
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
