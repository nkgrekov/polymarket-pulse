import os
import json
import logging
import secrets
import hashlib
import hmac
import html
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import quote, urlencode, urlparse

import psycopg
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response
from pydantic import BaseModel, EmailStr
from psycopg.types.json import Jsonb

load_dotenv()

logger = logging.getLogger("polymarket_pulse_site")

PG_CONN = os.environ.get("PG_CONN", "")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8000")
PULSE_BOT_URL = "https://t.me/polymarket_pulse_bot?start=email_backup"
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "Polymarket Pulse <onboarding@resend.dev>")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_PRICE_ID_MONTHLY = os.environ.get("STRIPE_PRICE_ID_MONTHLY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_SUCCESS_URL = os.environ.get("STRIPE_SUCCESS_URL", "")
STRIPE_CANCEL_URL = os.environ.get("STRIPE_CANCEL_URL", "")
PRO_SUBSCRIPTION_DAYS = int(os.environ.get("PRO_SUBSCRIPTION_DAYS", "30"))
WEB_SESSION_DAYS = int(os.environ.get("WEB_SESSION_DAYS", "30"))
WEB_AUTH_REQUEST_MINUTES = int(os.environ.get("WEB_AUTH_REQUEST_MINUTES", "30"))
WEB_SESSION_COOKIE = os.environ.get("WEB_SESSION_COOKIE", "pulse_session")

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"

app = FastAPI(title="Polymarket Pulse Site API")

SEO_PAGES: dict[str, dict[str, dict[str, str]]] = {
    "analytics": {
        "en": {
            "title": "Polymarket Analytics - Live Probability Shifts That Matter | Polymarket Pulse",
            "description": "Polymarket analytics for real probability shifts: top movers, watchlist deltas, and signal-first Telegram alerts without dashboard overload.",
            "h1": "Polymarket analytics for people who act, not browse.",
            "intro": "See live repricing fast, filter out terminal noise, and move from discovery to action inside Telegram instead of babysitting a dashboard tab.",
            "k1": "Top movers from the current live repricing window",
            "k2": "Watchlist deltas filtered by your own threshold",
            "k3": "Telegram-first handoff from signal to action",
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
            "title": "Polymarket Dashboard Alternative - Fast Signals, Not Dashboard Overload",
            "description": "A Polymarket dashboard alternative built for action: live movers, watchlists, and clear Telegram alerts without terminal overload.",
            "h1": "A Polymarket dashboard alternative built for action.",
            "intro": "Skip the widget sprawl. Pulse gives you one fast surface for movers, watchlist deltas, and inbox signals so you can react instead of browsing.",
            "k1": "One feed for movers, inbox, and watchlist deltas",
            "k2": "Clear delta plus time-window context on every signal",
            "k3": "Freemium path into Pro without dashboard clutter",
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
            "title": "Polymarket Signals - Low-Noise Live Alerts in Telegram | Polymarket Pulse",
            "description": "Get Polymarket signals based on real probability shifts. Set your threshold, cut the noise, and receive clean live alerts in Telegram.",
            "h1": "Live signals with an actual noise filter.",
            "intro": "Most signal feeds spam every twitch. Pulse filters by threshold, deduplicates repeated moves, and stays quiet when the market is flat.",
            "k1": "Per-user threshold in Telegram settings",
            "k2": "Deduplicated alerts instead of repeat spam",
            "k3": "Fast activation path from /start to first signal",
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
            "title": "Best Polymarket Telegram Bot for Live Movers & Alerts | Polymarket Pulse",
            "description": "Looking for the best Polymarket Telegram bot? Polymarket Pulse tracks live movers, watchlist markets, and low-noise alerts in Telegram so you can act before dashboard lag.",
            "h1": "The Polymarket Telegram bot for live movers, watchlists, and low-noise alerts.",
            "intro": "Search intent should become signal fast: open Telegram, add one live market, and let Pulse surface the move when it matters. No dashboard camping and no wallet required for the signal layer.",
            "k1": "/movers shows the fastest live probability shifts",
            "k2": "/watchlist and /threshold turn noise into a personal signal feed",
            "k3": "/inbox stays quiet until a tracked move clears your threshold",
        },
        "ru": {
            "title": "Polymarket Telegram bot - live movers и watchlist алерты",
            "description": "Используйте Telegram-бота Polymarket Pulse для top movers, отслеживания watchlist и live алертов вероятности.",
            "h1": "Telegram-бот для action-first сигналов Polymarket.",
            "intro": "Большинство решений заточено под дашборды. Pulse заточен под действие: /start -> один рынок в watchlist -> первый live-сигнал меньше чем за 60 секунд.",
            "k1": "Action вместо перегруза dashboard-ами",
            "k2": "Активация за 60 секунд",
            "k3": "Качество сигнала: threshold + дедуп",
        },
    },
    "top-movers": {
        "en": {
            "title": "Polymarket Top Movers - Fastest Live Probability Shifts",
            "description": "See Polymarket top movers by probability change, catch the fastest repricing, and push the move straight into Telegram.",
            "h1": "Catch the fastest movers before the tab crowd does.",
            "intro": "When a live window wakes up, Pulse surfaces the move fast. When it stays flat, fallback logic expands the view instead of faking activity.",
            "k1": "Latest repricing window ranked by meaningful delta",
            "k2": "Adaptive fallback when the short window is quiet",
            "k3": "One-tap move from mover to watchlist tracking",
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
    "watchlist": {
        "en": {
            "title": "Polymarket Watchlist - Save Markets First, Alerts Second",
            "description": "Build a Polymarket watchlist for the markets you care about, then enable Telegram alerts separately when a saved market is worth waking up for.",
            "h1": "Build a watchlist first. Turn alerts on second.",
            "intro": "A watchlist is your saved market set. Alerts are a separate choice. Pulse keeps those layers clean so you can track markets without turning every saved line into a ping.",
            "k1": "Saved markets stay separate from alert delivery",
            "k2": "Telegram holds identity, threshold, and alert settings",
            "k3": "Choose one market, then decide whether it deserves a bell",
        },
        "ru": {
            "title": "Polymarket Watchlist - сначала рынки, потом алерты",
            "description": "Соберите watchlist Polymarket для важных рынков и включайте Telegram-алерты отдельно, только когда рынок действительно стоит шума.",
            "h1": "Сначала watchlist. Потом алерты.",
            "intro": "Watchlist - это набор сохранённых рынков. Alerts - отдельное решение. Pulse специально разделяет эти слои, чтобы вы могли следить за рынками без лишних пингов.",
            "k1": "Сохранённые рынки отделены от доставки алертов",
            "k2": "Telegram хранит identity, threshold и alert-настройки",
            "k3": "Сначала выберите рынок, потом решите, нужен ли ему bell",
        },
    },
    "watchlist-alerts": {
        "en": {
            "title": "Polymarket Watchlist Alerts - Low-Noise Market Tracking in Telegram",
            "description": "Build a Polymarket watchlist, tune your threshold, and get low-noise Telegram alerts when selected markets actually move.",
            "h1": "Watchlist alerts for markets you actually care about.",
            "intro": "Pin the markets that matter, set your own threshold, and let Telegram surface only the repricing worth reacting to.",
            "k1": "Free plan: 3 markets and 20 alerts per day",
            "k2": "Pro plan: 20 markets, unlimited alerts, email digest",
            "k3": "Clear /plan and /upgrade path inside the bot",
        },
        "ru": {
            "title": "Polymarket Watchlist Alerts - кастомное отслеживание рынков",
            "description": "Соберите свой watchlist Polymarket и получайте кастомные Telegram-алерты, когда выбранные рынки двигаются.",
            "h1": "Watchlist-алерты, которые помогают действовать.",
            "intro": "Добавьте важные для вас рынки и настройте чувствительность персональным threshold.",
            "k1": "Free: 3 рынка и 20 алертов в день",
            "k2": "Pro: 20 рынков в watchlist, безлимит алертов и email-дайджест",
            "k3": "Понятный сценарий /plan и /upgrade в Telegram",
        },
    },
}

SEO_PAGE_FAQ: dict[str, dict[str, list[dict[str, str]]]] = {
    "analytics": {
        "en": [
            {
                "q": "What makes this different from a normal Polymarket dashboard?",
                "a": "Polymarket Pulse prioritizes live repricing and actionability. Instead of asking you to scan charts manually, it surfaces movers, watchlist deltas, and alert-ready changes directly in Telegram.",
            },
            {
                "q": "Do I need to connect a wallet to use the analytics layer?",
                "a": "No. The analytics and signal layer works without wallet connection. Wallet and execution flows live in the separate Trader product.",
            },
        ],
        "ru": [
            {
                "q": "Чем это отличается от обычного Polymarket dashboard?",
                "a": "Polymarket Pulse делает упор на live-переоценку и actionability. Вместо того чтобы заставлять вас вручную сканировать графики, он приносит movers, watchlist-дельты и алерты прямо в Telegram.",
            },
            {
                "q": "Нужно ли подключать кошелёк для аналитического слоя?",
                "a": "Нет. Analytics и signal-слой работают без кошелька. Wallet и execution живут в отдельном Trader-продукте.",
            },
        ],
    },
    "dashboard": {
        "en": [
            {
                "q": "Why use this instead of a dashboard tab that shows more widgets?",
                "a": "Because most users do not need more widgets. They need one clear answer: what moved, by how much, and whether it matters right now.",
            },
            {
                "q": "Can I still track specific markets?",
                "a": "Yes. The watchlist flow lets you pin markets that matter and only surface them when their move clears your threshold.",
            },
        ],
        "ru": [
            {
                "q": "Зачем это вместо dashboard-а с большим количеством виджетов?",
                "a": "Потому что большинству пользователей не нужны новые виджеты. Им нужен один ясный ответ: что сдвинулось, насколько и важно ли это прямо сейчас.",
            },
            {
                "q": "Можно ли всё равно отслеживать конкретные рынки?",
                "a": "Да. Watchlist позволяет закрепить важные рынки и показывать их только когда движение проходит ваш порог.",
            },
        ],
    },
    "signals": {
        "en": [
            {
                "q": "How do Polymarket signals stay low-noise?",
                "a": "Signals are filtered by user threshold, deduplicated across repeated windows, and intentionally return quiet states when the market is flat.",
            },
            {
                "q": "What happens if the short window shows no meaningful move?",
                "a": "Pulse falls back to a wider window instead of forcing fake activity. If nothing meaningful moved, it stays quiet on purpose.",
            },
        ],
        "ru": [
            {
                "q": "Как сигналы Polymarket остаются низкошумными?",
                "a": "Сигналы фильтруются персональным threshold, дедуплицируются между повторяющимися окнами и специально показывают тихое состояние, если рынок плоский.",
            },
            {
                "q": "Что происходит, если в коротком окне нет значимого движения?",
                "a": "Pulse делает fallback на более широкое окно, а не выдумывает активность. Если ничего важного не сдвинулось, бот специально молчит.",
            },
        ],
    },
    "telegram-bot": {
        "en": [
            {
                "q": "How fast can a new user get to first value?",
                "a": "The intended path is simple: open the bot, add one live market, and get your first useful signal in under 60 seconds.",
            },
            {
                "q": "Is Polymarket Pulse a Telegram bot for Polymarket?",
                "a": "Yes. Polymarket Pulse is a Telegram-first signal product for Polymarket. It focuses on top movers, watchlist tracking, and low-noise alerts rather than dashboard overload.",
            },
            {
                "q": "What is the best Polymarket Telegram bot for live alerts?",
                "a": "If you want live movers, watchlists, thresholded alerts, and a Telegram-first workflow without connecting a wallet, Polymarket Pulse is built for that use case.",
            },
            {
                "q": "What can this Polymarket Telegram bot actually do?",
                "a": "It lets you watch top movers, add markets to a personal watchlist, tune your alert threshold, and use Inbox to see only the moves that clear your level.",
            },
            {
                "q": "Why do /movers or /inbox sometimes show zero?",
                "a": "That is intentional. If current repricing is flat, Pulse falls back to a wider window and stays quiet if the market still is not moving.",
            },
        ],
        "ru": [
            {
                "q": "Как быстро новый пользователь получает первую ценность?",
                "a": "Сценарий простой: открыть бота, добавить один live-рынок и получить первый полезный сигнал меньше чем за 60 секунд.",
            },
            {
                "q": "Почему /movers или /inbox иногда показывают ноль?",
                "a": "Это намеренно. Если текущий repricing плоский, Pulse делает fallback на более широкое окно и молчит, если рынок всё ещё не движется.",
            },
        ],
    },
    "top-movers": {
        "en": [
            {
                "q": "Are top movers ranked only by raw delta?",
                "a": "The public movers surface is delta-first, but the broader product also uses liquidity and live coverage logic for better candidate quality and watchlist suggestions.",
            },
            {
                "q": "Can I add a mover directly to my watchlist?",
                "a": "Yes. The bot supports one-tap add and replacement flows so live movers can become watchlist markets immediately.",
            },
        ],
        "ru": [
            {
                "q": "Ранжируются ли top movers только по сырой дельте?",
                "a": "Публичная movers-поверхность delta-first, но сам продукт также использует ликвидность и live-coverage логику для лучшего качества кандидатов и watchlist-подсказок.",
            },
            {
                "q": "Можно ли добавить mover прямо в watchlist?",
                "a": "Да. Бот поддерживает сценарий one-tap add и replacement, так что live movers можно сразу превращать в watchlist-рынки.",
            },
        ],
    },
    "watchlist": {
        "en": [
            {
                "q": "Does adding a market to watchlist automatically enable alerts?",
                "a": "No. Watchlist and alerts are separate concepts. A saved market does not need to become a Telegram alert until you decide it should.",
            },
            {
                "q": "Where do threshold and alert settings live?",
                "a": "Telegram is the current control loop for identity, threshold, and alert delivery. The watchlist is the market set; Telegram decides when to wake you up.",
            },
        ],
        "ru": [
            {
                "q": "Добавление рынка в watchlist автоматически включает алерты?",
                "a": "Нет. Watchlist и alerts - разные вещи. Сохранённый рынок не обязан сразу становиться Telegram-алертом.",
            },
            {
                "q": "Где живут threshold и alert-настройки?",
                "a": "Сейчас Telegram - основной контур для identity, threshold и доставки алертов. Watchlist задаёт набор рынков, а Telegram решает, когда вас будить.",
            },
        ],
    },
    "watchlist-alerts": {
        "en": [
            {
                "q": "What does the free plan include?",
                "a": "Free currently includes 3 watchlist markets and 20 alerts per day. Pro extends that to 20 markets, unlimited alerts, and email digest.",
            },
            {
                "q": "Why might a watchlist market stay quiet after I add it?",
                "a": "The market may be closed, may not have current bid/ask quotes, or may not have cleared your threshold in the latest window.",
            },
        ],
        "ru": [
            {
                "q": "Что входит в free-план?",
                "a": "Free сейчас включает 3 рынка в watchlist и 20 алертов в день. Pro расширяет это до 20 рынков, безлимитных алертов и email-дайджеста.",
            },
            {
                "q": "Почему рынок в watchlist может молчать после добавления?",
                "a": "Рынок может быть закрыт, может не иметь текущих bid/ask котировок или не пройти ваш threshold в последнем окне.",
            },
        ],
    },
}

SEO_PAGE_LINKS: dict[str, list[str]] = {
    "analytics": ["signals", "top-movers", "watchlist", "telegram-bot"],
    "dashboard": ["analytics", "signals", "watchlist", "telegram-bot"],
    "signals": ["telegram-bot", "watchlist", "top-movers", "analytics"],
    "telegram-bot": ["signals", "top-movers", "watchlist", "analytics"],
    "top-movers": ["watchlist", "telegram-bot", "signals", "analytics"],
    "watchlist": ["watchlist-alerts", "signals", "telegram-bot", "top-movers"],
    "watchlist-alerts": ["watchlist", "signals", "telegram-bot", "analytics"],
}

SEO_PAGE_CTA_NOTE: dict[str, dict[str, str]] = {
    "dashboard": {
        "en": "Use the bot for the move itself, not for another dashboard tab that waits to be ignored.",
        "ru": "Используйте бота ради самого движения, а не ради ещё одной dashboard-вкладки, которую легко забыть.",
    },
    "analytics": {
        "en": "Open the bot, pin one market, and see whether the latest repricing actually deserves attention.",
        "ru": "Откройте бота, закрепите один рынок и сразу увидите, заслуживает ли последнее движение внимания.",
    },
    "signals": {
        "en": "Set a threshold, keep noise low, and let Telegram surface only the repricing that matters.",
        "ru": "Выставьте threshold, уберите шум и получайте в Telegram только действительно значимый repricing.",
    },
    "telegram-bot": {
        "en": "No wallet and no dashboard required. Start with movers, add one live market, and get to first value fast.",
        "ru": "Не нужен ни кошелёк, ни dashboard. Начните с movers, добавьте один live-рынок и быстро получите первую ценность.",
    },
    "top-movers": {
        "en": "When the short window wakes up, the fastest route to action is one tap into the bot.",
        "ru": "Когда короткое окно оживает, самый быстрый путь к действию — один тап в бота.",
    },
    "watchlist": {
        "en": "Use the watchlist to decide what deserves attention. Enable Telegram alerts only after the saved market set feels right.",
        "ru": "Используйте watchlist, чтобы сначала решить, что вообще заслуживает внимания. Telegram-алерты включайте уже после этого.",
    },
    "watchlist-alerts": {
        "en": "Use Telegram for action now, keep email as backup for digest and launch updates.",
        "ru": "Используйте Telegram для действий сейчас, а email оставьте как backup для дайджеста и обновлений.",
    },
}

SITE_NAV_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("top-movers", "/top-movers", "Live Movers"),
    ("signals", "/signals", "Signals"),
    ("watchlist", "/watchlist", "Watchlist"),
    ("commands", "/commands", "Commands"),
    ("pricing", "/#pricing", "Pricing"),
)

SITE_NAV_ACTIVE_ALIASES: dict[str, str] = {
    "top-movers": "top-movers",
    "signals": "signals",
    "watchlist": "watchlist",
    "watchlist-alerts": "watchlist",
    "commands": "commands",
}

SITE_PAGE_LABELS: dict[str, dict[str, str]] = {
    "index": {"en": "Homepage", "ru": "Главная"},
    "analytics": {"en": "Analytics", "ru": "Аналитика"},
    "dashboard": {"en": "Dashboard", "ru": "Dashboard"},
    "signals": {"en": "Signals", "ru": "Сигналы"},
    "telegram-bot": {"en": "Telegram Bot", "ru": "Telegram-бот"},
    "top-movers": {"en": "Live Movers", "ru": "Live Movers"},
    "watchlist": {"en": "Watchlist", "ru": "Watchlist"},
    "watchlist-alerts": {"en": "Watchlist Alerts", "ru": "Watchlist alerts"},
    "how-it-works": {"en": "How It Works", "ru": "Как это работает"},
    "commands": {"en": "Commands", "ru": "Команды"},
}


def _site_page_label(page_key: str, lang: Literal["ru", "en"]) -> str:
    return SITE_PAGE_LABELS.get(page_key, {}).get(lang) or page_key.replace("-", " ").title()


def _render_site_header(
    *,
    current_page: str,
    lang: Literal["ru", "en"],
    telegram_href: str,
    guide_href: str,
    guide_text: str,
) -> str:
    active_nav = SITE_NAV_ACTIVE_ALIASES.get(current_page, "")
    page_chip = html.escape(_site_page_label(current_page, lang))
    cta_text = "Open Telegram Bot" if lang == "en" else "Открыть Telegram-бота"
    nav_html = []
    menu_html = []
    for item_key, href, label in SITE_NAV_ITEMS:
        active_attr = ' aria-current="page"' if active_nav == item_key else ""
        active_cls = " active" if active_nav == item_key else ""
        nav_html.append(
            f'<a class="site-nav-link{active_cls}" href="{href}"{active_attr}>{label}</a>'
        )
        menu_html.append(
            f'<a class="site-menu-link{active_cls}" href="{href}"{active_attr}>{label}</a>'
        )

    return f"""
    <header class="site-header reveal delay-1">
      <div class="site-header-inner">
        <a class="site-brand" href="/">
          <span class="site-brand-mark">Polymarket Pulse</span>
          <span class="site-brand-copy">Signal terminal</span>
        </a>
        <nav class="site-nav" aria-label="Primary">
          {''.join(nav_html)}
        </nav>
        <div class="site-actions">
          <span class="site-page-chip">{page_chip}</span>
          <a class="site-guide-link{' active' if current_page == 'how-it-works' else ''}" href="{guide_href}">{guide_text}</a>
          <a class="site-cta" href="{telegram_href}" target="_blank" rel="noopener noreferrer">{cta_text}</a>
        </div>
        <details class="site-menu">
          <summary class="site-menu-summary">Menu</summary>
          <div class="site-menu-panel">
            <span class="site-page-chip">{page_chip}</span>
            {''.join(menu_html)}
            <a class="site-menu-link{' active' if current_page == 'how-it-works' else ''}" href="{guide_href}">{guide_text}</a>
            <a class="site-cta" href="{telegram_href}" target="_blank" rel="noopener noreferrer">{cta_text}</a>
          </div>
        </details>
      </div>
    </header>
"""


class WaitlistRequest(BaseModel):
    email: EmailStr
    source: str = "site"
    details: dict | None = None


class SiteEventRequest(BaseModel):
    event_type: str
    source: str = "site"
    details: dict | None = None


class StripeCheckoutRequest(BaseModel):
    email: EmailStr
    user_id: str | None = None
    source: str = "site"
    lang: Literal["ru", "en"] | None = None


class TraderAlphaRequest(BaseModel):
    email: EmailStr
    user_id: str | None = None
    telegram_id: int | None = None
    chat_id: int | None = None
    source: str = "site"
    details: dict | None = None


class TraderSignerSubmitRequest(BaseModel):
    token: str
    signed_payload: str


class WatchlistAuthStartRequest(BaseModel):
    intent: Literal["login", "watchlist_add", "alert", "return_watchlist"] = "login"
    market_id: str | None = None
    return_path: str | None = "/watchlist"
    locale: Literal["ru", "en"] | None = None
    question: str | None = None
    source: str = "site"


class WatchlistSaveRequest(BaseModel):
    market_id: str
    question: str | None = None
    slug: str | None = None
    source: str = "site"


class WatchlistSyncRequest(BaseModel):
    items: list[WatchlistSaveRequest]


HOT_PREVIEW_MAX_FRESHNESS_SECONDS = int(os.environ.get("HOT_PREVIEW_MAX_FRESHNESS_SECONDS", "120"))
HOT_PREVIEW_MIN_LIQUIDITY = float(os.environ.get("HOT_PREVIEW_MIN_LIQUIDITY", "1000"))
HOT_PREVIEW_MAX_SPREAD = float(os.environ.get("HOT_PREVIEW_MAX_SPREAD", "0.25"))
WATCHLIST_CLIENT_ASSET_VERSION = "20260429e"
WATCHLIST_CLIENT_ASSET_PATH = f"/api/watchlist-client?v={WATCHLIST_CLIENT_ASSET_VERSION}"
WATCHLIST_WORKSPACE_SPARK_SNAPSHOTS = int(os.environ.get("WATCHLIST_WORKSPACE_SPARK_SNAPSHOTS", "14"))
WATCHLIST_WORKSPACE_SPARK_POINTS = int(os.environ.get("WATCHLIST_WORKSPACE_SPARK_POINTS", "14"))


SQL_HOT_LIVE_MOVERS_PREVIEW = """
with hot as (
  select
    r.market_id,
    r.question,
    r.slug,
    q.quote_ts as last_bucket,
    prev.ts_bucket as prev_bucket,
    q.mid_yes as yes_mid_now,
    prev.mid_yes_prev as yes_mid_prev,
    (q.mid_yes - prev.mid_yes_prev)::double precision as delta_yes,
    m1.delta_mid::double precision as delta_1m,
    coalesce(q.liquidity, 0)::double precision as liquidity,
    q.spread::double precision as spread,
    q.freshness_seconds::double precision as freshness_seconds
  from public.hot_market_registry_latest r
  join public.hot_market_quotes_latest q using (market_id)
  left join public.hot_top_movers_1m m1 using (market_id)
  join lateral (
    with per_bucket as (
      select
        ms.ts_bucket,
        max(coalesce(((ms.yes_bid + ms.yes_ask) / 2.0), ms.yes_bid, ms.yes_ask))::double precision as mid_yes_prev
      from public.market_snapshots ms
      where ms.market_id = r.market_id
        and (ms.yes_bid is not null or ms.yes_ask is not null)
      group by ms.ts_bucket
    )
    select ts_bucket, mid_yes_prev
    from per_bucket
    where mid_yes_prev is not null
      and ts_bucket <= q.quote_ts - interval '4 minutes'
    order by ts_bucket desc
    limit 1
  ) prev on true
  where coalesce(r.status, 'active') = 'active'
    and q.has_two_sided_quote
    and q.mid_yes is not null
    and q.freshness_seconds <= %s
    and coalesce(q.liquidity, 0) >= %s
    and coalesce(q.spread, 0) <= %s
)
select
  market_id,
  question,
  slug,
  last_bucket,
  prev_bucket,
  yes_mid_now,
  yes_mid_prev,
  delta_yes,
  delta_1m,
  liquidity,
  spread,
  freshness_seconds,
  'hot'::text as source,
  'live_quality_gated'::text as signal_quality
from hot
order by abs(delta_yes) desc nulls last, liquidity desc nulls last
limit %s;
"""

SQL_LIVE_MOVERS_PREVIEW_LEGACY = """
select
  tm.market_id,
  coalesce(tm.question, m.question) as question,
  m.slug,
  tm.last_bucket,
  tm.prev_bucket,
  tm.yes_mid_now,
  tm.yes_mid_prev,
  tm.delta_yes,
  null::double precision as liquidity,
  null::double precision as spread,
  null::double precision as freshness_seconds,
  'legacy'::text as source,
  'legacy_fallback'::text as signal_quality
from public.top_movers_latest tm
join public.markets m on m.market_id = tm.market_id
where tm.yes_mid_now is not null
  and tm.yes_mid_prev is not null
order by abs(delta_yes) desc nulls last
limit %s;
"""

SQL_LIVE_SPARKLINE_POINTS = """
with per_bucket as (
  select
    ms.market_id,
    ms.ts_bucket,
    max(coalesce(((ms.yes_bid + ms.yes_ask) / 2.0), ms.yes_bid, ms.yes_ask))::double precision as yes_mid
  from public.market_snapshots ms
  where ms.market_id = any(%s::text[])
    and (ms.yes_bid is not null or ms.yes_ask is not null)
  group by ms.market_id, ms.ts_bucket
),
ranked as (
  select
    market_id,
    ts_bucket,
    yes_mid as mid,
    row_number() over (partition by market_id order by ts_bucket desc) as rn
  from per_bucket
  where yes_mid is not null
)
select
  market_id,
  ts_bucket,
  mid
from ranked
where rn <= %s
order by market_id, ts_bucket asc;
"""

SQL_WATCHLIST_WORKSPACE = """
with wanted as (
  select distinct unnest(%s::text[]) as market_id
)
select
  w.market_id,
  coalesce(r.question, m.question, tm.question, w.market_id) as question,
  coalesce(r.slug, m.slug) as slug,
  coalesce(r.status, m.status, 'unknown') as market_status,
  coalesce(q.quote_ts, hm5.quote_ts, tm.last_bucket) as quote_ts,
  coalesce(q.mid_yes, hm5.current_mid, tm.yes_mid_now)::double precision as yes_mid_now,
  coalesce(hm5.prev_mid, tm.yes_mid_prev)::double precision as yes_mid_prev_5m,
  hm1.delta_mid::double precision as delta_1m,
  hm5.delta_mid::double precision as delta_5m,
  coalesce(hm5.delta_mid, tm.delta_yes)::double precision as delta_primary,
  q.liquidity::double precision as liquidity,
  q.spread::double precision as spread,
  q.freshness_seconds::double precision as freshness_seconds,
  q.has_two_sided_quote,
  case
    when coalesce(r.status, m.status, 'unknown') <> 'active' then 'market_closed'
    when coalesce(q.mid_yes, hm5.current_mid, tm.yes_mid_now) is null then 'no_quotes'
    when q.freshness_seconds is not null and q.freshness_seconds > %s then 'stale_quotes'
    when q.spread is not null and q.spread > %s then 'filtered_by_spread'
    when q.liquidity is not null and q.liquidity < %s then 'filtered_by_liquidity'
    when q.mid_yes is not null then 'saved'
    when hm5.current_mid is not null or tm.yes_mid_now is not null then 'legacy_snapshot'
    else 'no_quotes'
  end as row_state,
  case
    when coalesce(r.status, m.status, 'unknown') <> 'active' then 'market_closed'
    when coalesce(q.mid_yes, hm5.current_mid, tm.yes_mid_now) is null then 'no_quotes'
    when q.freshness_seconds is not null and q.freshness_seconds > %s then 'stale_quotes'
    when q.spread is not null and q.spread > %s then 'filtered_by_spread'
    when q.liquidity is not null and q.liquidity < %s then 'filtered_by_liquidity'
    when q.mid_yes is not null then 'live_quality_gated'
    when hm5.current_mid is not null or tm.yes_mid_now is not null then 'legacy_fallback'
    else 'no_quotes'
  end as signal_quality
from wanted w
left join public.hot_market_registry_latest r using (market_id)
left join public.markets m using (market_id)
left join public.hot_market_quotes_latest q using (market_id)
left join public.hot_top_movers_1m hm1 using (market_id)
left join public.hot_top_movers_5m hm5 using (market_id)
left join public.top_movers_latest tm using (market_id);
"""

SQL_WATCHLIST_WORKSPACE_USER = """
with wanted as (
  select
    w.market_id,
    w.created_at as saved_at
  from bot.watchlist w
  where w.user_id = %s::uuid
  order by w.created_at desc
  limit 100
), last_alert as (
  select
    market_id,
    max(sent_at) as last_alert_at
  from bot.sent_alerts_log
  where user_id = %s::uuid
    and channel = 'bot'
    and alert_type = 'watchlist'
  group by market_id
)
select
  w.market_id,
  w.saved_at,
  coalesce(r.question, m.question, tm.question, w.market_id) as question,
  coalesce(r.slug, m.slug) as slug,
  coalesce(r.status, m.status, 'unknown') as market_status,
  coalesce(q.quote_ts, hm5.quote_ts, tm.last_bucket) as quote_ts,
  coalesce(q.mid_yes, hm5.current_mid, tm.yes_mid_now)::double precision as yes_mid_now,
  coalesce(hm5.prev_mid, tm.yes_mid_prev)::double precision as yes_mid_prev_5m,
  hm1.delta_mid::double precision as delta_1m,
  hm5.delta_mid::double precision as delta_5m,
  coalesce(hm5.delta_mid, tm.delta_yes)::double precision as delta_primary,
  q.liquidity::double precision as liquidity,
  q.spread::double precision as spread,
  q.freshness_seconds::double precision as freshness_seconds,
  q.has_two_sided_quote,
  coalesce(s.alert_enabled, false) as alert_enabled,
  coalesce(s.alert_paused, false) as alert_paused,
  s.threshold_value::double precision as alert_threshold_value,
  coalesce(s.threshold_value, u.threshold, 0.03)::double precision as effective_threshold_value,
  coalesce(s.last_alert_at, la.last_alert_at) as last_alert_at,
  case
    when coalesce(r.status, m.status, 'unknown') <> 'active' then 'market_closed'
    when coalesce(q.mid_yes, hm5.current_mid, tm.yes_mid_now) is null then 'no_quotes'
    when q.freshness_seconds is not null and q.freshness_seconds > %s then 'stale_quotes'
    when q.spread is not null and q.spread > %s then 'filtered_by_spread'
    when q.liquidity is not null and q.liquidity < %s then 'filtered_by_liquidity'
    when q.mid_yes is not null then 'saved'
    when hm5.current_mid is not null or tm.yes_mid_now is not null then 'legacy_snapshot'
    else 'no_quotes'
  end as row_state,
  case
    when coalesce(r.status, m.status, 'unknown') <> 'active' then 'market_closed'
    when coalesce(q.mid_yes, hm5.current_mid, tm.yes_mid_now) is null then 'no_quotes'
    when q.freshness_seconds is not null and q.freshness_seconds > %s then 'stale_quotes'
    when q.spread is not null and q.spread > %s then 'filtered_by_spread'
    when q.liquidity is not null and q.liquidity < %s then 'filtered_by_liquidity'
    when q.mid_yes is not null then 'live_quality_gated'
    when hm5.current_mid is not null or tm.yes_mid_now is not null then 'legacy_fallback'
    else 'no_quotes'
  end as signal_quality
from wanted w
left join public.hot_market_registry_latest r using (market_id)
left join public.markets m using (market_id)
left join public.hot_market_quotes_latest q using (market_id)
left join public.hot_top_movers_1m hm1 using (market_id)
left join public.hot_top_movers_5m hm5 using (market_id)
left join public.top_movers_latest tm using (market_id)
left join bot.watchlist_alert_settings s
  on s.user_id = %s::uuid
 and s.market_id = w.market_id
left join bot.user_settings u
  on u.user_id = %s::uuid
left join last_alert la
  on la.market_id = w.market_id;
"""

SQL_WEB_AUTH_REQUEST_INSERT = """
insert into app.web_auth_requests (
  request_token,
  market_id,
  intent,
  return_path,
  locale,
  payload,
  expires_at
)
values (
  %s,
  %s,
  %s,
  %s,
  %s,
  %s,
  now() + make_interval(mins => %s)
);
"""

SQL_WEB_AUTH_REQUEST_COMPLETE = """
update app.web_auth_requests
set user_id = %s::uuid,
    telegram_id = %s,
    chat_id = %s,
    status = 'completed',
    completed_at = now(),
    payload = coalesce(payload, '{}'::jsonb) || %s::jsonb
where request_token = %s
  and expires_at > now()
returning
  id,
  request_token,
  market_id,
  intent,
  return_path,
  locale,
  status,
  user_id,
  payload,
  expires_at;
"""

SQL_WEB_AUTH_REQUEST_SELECT = """
select
  id,
  request_token,
  market_id,
  intent,
  return_path,
  locale,
  status,
  user_id,
  payload,
  expires_at
from app.web_auth_requests
where request_token = %s
limit 1;
"""

SQL_WEB_AUTH_REQUEST_CLAIM = """
update app.web_auth_requests
set status = 'claimed',
    claimed_at = now()
where request_token = %s
  and status = 'completed'
  and expires_at > now()
returning
  id,
  request_token,
  market_id,
  intent,
  return_path,
  locale,
  user_id,
  payload;
"""

SQL_WEB_SESSION_INSERT = """
insert into app.web_sessions (
  session_token,
  user_id,
  source,
  expires_at,
  user_agent,
  ip,
  payload
)
values (
  %s,
  %s::uuid,
  'telegram',
  now() + make_interval(days => %s),
  %s,
  %s,
  %s
);
"""

SQL_WEB_SESSION_SELECT = """
select
  s.session_token,
  s.user_id,
  s.created_at,
  s.expires_at,
  s.last_seen_at,
  p.telegram_id,
  p.chat_id,
  p.username,
  p.first_name,
  p.last_name,
  p.locale
from app.web_sessions s
left join bot.profiles p
  on p.user_id = s.user_id
where s.session_token = %s
  and s.expires_at > now()
limit 1;
"""

SQL_WEB_SESSION_TOUCH = """
update app.web_sessions
set last_seen_at = now()
where session_token = %s;
"""

SQL_SITE_WATCHLIST_ADD = """
insert into bot.watchlist (user_id, market_id)
values (%s::uuid, %s)
on conflict (user_id, market_id) do nothing;
"""

SQL_SITE_WATCHLIST_REMOVE = """
delete from bot.watchlist
where user_id = %s::uuid
  and market_id = %s;
"""

SQL_SITE_ALERT_SETTINGS_UPSERT = """
insert into bot.watchlist_alert_settings (
  user_id,
  market_id,
  alert_enabled,
  alert_paused,
  threshold_value,
  source
)
values (
  %s::uuid,
  %s,
  %s,
  %s,
  %s,
  %s
)
on conflict (user_id, market_id) do update
set alert_enabled = excluded.alert_enabled,
    alert_paused = excluded.alert_paused,
    threshold_value = coalesce(excluded.threshold_value, bot.watchlist_alert_settings.threshold_value),
    source = excluded.source,
    updated_at = now();
"""

SQL_ENSURE_PAYMENT_EVENTS = """
create table if not exists app.payment_events (
  id bigserial primary key,
  provider text not null,
  external_id text not null,
  event_type text not null,
  status text not null default 'succeeded',
  user_id uuid references app.users(id) on delete set null,
  email text,
  amount_cents bigint,
  currency text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (provider, external_id)
);
"""

SQL_PAYMENT_EVENT_EXISTS = """
select 1
from app.payment_events
where provider = %s
  and external_id = %s
limit 1;
"""

SQL_PAYMENT_EVENT_INSERT = """
insert into app.payment_events (
  provider,
  external_id,
  event_type,
  status,
  user_id,
  email,
  amount_cents,
  currency,
  payload
)
values (%s, %s, %s, %s, %s::uuid, %s, %s, %s, %s);
"""

SQL_SUBSCRIPTION_INSERT_PRO = """
insert into app.subscriptions (
  user_id,
  plan,
  status,
  source,
  started_at,
  renew_at
)
values (
  %s::uuid,
  'pro',
  'active',
  %s,
  now(),
  now() + make_interval(days => %s)
)
returning renew_at;
"""

SQL_PROFILE_SET_PRO = """
update bot.profiles
set plan = 'pro',
    updated_at = now()
where user_id = %s::uuid;
"""

SQL_ENSURE_TRADE_ALPHA_WAITLIST = """
create schema if not exists trade;

create table if not exists trade.alpha_waitlist (
  id bigserial primary key,
  email text not null unique,
  user_id uuid references app.users(id) on delete set null,
  telegram_id bigint,
  chat_id bigint,
  source text not null default 'site',
  status text not null default 'new',
  use_case text not null default 'execution_alpha',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (source in ('site', 'pulse_bot', 'telegram_bot', 'x', 'threads', 'manual')),
  check (status in ('new', 'review', 'approved', 'declined'))
);
"""

SQL_TRADE_ALPHA_WAITLIST_UPSERT = """
insert into trade.alpha_waitlist (
  email,
  user_id,
  telegram_id,
  chat_id,
  source,
  status,
  use_case,
  details
)
values (%s, %s::uuid, %s, %s, %s, 'new', 'execution_alpha', %s)
on conflict (email) do update
set user_id = coalesce(trade.alpha_waitlist.user_id, excluded.user_id),
    telegram_id = coalesce(trade.alpha_waitlist.telegram_id, excluded.telegram_id),
    chat_id = coalesce(trade.alpha_waitlist.chat_id, excluded.chat_id),
    source = excluded.source,
    details = trade.alpha_waitlist.details || excluded.details,
    updated_at = now()
returning id;
"""

SQL_SIGNER_SESSION_LOOKUP = """
select
  ss.id,
  ss.account_id,
  a.user_id,
  ss.wallet_link_id,
  ss.session_token,
  ss.status,
  ss.challenge_text,
  ss.signed_payload,
  ss.verified_at,
  ss.expires_at,
  ss.created_at,
  wl.wallet_address,
  wl.status as wallet_status,
  wl.signer_kind
from trade.signer_sessions ss
join trade.accounts a on a.id = ss.account_id
join trade.wallet_links wl on wl.id = ss.wallet_link_id
where ss.session_token = %s
limit 1;
"""

SQL_SIGNER_SESSION_OPEN = """
update trade.signer_sessions
set status = 'opened',
    updated_at = now()
where id = %s
  and status = 'new'
returning id;
"""

SQL_SIGNER_SESSION_SUBMIT = """
update trade.signer_sessions
set status = case when status = 'verified' then 'verified' else 'signed' end,
    signed_payload = %s::jsonb,
    updated_at = now()
where id = %s
returning id, status, expires_at, verified_at;
"""

SQL_SIGNER_ACTIVITY = """
insert into trade.activity_events (
  user_id,
  account_id,
  event_type,
  source,
  market_id,
  details
) values (%s::uuid, %s, %s, 'site', null, %s::jsonb);
"""


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


def detect_site_lang(request: Request) -> Literal["ru", "en"]:
    q_lang = (request.query_params.get("lang") or "").strip().lower()
    if q_lang == "ru":
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


def _safe_return_path(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        return "/watchlist"
    if not raw.startswith("/"):
        return "/watchlist"
    if raw.startswith("//") or raw.startswith("/auth/telegram/complete"):
        return "/watchlist"
    return raw[:512]


def _build_site_start_payload(*, intent: str, market_id: str | None, token: str) -> str:
    clean_market_id = _safe_market_token(market_id, max_len=48)
    if intent == "watchlist_add" and clean_market_id:
        return f"site_watchlist_add_{clean_market_id}_{token}"
    if intent == "alert" and clean_market_id:
        return f"site_alert_{clean_market_id}_{token}"
    if intent == "return_watchlist":
        return f"site_return_watchlist_{token}"
    return f"site_login_{token}"


def build_site_telegram_url(*, intent: str, market_id: str | None, token: str) -> str:
    payload = _build_site_start_payload(intent=intent, market_id=market_id, token=token)
    return f"https://t.me/polymarket_pulse_bot?start={quote(payload)}"


def fetch_site_session(token: str) -> dict | None:
    if not PG_CONN or not token:
        return None
    with psycopg.connect(PG_CONN, connect_timeout=5, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '6000ms'")
            cur.execute(SQL_WEB_SESSION_SELECT, (token,))
            row = cur.fetchone()
            if row:
                cur.execute(SQL_WEB_SESSION_TOUCH, (token,))
                conn.commit()
            return dict(row) if row else None


def current_site_session(request: Request) -> dict | None:
    token = str(request.cookies.get(WEB_SESSION_COOKIE) or "").strip()
    if not token:
        return None
    try:
        return fetch_site_session(token)
    except Exception:
        logger.exception("site session lookup failed")
        return None


def create_web_auth_request(
    *,
    intent: str,
    market_id: str | None,
    return_path: str,
    locale: str,
    payload: dict | None,
) -> str:
    if not PG_CONN:
        raise HTTPException(status_code=500, detail="PG_CONN is not configured")
    token = secrets.token_urlsafe(24)
    with psycopg.connect(PG_CONN, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '6000ms'")
            cur.execute(
                SQL_WEB_AUTH_REQUEST_INSERT,
                (
                    token,
                    _safe_market_token(market_id, max_len=48) or None,
                    intent,
                    _safe_return_path(return_path),
                    "ru" if locale == "ru" else "en",
                    Jsonb(payload or {}),
                    WEB_AUTH_REQUEST_MINUTES,
                ),
            )
        conn.commit()
    return token


def create_site_session(
    *,
    user_id: str,
    request: Request,
    auth_request: dict,
) -> str:
    if not PG_CONN:
        raise HTTPException(status_code=500, detail="PG_CONN is not configured")
    token = secrets.token_urlsafe(32)
    payload = {
        "auth_request_id": auth_request.get("id"),
        "intent": auth_request.get("intent"),
        "market_id": auth_request.get("market_id"),
    }
    with psycopg.connect(PG_CONN, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '6000ms'")
            cur.execute(
                SQL_WEB_SESSION_INSERT,
                (
                    token,
                    user_id,
                    WEB_SESSION_DAYS,
                    request.headers.get("user-agent"),
                    request.client.host if request.client else None,
                    Jsonb(payload),
                ),
            )
        conn.commit()
    return token


def site_session_response_redirect(url: str, *, session_token: str) -> RedirectResponse:
    response = RedirectResponse(url=url, status_code=303)
    secure = base_url().startswith("https://")
    response.set_cookie(
        WEB_SESSION_COOKIE,
        session_token,
        max_age=WEB_SESSION_DAYS * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )
    return response


def render_seo_page(slug: str, lang: Literal["ru", "en"], *, noindex_override: bool = False) -> str:
    page = SEO_PAGES[slug][lang]
    faq_items = SEO_PAGE_FAQ.get(slug, {}).get(lang, [])
    related_page_slugs = SEO_PAGE_LINKS.get(slug, [name for name in SEO_PAGES if name != slug])
    cta_text = "Open Telegram Bot" if lang == "en" else "Открыть Telegram-бота"
    cta_guide_text = "How it works" if lang == "en" else "Как это работает?"
    cta_backup_link_text = "Keep email as backup" if lang == "en" else "Email как backup"
    back_text = "Back to homepage" if lang == "en" else "На главную"
    links_head = "Related pages" if lang == "en" else "Связанные страницы"
    faq_head = "Common questions" if lang == "en" else "Частые вопросы"
    preview_head = "Preview surfaces" if lang == "en" else "Ключевые экраны"
    cta_note = SEO_PAGE_CTA_NOTE.get(slug, {}).get(
        lang,
        "Open the bot first. Add markets second. Let the signal layer tell you when to care."
        if lang == "en"
        else "Сначала откройте бота. Потом добавьте рынки. Пусть signal-слой сам подскажет, когда пора реагировать.",
    )
    cta_backup_note = (
        "Keep email only as a backup for digest and launch updates. Telegram stays the primary live loop."
        if lang == "en"
        else "Оставляйте email только как backup для дайджеста и обновлений. Telegram остаётся основным live-каналом."
    )
    preview_copy_1 = (
        "Catch the fastest repricing in the current live window."
        if lang == "en"
        else "Показывает самые быстрые переоценки в текущем live-окне."
    )
    preview_copy_2 = (
        "Tune sensitivity per user and keep your feed clean."
        if lang == "en"
        else "Настраивает чувствительность под пользователя и убирает шум."
    )
    preview_copy_3 = (
        "Telegram delivery loop with clear time-window context."
        if lang == "en"
        else "Telegram-доставка с понятным контекстом временного окна."
    )
    page_stats = _seo_page_stats(slug, lang)
    (stat_1_label, stat_1_value, stat_1_copy), (stat_2_label, stat_2_value, stat_2_copy), (stat_3_label, stat_3_value, stat_3_copy) = page_stats
    badge_1 = "4.8/5 trader score" if lang == "en" else "4.8/5 оценка трейдеров"
    badge_3 = "Telegram-first flow" if lang == "en" else "Telegram-first сценарий"
    screen_label = "Screen" if lang == "en" else "Экран"
    page_view_js_lang = "en" if lang == "en" else "ru"
    base = base_url()
    canonical_url = f"{base}/{slug}"
    robots_meta = "index,follow" if lang == "en" else "noindex,follow"
    og_image_url = f"{base}/og-card.svg"
    page_schema = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "@id": canonical_url,
            "url": canonical_url,
            "name": page["title"],
            "description": page["description"],
            "inLanguage": "en-US" if lang == "en" else "ru-RU",
            "isPartOf": {"@type": "WebSite", "url": base, "name": "Polymarket Pulse"},
            "about": {
                "@type": "Thing",
                "name": "Polymarket Pulse Telegram bot for live analytics and signals"
                if slug == "telegram-bot" and lang == "en"
                else "Polymarket live analytics and Telegram signals"
            },
        },
        ensure_ascii=False,
    )
    faq_schema = ""
    if faq_items:
        faq_schema = json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": item["q"],
                        "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
                    }
                    for item in faq_items
                ],
            },
            ensure_ascii=False,
        )
    faq_schema_tag = f'<script type="application/ld+json">{faq_schema}</script>' if faq_schema else ""
    faq_cards = "".join(
        f'<article class="faq-card"><h3 class="faq-question">{html.escape(item["q"])}</h3><p class="faq-answer">{html.escape(item["a"])}</p></article>'
        for item in faq_items
    )
    faq_block = (
        f"""
    <section class="links-wrap reveal delay-4">
      <p class="links-title">{faq_head}</p>
      <div class="faq-grid">
        {faq_cards}
      </div>
    </section>
"""
        if faq_items
        else ""
    )

    links = "".join(
        f'<a href="/{name}">{html.escape(_site_page_label(name, lang))}</a>'
        for name in related_page_slugs
        if name in SEO_PAGES and name != slug and name != "trader-bot"
    )
    guide_href = f"/how-it-works?placement=seo_{slug}_guide"
    backup_href = f"/?placement=seo_{slug}_backup#waitlist-form"
    guide_cta = f'<a id="guide-link" class="cta-secondary" href="{guide_href}">{cta_guide_text}</a>'
    backup_cta = f'<a id="backup-link" class="cta-backup-link" href="{backup_href}">{cta_backup_link_text}</a>'
    header_html = _render_site_header(
        current_page=slug,
        lang=lang,
        telegram_href=f"https://t.me/polymarket_pulse_bot?start=seo_{slug}_{lang}_header",
        guide_href=guide_href,
        guide_text=cta_guide_text,
    )
    compare_head = "Why Pulse instead of another dashboard" if lang == "en" else "Почему Pulse, а не ещё один dashboard"
    compare_title = (
        "Open the bot. Track one market. Ignore the dashboard bloat."
        if lang == "en"
        else "Скорость для нормального пользователя важнее терминального косплея."
    )
    compare_1 = (
        "<strong>Dashboard tools</strong> make you search for a move. <strong>Pulse</strong> pushes the move into Telegram."
        if lang == "en"
        else "<strong>Dashboard-инструменты</strong> заставляют вас искать движение. <strong>Pulse</strong> приносит его прямо в Telegram."
    )
    compare_2 = (
        "<strong>Noisy alert feeds</strong> force you to second-guess every ping. <strong>Pulse</strong> starts from actual repricing and honest quiet states."
        if lang == "en"
        else "<strong>Шумные алерты</strong> заставляют сомневаться в каждом пинге. <strong>Pulse</strong> стартует с реального repricing и честных quiet-state."
    )
    compare_3 = (
        "<strong>Our edge</strong>: signal first, watchlist second, action only when the move is worth caring about."
        if lang == "en"
        else "<strong>Наш угол атаки</strong>: сначала сигнал, потом watchlist, а действие только когда движение реально заслуживает внимания."
    )
    compare_block = (
        f"""
    <section id="seo-bridge" class="links-wrap reveal delay-4">
      <p class="links-title">{compare_head}</p>
      <div class="preview-grid">
        <article class="preview-card">
          <p class="preview-kicker">01</p>
          <h3 class="preview-title">{compare_title}</h3>
          <p class="preview-copy">{compare_1}</p>
        </article>
        <article class="preview-card">
          <p class="preview-kicker">02</p>
          <h3 class="preview-title">Trust the feed</h3>
          <p class="preview-copy">{compare_2}</p>
        </article>
        <article class="preview-card">
          <p class="preview-kicker">03</p>
          <h3 class="preview-title">Signal-first stack</h3>
          <p class="preview-copy">{compare_3}</p>
        </article>
      </div>
    </section>
"""
        if slug == "telegram-bot"
        else ""
    )
    bot_flow_block = (
        """
    <section id="bot-command-flow" class="command-flow reveal delay-3">
      <div class="command-flow-head">
        <p class="links-title">BOT FLOW</p>
        <p class="command-flow-subtitle">The fastest useful path is not a dashboard tour. It is one live market, one threshold, and one quiet inbox that only wakes up when the move matters.</p>
      </div>
      <div class="command-grid">
        <article class="command-card">
          <p class="command-name">/start</p>
          <h3 class="command-title">Open the signal layer</h3>
          <p class="command-copy">Start in Telegram without wallet setup. Pulse is analytics-first; trading execution is a separate product layer.</p>
        </article>
        <article class="command-card">
          <p class="command-name">/movers</p>
          <h3 class="command-title">See what is repricing now</h3>
          <p class="command-copy">Use live movers to find a market worth tracking instead of guessing which Polymarket tab deserves attention.</p>
        </article>
        <article class="command-card">
          <p class="command-name">/watchlist</p>
          <h3 class="command-title">Pin the market</h3>
          <p class="command-copy">Track the markets you actually care about and keep the rest of Polymarket out of your alert stream.</p>
        </article>
        <article class="command-card">
          <p class="command-name">/threshold</p>
          <h3 class="command-title">Set your noise filter</h3>
          <p class="command-copy">A 0.03 threshold means 3 percentage points. Inbox alerts only when abs(delta) clears your personal level.</p>
        </article>
        <article class="command-card strong">
          <p class="command-name">/inbox</p>
          <h3 class="command-title">Act only when it matters</h3>
          <p class="command-copy">Watchlist may move while Inbox stays empty. That is intentional: quiet is a product state, not a bug.</p>
        </article>
      </div>
    </section>
"""
        if slug == "telegram-bot" and lang == "en"
        else ""
    )
    bridge_block = (
        """
    <section class="links-wrap reveal delay-4">
      <p class="links-title">FASTEST NEXT STEP</p>
      <div class="preview-grid">
        <article class="preview-card">
          <p class="preview-kicker">01</p>
          <h3 class="preview-title">Open the bot now</h3>
          <p class="preview-copy">If the intent is already clear, skip the extra tabs. Open Telegram, hit /start, and add one live market before the move gets stale.</p>
        </article>
        <article class="preview-card">
          <p class="preview-kicker">02</p>
          <h3 class="preview-title">What you get</h3>
          <p class="preview-copy">Top movers, watchlist tracking, and Inbox alerts live in one Telegram flow instead of forcing another dashboard habit.</p>
        </article>
        <article class="preview-card">
          <p class="preview-kicker">03</p>
          <h3 class="preview-title">Backup, not a detour</h3>
          <p class="preview-copy">Email stays optional and secondary. Telegram remains the shortest path to first value and the main live signal loop.</p>
        </article>
      </div>
      <div class="cta-row" style="margin-top:14px;">
        <a id="tg-link-bridge" class="cta" href="https://t.me/polymarket_pulse_bot?start=seo_telegram-bot_bridge_en" target="_blank" rel="noopener noreferrer">Open Telegram Bot →</a>
        <a id="guide-link-bridge" class="cta-secondary" href="/how-it-works?placement=seo_telegram-bot_bridge_guide">See the bot flow</a>
      </div>
      <p class="cta-note">The goal here is not another dashboard. It is one clean move from search intent to a live market in Telegram.</p>
    </section>
"""
        if slug == "telegram-bot" and lang == "en"
        else ""
    )
    live_signal_block = _render_signal_quality_block(slug, lang)
    hero_focus_block = _render_page_focus_block(slug, lang)
    if slug == "telegram-bot" and lang == "en":
        hero_focus_block = bot_flow_block
        bot_flow_block = ""
    hero_live_signal_block = live_signal_block if slug in {"signals", "top-movers"} else ""
    body_live_signal_block = "" if slug in {"signals", "top-movers"} else live_signal_block
    watchlist_workspace_block = _render_watchlist_workspace_block(lang) if slug == "watchlist" else ""
    watchlist_workspace_lead = watchlist_workspace_block if slug == "watchlist" else ""
    watchlist_workspace_tail = "" if slug == "watchlist" else watchlist_workspace_block
    hero_card_class = "card reveal delay-2 watchlist-card-compact" if slug == "watchlist" else "card reveal delay-2"
    hero_stats_block = (
        ""
        if slug == "watchlist"
        else f"""
      <div class="stats">
        <article class="stat">
          <p class="stat-label">{stat_1_label}</p>
          <p class="stat-value">{stat_1_value}</p>
          <p class="stat-copy">{stat_1_copy}</p>
        </article>
        <article class="stat">
          <p class="stat-label">{stat_2_label}</p>
          <p class="stat-value">{stat_2_value}</p>
          <p class="stat-copy">{stat_2_copy}</p>
        </article>
        <article class="stat">
          <p class="stat-label">{stat_3_label}</p>
          <p class="stat-value">{stat_3_value}</p>
          <p class="stat-copy">{stat_3_copy}</p>
        </article>
      </div>
"""
    )
    hero_feature_rows = (
        ""
        if slug == "watchlist"
        else f"""
      <div class="feature-rows">
        <div class="feature-row">{page["k1"]}</div>
        <div class="feature-row">{page["k2"]}</div>
        <div class="feature-row">{page["k3"]}</div>
      </div>
"""
    )
    preview_block = (
        ""
        if slug == "watchlist"
        else f"""
    <section class="preview reveal delay-3">
      <p class="links-title">{preview_head}</p>
      <div class="preview-grid">
        <article class="preview-card">
          <p class="preview-kicker">{screen_label} 01</p>
          <h3 class="preview-title">{page["k1"]}</h3>
          <p class="preview-copy">{preview_copy_1}</p>
          <div class="preview-bar" style="--w:72%;"><span></span></div>
        </article>
        <article class="preview-card">
          <p class="preview-kicker">{screen_label} 02</p>
          <h3 class="preview-title">{page["k2"]}</h3>
          <p class="preview-copy">{preview_copy_2}</p>
          <div class="preview-bar" style="--w:58%;"><span></span></div>
        </article>
        <article class="preview-card">
          <p class="preview-kicker">{screen_label} 03</p>
          <h3 class="preview-title">{page["k3"]}</h3>
          <p class="preview-copy">{preview_copy_3}</p>
          <div class="preview-bar down" style="--w:36%;"><span></span></div>
        </article>
      </div>
    </section>
"""
    )
    robots_meta = "index,follow" if lang == "en" else "noindex,follow"
    if noindex_override:
        robots_meta = "noindex,follow"

    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{page["title"]}</title>
  <meta name="description" content="{page["description"]}" />
  <meta name="robots" content="{robots_meta}" />
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
  <link rel="icon" type="image/svg+xml" sizes="any" href="/favicon.svg" />
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
  <link rel="icon" type="image/png" sizes="48x48" href="/favicon-48x48.png" />
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
  <link rel="shortcut icon" href="/favicon.ico" />
  <script defer src="{WATCHLIST_CLIENT_ASSET_PATH}"></script>
  <script type="application/ld+json">{page_schema}</script>
  {faq_schema_tag}
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-J901VRQH4G"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-J901VRQH4G');
  </script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
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
      --negative: #ff4444;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Space Grotesk", "Segoe UI", sans-serif;
      background:
        radial-gradient(1200px 800px at 85% -20%, rgba(0, 255, 136, 0.08) 0%, transparent 60%),
        radial-gradient(900px 600px at -10% 10%, rgba(0, 255, 136, 0.05) 0%, transparent 58%),
        linear-gradient(180deg, var(--bg-2) 0%, var(--bg) 60%, var(--bg-2) 100%);
      color: var(--text);
      min-height: 100vh;
      overflow-x: hidden;
    }}
    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.015) 1px, transparent 1px);
      background-size: 28px 28px;
      opacity: 0.16;
    }}
    @keyframes rise-in {{
      from {{ opacity: 0; transform: translateY(14px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .reveal {{
      opacity: 0;
      animation: rise-in 0.28s ease forwards;
    }}
    .reveal.delay-1 {{ animation-delay: 0.08s; }}
    .reveal.delay-2 {{ animation-delay: 0.16s; }}
    .reveal.delay-3 {{ animation-delay: 0.24s; }}
    .reveal.delay-4 {{ animation-delay: 0.32s; }}
    body.ready .reveal {{ opacity: 1; }}
    .wrap {{
      width: min(1080px, calc(100% - 32px));
      margin: 0 auto;
      padding: 24px 0 48px;
      position: relative;
      z-index: 1;
    }}
    .site-header {{
      position: sticky;
      top: 12px;
      z-index: 24;
      margin-bottom: 18px;
    }}
    .site-header-inner {{
      display: flex;
      align-items: center;
      gap: 12px;
      border: 1px solid rgba(42, 51, 43, 0.92);
      border-radius: 16px;
      padding: 10px 12px;
      background: rgba(13, 15, 14, 0.84);
      backdrop-filter: blur(16px);
      box-shadow: 0 18px 48px rgba(0, 0, 0, 0.32);
    }}
    .site-brand {{
      min-width: 0;
      display: grid;
      gap: 2px;
      text-decoration: none;
    }}
    .site-brand-mark {{
      color: var(--text);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      line-height: 1;
    }}
    .site-brand-copy {{
      color: var(--muted-soft);
      font-family: "JetBrains Mono", monospace;
      font-size: 10px;
      line-height: 1;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .site-nav {{
      display: flex;
      flex: 1;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }}
    .site-nav-link,
    .site-guide-link,
    .site-page-chip,
    .site-menu-link {{
      border: 1px solid var(--line-soft);
      border-radius: 999px;
      padding: 7px 10px;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1;
      text-decoration: none;
      background: rgba(19, 23, 20, 0.72);
      white-space: nowrap;
    }}
    .site-page-chip {{
      color: var(--text);
      border-color: rgba(255, 255, 255, 0.08);
    }}
    .site-nav-link:hover,
    .site-nav-link:focus-visible,
    .site-guide-link:hover,
    .site-guide-link:focus-visible,
    .site-menu-link:hover,
    .site-menu-link:focus-visible {{
      color: var(--text);
      border-color: var(--accent);
      outline: none;
    }}
    .site-nav-link.active,
    .site-guide-link.active,
    .site-menu-link.active {{
      color: var(--text);
      border-color: rgba(0, 255, 136, 0.42);
      box-shadow: 0 0 0 1px rgba(0, 255, 136, 0.16) inset;
    }}
    .site-actions {{
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 8px;
      margin-left: auto;
    }}
    .site-cta {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 40px;
      padding: 10px 14px;
      border-radius: 12px;
      text-decoration: none;
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      font-weight: 700;
      color: var(--bg-2);
      background: linear-gradient(180deg, #00ff88 0%, #00d874 100%);
      border: 1px solid var(--accent);
      white-space: nowrap;
    }}
    .site-menu {{
      display: none;
      margin-left: auto;
      position: relative;
    }}
    .site-menu[open] {{
      z-index: 30;
    }}
    .site-menu-summary {{
      list-style: none;
      cursor: pointer;
      border: 1px solid var(--line-soft);
      border-radius: 999px;
      padding: 8px 12px;
      color: var(--text);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      background: rgba(19, 23, 20, 0.92);
    }}
    .site-menu-summary::-webkit-details-marker {{
      display: none;
    }}
    .site-menu-panel {{
      position: absolute;
      right: 0;
      top: calc(100% + 10px);
      min-width: 240px;
      display: grid;
      gap: 8px;
      padding: 12px;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: rgba(13, 15, 14, 0.98);
      box-shadow: 0 20px 54px rgba(0, 0, 0, 0.42);
    }}
    .card {{
      margin-top: 16px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 24px;
      box-shadow: 0 24px 72px rgba(0, 0, 0, 0.42), inset 0 0 0 1px rgba(255, 255, 255, 0.015);
    }}
    .badge-row {{
      margin-bottom: 14px;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      color: var(--muted);
      letter-spacing: 0.07em;
      text-transform: uppercase;
    }}
    .badge {{
      border: 1px solid var(--line-soft);
      border-radius: 999px;
      padding: 6px 10px;
      background: rgba(19, 23, 20, 0.72);
    }}
    .badge.active {{
      border-color: rgba(0, 255, 136, 0.45);
      color: var(--text);
      box-shadow: 0 0 0 1px rgba(0, 255, 136, 0.18) inset;
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
      font-family: "JetBrains Mono", monospace;
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
      font-family: "JetBrains Mono", monospace;
      color: var(--muted);
      font-size: 13px;
    }}
    .stats {{
      margin-top: 16px;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}
    .stat {{
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 11px 12px;
      background: rgba(19, 23, 20, 0.88);
    }}
    .stat-label {{
      margin: 0;
      color: var(--muted-soft);
      font-family: "JetBrains Mono", monospace;
      font-size: 11px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }}
    .stat-value {{
      margin: 6px 0 0;
      font-size: clamp(19px, 3vw, 27px);
      line-height: 1;
      letter-spacing: -0.02em;
    }}
    .stat-copy {{
      margin: 6px 0 0;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.4;
    }}
    .cta-row {{
      margin-top: 18px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
    }}
    .cta {{
      display:inline-flex; align-items:center; justify-content:center;
      min-height: 48px; padding: 10px 16px; border-radius: 12px; text-decoration: none;
      font-family: "JetBrains Mono", monospace; font-weight: 700;
      color: var(--bg-2); background: linear-gradient(180deg, #00ff88 0%, #00d874 100%);
      border: 1px solid var(--accent);
    }}
    .cta-secondary {{
      display:inline-flex; align-items:center; justify-content:center;
      min-height: 48px; padding: 10px 16px; border-radius: 12px; text-decoration: none;
      font-family: "JetBrains Mono", monospace; font-weight: 700;
      color: var(--text); background: #131714;
      border: 1px solid var(--line-soft);
    }}
    .cta-secondary:hover, .cta-secondary:focus-visible {{ border-color: var(--accent); outline: none; }}
    .cta-trust {{
      margin-top: 10px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .trust-pill {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 6px 10px;
      background: #131714;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 11px;
      line-height: 1;
    }}
    .cta-note {{
      margin: 10px 0 0;
      color: var(--muted-soft);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.55;
    }}
    .cta-backup-note {{
      margin: 8px 0 0;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.5;
    }}
    .cta-backup-link-wrap {{
      margin: 8px 0 0;
    }}
    .cta-backup-link {{
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.5;
      text-decoration: underline;
      text-underline-offset: 2px;
    }}
    .cta-backup-link:hover, .cta-backup-link:focus-visible {{
      color: var(--text);
      outline: none;
    }}
    .preview {{
      margin-top: 16px;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px;
      background: #131714;
    }}
    .preview-grid {{
      margin-top: 10px;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}
    .preview-card {{
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
      background: #131714;
      transition: transform 0.2s ease, border-color 0.2s ease;
    }}
    .preview-card:hover {{
      transform: translateY(-2px);
      border-color: rgba(0, 255, 136, 0.36);
    }}
    .preview-kicker {{
      margin: 0;
      color: var(--muted-soft);
      font-family: "JetBrains Mono", monospace;
      font-size: 11px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }}
    .preview-title {{
      margin: 8px 0 0;
      font-size: 17px;
      line-height: 1.15;
      letter-spacing: -0.01em;
    }}
    .preview-copy {{
      margin: 8px 0 0;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.45;
    }}
    .preview-bar {{
      margin-top: 10px;
      height: 7px;
      border-radius: 999px;
      background: #0c0f0d;
      border: 1px solid var(--line);
      overflow: hidden;
      position: relative;
    }}
    .preview-bar > span {{
      position: absolute;
      inset: 0 auto 0 0;
      width: var(--w, 50%);
      border-radius: 999px;
      background: linear-gradient(90deg, #00cc6f 0%, #00ff88 100%);
    }}
    .preview-bar.down > span {{
      background: linear-gradient(90deg, #ff4444 0%, #ff6d6d 100%);
    }}
    .links-wrap {{
      margin-top: 16px;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px;
      background: #131714;
    }}
    .command-flow {{
      margin-top: 16px;
      border: 1px solid rgba(0, 255, 136, 0.18);
      border-radius: 16px;
      padding: 14px;
      background:
        radial-gradient(700px 220px at 10% 0%, rgba(0, 255, 136, 0.08), transparent 58%),
        #101511;
    }}
    .command-flow-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: end;
      margin-bottom: 10px;
    }}
    .command-flow-subtitle {{
      margin: 0;
      max-width: 520px;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.45;
      text-align: right;
    }}
    .command-grid {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 9px;
    }}
    .command-card {{
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
      background: #131714;
    }}
    .command-card.strong {{
      border-color: rgba(0, 255, 136, 0.34);
      background: linear-gradient(180deg, rgba(0, 255, 136, 0.055), rgba(19, 23, 20, 0.95));
    }}
    .command-name {{
      margin: 0;
      color: var(--accent);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      font-weight: 700;
    }}
    .command-title {{
      margin: 9px 0 0;
      color: var(--text);
      font-size: 15px;
      line-height: 1.1;
    }}
    .command-copy {{
      margin: 8px 0 0;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 11px;
      line-height: 1.45;
    }}
    .live-signal-board {{
      margin-top: 16px;
      border: 1px solid rgba(0, 255, 136, 0.2);
      border-radius: 16px;
      padding: 14px;
      background:
        linear-gradient(180deg, rgba(0, 255, 136, 0.045), rgba(0, 0, 0, 0) 42%),
        #101511;
    }}
    .live-signal-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: end;
      margin-bottom: 10px;
    }}
    .live-signal-subtitle {{
      margin: 0;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.4;
      text-align: right;
      max-width: 420px;
    }}
    .live-signal-list {{
      display: grid;
      gap: 10px;
    }}
    .live-signal-row {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 14px;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
      background: #131714;
    }}
    .live-signal-question {{
      margin: 0;
      color: var(--text);
      font-size: 15px;
      line-height: 1.25;
    }}
    .live-signal-meta {{
      margin: 7px 0 0;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.4;
    }}
    .live-signal-quality {{
      margin-top: 8px;
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .live-signal-pill {{
      border: 1px solid var(--line-soft);
      border-radius: 999px;
      padding: 4px 7px;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 10px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      white-space: nowrap;
    }}
    .live-signal-pill.strong {{
      color: var(--text);
      border-color: rgba(0, 255, 136, 0.28);
      background: rgba(0, 255, 136, 0.07);
    }}
    .live-signal-side {{
      display: flex;
      flex-direction: column;
      align-items: end;
      justify-content: space-between;
      gap: 10px;
    }}
    .live-signal-delta {{
      font-family: "JetBrains Mono", monospace;
      font-size: 20px;
      line-height: 1;
    }}
    .live-signal-delta.up {{ color: var(--accent); }}
    .live-signal-delta.down {{ color: var(--negative); }}
    .live-signal-tape {{
      margin-top: 5px;
      display: block;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 11px;
      text-align: right;
      white-space: nowrap;
    }}
    .live-signal-actions {{
      display: flex;
      justify-content: flex-end;
      flex-wrap: wrap;
      gap: 7px;
    }}
    .live-signal-link {{
      appearance: none;
      background: #131714;
      cursor: pointer;
      border: 1px solid var(--line-soft);
      border-radius: 999px;
      padding: 7px 9px;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 11px;
      text-decoration: none;
      white-space: nowrap;
    }}
    .live-signal-link.primary {{
      color: var(--text);
      border-color: rgba(0, 255, 136, 0.32);
    }}
    .live-signal-link.saved {{
      color: var(--text);
      border-color: rgba(0, 255, 136, 0.42);
      box-shadow: 0 0 0 1px rgba(0, 255, 136, 0.16) inset;
    }}
    .live-signal-empty {{
      border: 1px dashed var(--line-soft);
      border-radius: 12px;
      padding: 16px;
      background: rgba(19, 23, 20, 0.72);
    }}
    .live-signal-empty p {{
      margin: 8px 0 0;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.5;
    }}
    .live-signal-link:hover,
    .live-signal-link:focus-visible {{
      border-color: var(--accent);
      color: var(--text);
      outline: none;
    }}
    .watchlist-workspace {{
      margin-top: 16px;
      border: 1px solid rgba(0, 255, 136, 0.18);
      border-radius: 16px;
      padding: 14px;
      background:
        radial-gradient(820px 280px at 10% 0%, rgba(0, 255, 136, 0.07), transparent 58%),
        #101511;
    }}
    .watchlist-workspace-head {{
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 12px;
      margin-bottom: 12px;
    }}
    .watchlist-workspace-copy,
    .watchlist-login-copy {{
      margin: 0;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.5;
      max-width: 620px;
    }}
    .watchlist-login-inline {{
      display: grid;
      gap: 8px;
      justify-items: end;
    }}
    .watchlist-root {{
      display: grid;
      gap: 12px;
    }}
    .watchlist-summary {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}
    .watchlist-summary-card {{
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #131714;
      padding: 14px;
      display: grid;
      gap: 6px;
    }}
    .watchlist-summary-card strong {{
      font-size: clamp(20px, 3vw, 28px);
      line-height: 1;
      letter-spacing: -0.02em;
    }}
    .watchlist-summary-card span {{
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.4;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .watchlist-empty,
    .watchlist-banner,
    .watchlist-table-wrap,
    .watchlist-card-grid {{
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #131714;
    }}
    .watchlist-empty,
    .watchlist-banner {{
      padding: 16px;
    }}
    .watchlist-banner.success {{
      border-color: rgba(0, 255, 136, 0.32);
      box-shadow: 0 0 0 1px rgba(0, 255, 136, 0.12) inset;
    }}
    .watchlist-empty h3,
    .watchlist-banner h3 {{
      margin: 0;
      font-size: 18px;
      line-height: 1.15;
    }}
    .watchlist-empty p,
    .watchlist-banner p {{
      margin: 10px 0 0;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.5;
    }}
    .watchlist-banner-actions {{
      margin-top: 12px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .watchlist-controls {{
      display: grid;
      grid-template-columns: minmax(220px, 1.4fr) repeat(4, minmax(0, 1fr)) auto;
      gap: 8px;
      align-items: center;
    }}
    .watchlist-input,
    .watchlist-select,
    .watchlist-view-btn {{
      width: 100%;
      min-height: 42px;
      border: 1px solid var(--line-soft);
      border-radius: 12px;
      background: #0f1410;
      color: var(--text);
      padding: 10px 12px;
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
    }}
    .watchlist-view-btn {{
      cursor: pointer;
      white-space: nowrap;
    }}
    .watchlist-table-wrap {{
      overflow-x: auto;
    }}
    .watchlist-table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 1120px;
    }}
    .watchlist-table th,
    .watchlist-table td {{
      padding: 12px 10px;
      border-bottom: 1px solid rgba(42, 51, 43, 0.72);
      text-align: left;
      vertical-align: top;
    }}
    .watchlist-table th {{
      color: var(--muted-soft);
      font-family: "JetBrains Mono", monospace;
      font-size: 11px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }}
    .watchlist-table tr:last-child td {{
      border-bottom: 0;
    }}
    .watchlist-table.compact th,
    .watchlist-table.compact td {{
      padding-top: 8px;
      padding-bottom: 8px;
    }}
    .watchlist-question {{
      margin: 0;
      font-size: 14px;
      line-height: 1.3;
    }}
    .watchlist-table td:first-child {{
      min-width: 280px;
    }}
    .watchlist-question-meta {{
      margin: 6px 0 0;
      color: var(--muted-soft);
      font-family: "JetBrains Mono", monospace;
      font-size: 11px;
      line-height: 1.4;
    }}
    .watchlist-spark {{
      margin-top: 12px;
      width: 236px;
      max-width: 100%;
      height: 64px;
      display: block;
    }}
    .watchlist-spark .spark-frame {{
      fill: rgba(255, 255, 255, 0.012);
      stroke: rgba(42, 51, 43, 0.82);
      stroke-width: 1;
    }}
    .watchlist-spark .spark-grid {{
      stroke: rgba(143, 168, 143, 0.16);
      stroke-width: 1;
      stroke-dasharray: 3 4;
    }}
    .watchlist-spark .spark-area {{
      opacity: 0.22;
    }}
    .watchlist-spark polyline {{
      fill: none;
      stroke-width: 2.2;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}
    .watchlist-spark.down .spark-area {{
      fill: rgba(255, 91, 91, 0.12);
    }}
    .watchlist-spark.down polyline {{
      stroke: #ff5b5b;
    }}
    .watchlist-spark.up .spark-area {{
      fill: rgba(0, 255, 136, 0.12);
    }}
    .watchlist-spark.up polyline {{
      stroke: var(--accent);
    }}
    .watchlist-chip-row,
    .watchlist-action-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .watchlist-chip {{
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      border-radius: 999px;
      border: 1px solid var(--line-soft);
      padding: 0 8px;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 10px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      white-space: nowrap;
      background: rgba(19, 23, 20, 0.72);
    }}
    .watchlist-chip.strong {{
      color: var(--text);
      border-color: rgba(0, 255, 136, 0.3);
      background: rgba(0, 255, 136, 0.08);
    }}
    .watchlist-chip.down {{
      border-color: rgba(255, 68, 68, 0.28);
      color: #ffd3d3;
    }}
    .watchlist-action {{
      appearance: none;
      border: 1px solid var(--line-soft);
      border-radius: 999px;
      padding: 7px 10px;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 11px;
      background: #131714;
      text-decoration: none;
      cursor: pointer;
    }}
    .watchlist-action:hover,
    .watchlist-action:focus-visible,
    .watchlist-view-btn:hover,
    .watchlist-view-btn:focus-visible {{
      border-color: var(--accent);
      color: var(--text);
      outline: none;
    }}
    .watchlist-action.primary {{
      color: var(--text);
      border-color: rgba(0, 255, 136, 0.32);
    }}
    .watchlist-action.saved {{
      color: var(--text);
      border-color: rgba(0, 255, 136, 0.22);
      box-shadow: 0 0 0 1px rgba(0, 255, 136, 0.12) inset;
    }}
    .watchlist-card-grid {{
      display: none;
      padding: 10px;
      gap: 10px;
    }}
    .watchlist-card-compact {{
      padding-top: 20px;
      padding-bottom: 20px;
    }}
    .watchlist-card-compact h1 {{
      font-size: clamp(30px, 5vw, 48px);
    }}
    .watchlist-card-compact .intro {{
      max-width: 980px;
      font-size: clamp(14px, 1.6vw, 18px);
    }}
    .watchlist-card {{
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
      background: #101511;
      display: grid;
      gap: 10px;
    }}
    .watchlist-card .watchlist-spark {{
      width: 100%;
    }}
    .watchlist-card-top {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: start;
    }}
    .faq-grid {{
      margin-top: 10px;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }}
    .faq-card {{
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 14px;
      background: #0f1410;
    }}
    .faq-question {{
      margin: 0;
      color: var(--text);
      font-size: 16px;
      line-height: 1.25;
    }}
    .faq-answer {{
      margin: 10px 0 0;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.55;
    }}
    .links-title {{
      margin: 0 0 8px;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
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
      font-family: "JetBrains Mono", monospace;
      font-size:13px;
      text-align: center;
    }}
    .links a:hover, .links a:focus-visible {{ border-color: var(--accent); color: var(--text); outline: none; }}
    .back {{
      margin-top: 14px;
      display: inline-block;
      color: var(--muted-soft);
      text-decoration: underline;
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
    }}
    .back:hover, .back:focus-visible {{ color: var(--text); outline: none; }}
    @media (max-width: 900px) {{
      .site-header-inner {{
        align-items: start;
      }}
      .site-nav,
      .site-actions {{
        display: none;
      }}
      .site-menu {{
        display: block;
      }}
      .stats {{ grid-template-columns: 1fr; }}
      .preview-grid {{ grid-template-columns: 1fr 1fr; }}
      .links {{ grid-template-columns: 1fr 1fr; }}
      .faq-grid {{ grid-template-columns: 1fr; }}
      .command-flow-head {{ display: block; }}
      .command-flow-subtitle {{ margin-top: 8px; text-align: left; }}
      .command-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .live-signal-head {{ display: block; }}
      .live-signal-subtitle {{ margin-top: 8px; text-align: left; }}
      .watchlist-workspace-head {{ display: block; }}
      .watchlist-login-inline {{ margin-top: 10px; justify-items: start; }}
      .watchlist-controls {{ grid-template-columns: 1fr 1fr; }}
    }}
    @media (max-width: 640px) {{
      .wrap {{ width: calc(100% - 20px); }}
      .card {{ padding: 16px; border-radius: 16px; }}
      .badge-row {{ gap: 6px; }}
      .cta {{ width: 100%; }}
      .cta-secondary {{ width: 100%; }}
      .preview-grid {{ grid-template-columns: 1fr; }}
      .links {{ grid-template-columns: 1fr; }}
      .command-grid {{ grid-template-columns: 1fr; }}
      .live-signal-row {{ grid-template-columns: 1fr; }}
      .live-signal-side {{ align-items: start; }}
      .live-signal-actions {{ justify-content: flex-start; }}
      .watchlist-controls {{ grid-template-columns: 1fr; }}
      .watchlist-summary {{ grid-template-columns: 1fr; }}
      .watchlist-table-wrap {{ display: none; }}
      .watchlist-card-grid {{ display: grid; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{
        animation: none !important;
        transition: none !important;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    {header_html}
    {watchlist_workspace_lead}
    <article class="{hero_card_class}">
      <div class="badge-row">
        <span class="badge active">{badge_1}</span>
        <span class="badge">{badge_3}</span>
      </div>
      <h1>{page["h1"]}</h1>
      <p class="intro">{page["intro"]}</p>
      {hero_stats_block}
      {hero_feature_rows}
      {hero_focus_block}
      <div class="cta-row">
        <a id="tg-link" class="cta" href="https://t.me/polymarket_pulse_bot?start=seo_{slug}_{lang}" target="_blank" rel="noopener noreferrer">{cta_text} →</a>
        {guide_cta}
      </div>
      <div class="cta-trust" aria-label="Telegram trust strip">
        <span class="trust-pill">No signup required</span>
        <span class="trust-pill">1 tap to open</span>
        <span class="trust-pill">Email backup only</span>
      </div>
      <p class="cta-note">{cta_note}</p>
      <p class="cta-backup-note">{cta_backup_note}</p>
      <p class="cta-backup-link-wrap">{backup_cta}</p>
      {hero_live_signal_block}
    </article>
    {watchlist_workspace_tail}
    {preview_block}
    {bot_flow_block}
    {body_live_signal_block}
    {compare_block}
    {bridge_block}
    {faq_block}
    <section class="links-wrap reveal delay-4">
      <p class="links-title">{links_head}</p>
      <div class="links" aria-label="{links_head}">
        {links}
      </div>
    </section>
      <a class="back" href="/">{back_text}</a>
  </div>
  <script>
    document.body.classList.add('ready');

    async function trackEvent(eventType, details = {{}}) {{
      const eventDetails = {{
        page_path: window.location.pathname + window.location.search,
        page_url: window.location.href,
        ...details
      }};
      try {{
        if (typeof window.gtag === 'function') {{
          window.gtag('event', eventType, eventDetails);
        }}
      }} catch (_) {{}}
      try {{
        await fetch('/api/events', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ event_type: eventType, source: 'site', details: eventDetails }}),
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
    const liveSignalSurface = document.getElementById('live-signal-surface');
    if (liveSignalSurface) {{
      const emitLiveBoardSeen = () => trackEvent('live_board_impression', {{ ...details, placement: 'seo_live_signal_board' }});
      if ('IntersectionObserver' in window) {{
        const liveBoardObserver = new IntersectionObserver((entries) => {{
          entries.forEach((entry) => {{
            if (!entry.isIntersecting) return;
            emitLiveBoardSeen();
            liveBoardObserver.disconnect();
          }});
        }}, {{ threshold: 0.35 }});
        liveBoardObserver.observe(liveSignalSurface);
      }} else {{
        emitLiveBoardSeen();
      }}
    }}
    liveSignalSurface?.addEventListener('click', (event) => {{
      const target = event.target instanceof Element ? event.target.closest('[data-market-action]') : null;
      if (!target) return;
      const action = target.getAttribute('data-market-action') || '';
      const marketId = target.getAttribute('data-market-id') || '';
      const payload = {{ ...details, placement: 'seo_live_signal_board', action, market_id: marketId }};
      if (action === 'track_telegram') {{
        trackEvent('tg_click', payload);
        return;
      }}
      if (action === 'open_polymarket') {{
        trackEvent('market_click', payload);
      }}
    }});
    const seoBridge = document.getElementById('seo-bridge');
    if ('IntersectionObserver' in window && seoBridge) {{
      const observer = new IntersectionObserver((entries) => {{
        entries.forEach((entry) => {{
          if (!entry.isIntersecting || entry.target.dataset.seen === 'true') return;
          entry.target.dataset.seen = 'true';
          trackEvent('page_view', {{ ...details, placement: 'seo_bridge', surface_impression: true }});
          observer.unobserve(entry.target);
        }});
      }}, {{ threshold: 0.35 }});
      observer.observe(seoBridge);
    }}
    document.getElementById('tg-link')?.addEventListener('click', () => {{
      trackEvent('tg_click', details);
    }});
    document.getElementById('tg-link-bridge')?.addEventListener('click', () => {{
      trackEvent('tg_click', {{ ...details, placement: 'seo_bridge' }});
    }});
    document.getElementById('guide-link')?.addEventListener('click', () => {{
      trackEvent('waitlist_intent', {{ ...details, placement: 'seo_guide' }});
    }});
    document.getElementById('guide-link-bridge')?.addEventListener('click', () => {{
      trackEvent('waitlist_intent', {{ ...details, placement: 'seo_bridge_guide' }});
    }});
    document.getElementById('backup-link')?.addEventListener('click', () => {{
      trackEvent('waitlist_intent', {{ ...details, placement: 'seo_backup' }});
    }});
  </script>
</body>
</html>
"""


def fetch_signer_session(token: str) -> dict | None:
    if not PG_CONN:
        return None
    with psycopg.connect(PG_CONN, connect_timeout=5, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '8000ms'")
            cur.execute(SQL_SIGNER_SESSION_LOOKUP, (token,))
            return cur.fetchone()


def touch_signer_session_open(session_id: int) -> None:
    if not PG_CONN:
        return
    with psycopg.connect(PG_CONN, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '5000ms'")
            cur.execute(SQL_SIGNER_SESSION_OPEN, (session_id,))
        conn.commit()


def save_signer_payload(token: str, signed_payload: str, request: Request) -> dict:
    if not PG_CONN:
        raise HTTPException(status_code=500, detail="PG_CONN is not configured")
    session = fetch_signer_session(token)
    if not session:
        raise HTTPException(status_code=404, detail="signer_session_not_found")
    expires_at = session.get("expires_at")
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="signer_session_expired")

    clean_payload = signed_payload.strip()
    if not clean_payload:
        raise HTTPException(status_code=400, detail="signed_payload_required")

    payload_obj = {
        "raw": clean_payload,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "user_agent": request.headers.get("user-agent"),
        "ip": request.client.host if request.client else None,
    }

    with psycopg.connect(PG_CONN, connect_timeout=8, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '8000ms'")
            cur.execute(SQL_SIGNER_SESSION_SUBMIT, (Jsonb(payload_obj), session["id"]))
            updated = cur.fetchone()
            cur.execute(
                SQL_SIGNER_ACTIVITY,
                (
                    session["user_id"],
                    session["account_id"],
                    "signer_payload_submitted",
                    Jsonb(
                        {
                            "session_token": token,
                            "wallet": session["wallet_address"],
                            "status": updated["status"] if updated else "signed",
                        }
                    ),
                ),
            )
        conn.commit()

    return {
        "wallet": session["wallet_address"],
        "status": updated["status"] if updated else "signed",
        "expires_at": _to_iso(updated["expires_at"] if updated else session.get("expires_at")),
        "verified_at": _to_iso(updated["verified_at"] if updated else session.get("verified_at")),
    }


def render_trader_connect_page(session: dict, lang: Literal["ru", "en"]) -> str:
    base = base_url()
    title = "Trader signer session" if lang == "en" else "Signer-session Trader"
    intro = (
        "This page stores your signed payload for alpha review. It does not unlock live execution by itself."
        if lang == "en"
        else "Эта страница сохраняет signed payload для alpha-review. Сама по себе она не включает live execution."
    )
    kicker = "SIGNER SESSION · ALPHA" if lang == "en" else "SIGNER SESSION · ALPHA"
    submit_label = "Store signed payload" if lang == "en" else "Сохранить signed payload"
    challenge_label = "Challenge" if lang == "en" else "Challenge"
    payload_label = "Signed payload" if lang == "en" else "Signed payload"
    payload_placeholder = (
        "Paste signature / signed message / wallet-exported payload here"
        if lang == "en"
        else "Вставьте сюда signature / signed message / payload из кошелька"
    )
    status_note = (
        "// After submit, session moves to signed. A real verify/activation layer is still required."
        if lang == "en"
        else "// После submit сессия перейдёт в signed. Реальный verify/activation слой всё ещё нужен."
    )
    open_bot = "Open Trader bot" if lang == "en" else "Открыть Trader-бота"
    open_trader_page = "Trader page" if lang == "en" else "Страница Trader"
    success_wait = (
        "Payload stored. Session is now signed and ready for the next verify layer."
        if lang == "en"
        else "Payload сохранён. Сессия теперь в статусе signed и готова к следующему verify-слою."
    )
    expired = False
    if session.get("expires_at"):
        try:
            expired = session["expires_at"] < datetime.now(timezone.utc)
        except Exception:
            expired = False
    wallet = html.escape(str(session.get("wallet_address") or "n/a"))
    status = html.escape(str(session.get("status") or "n/a"))
    wallet_status = html.escape(str(session.get("wallet_status") or "n/a"))
    signer_kind = html.escape(str(session.get("signer_kind") or "n/a"))
    challenge = html.escape(str(session.get("challenge_text") or ""))
    expires_at = html.escape(_to_iso(session.get("expires_at")) or "n/a")
    verified_at = html.escape(_to_iso(session.get("verified_at")) or "n/a")
    token = html.escape(str(session.get("session_token") or ""))
    disabled_attr = "disabled" if expired else ""
    disabled_copy = (
        "This signer session has expired. Return to Telegram and run /signer again."
        if lang == "en"
        else "Эта signer-session истекла. Вернитесь в Telegram и снова запустите /signer."
    )
    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <meta name="robots" content="noindex,nofollow" />
  <link rel="icon" type="image/svg+xml" sizes="any" href="/favicon.svg" />
  <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
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
      --danger: #ff5a5a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: "Space Grotesk", "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(1200px 800px at 85% -20%, rgba(0, 255, 136, 0.08) 0%, transparent 60%),
        linear-gradient(180deg, var(--bg-2) 0%, var(--bg) 55%, var(--bg-2) 100%);
    }}
    .wrap {{
      width: min(980px, calc(100% - 32px));
      margin: 0 auto;
      padding: 24px 0 48px;
    }}
    .top {{
      display:flex;
      justify-content:space-between;
      align-items:center;
      gap: 12px;
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      color: var(--muted);
    }}
    .card {{
      margin-top: 16px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 24px;
      box-shadow: 0 24px 72px rgba(0,0,0,0.42);
    }}
    .kicker {{
      margin: 0 0 12px;
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      color: var(--muted-soft);
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 0;
      line-height: 0.96;
      font-size: clamp(32px, 7vw, 56px);
      text-transform: uppercase;
      letter-spacing: -0.03em;
    }}
    .intro {{
      margin: 12px 0 0;
      color: var(--muted);
      font-size: 16px;
      line-height: 1.5;
      font-family: "JetBrains Mono", monospace;
    }}
    .grid {{
      margin-top: 20px;
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 18px;
      align-items: start;
    }}
    .stack {{
      display: grid;
      gap: 12px;
    }}
    .panel {{
      background: #131714;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px;
    }}
    .label {{
      margin: 0 0 8px;
      color: var(--muted-soft);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .value, .mono, textarea {{
      font-family: "JetBrains Mono", monospace;
    }}
    .value {{
      color: var(--text);
      font-size: 14px;
      line-height: 1.6;
      word-break: break-word;
    }}
    .status-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }}
    .status-pill {{
      border: 1px solid var(--line-soft);
      border-radius: 10px;
      padding: 10px 12px;
      background: #0f1410;
    }}
    .status-pill strong {{
      display: block;
      margin-top: 6px;
      font-family: "JetBrains Mono", monospace;
      font-size: 13px;
    }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: "JetBrains Mono", monospace;
      font-size: 13px;
      line-height: 1.55;
      color: var(--text);
    }}
    textarea {{
      width: 100%;
      min-height: 220px;
      background: #0d0f0e;
      color: var(--text);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 14px;
      font-size: 13px;
      resize: vertical;
    }}
    button, .cta {{
      width: 100%;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 48px;
      padding: 12px 16px;
      border-radius: 12px;
      border: 1px solid var(--accent);
      background: linear-gradient(180deg, #00ff88 0%, #00d874 100%);
      color: #0a0c0b;
      text-decoration: none;
      font-family: "JetBrains Mono", monospace;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
    }}
    .ghost {{
      width: 100%;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 48px;
      padding: 12px 16px;
      border-radius: 12px;
      border: 1px solid var(--line-soft);
      background: transparent;
      color: var(--muted);
      text-decoration: none;
      font-family: "JetBrains Mono", monospace;
      font-size: 14px;
      font-weight: 700;
    }}
    .note {{
      color: var(--muted-soft);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.5;
    }}
    .result {{
      min-height: 18px;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 13px;
      line-height: 1.5;
    }}
    .result.ok {{ color: var(--accent); }}
    .result.err {{ color: var(--danger); }}
    @media (max-width: 760px) {{
      .wrap {{ width: calc(100% - 20px); }}
      .card {{ padding: 16px; border-radius: 16px; }}
      .grid {{ grid-template-columns: 1fr; }}
      .status-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <span>POLYMARKET PULSE // SIGNER</span>
      <span>{kicker}</span>
    </div>
    <article class="card">
      <p class="kicker">{kicker}</p>
      <h1>{title}</h1>
      <p class="intro">{intro}</p>
      <div class="grid">
        <div class="stack">
          <section class="panel">
            <p class="label">Session</p>
            <div class="status-grid">
              <div class="status-pill">
                <span class="label">wallet</span>
                <strong>{wallet}</strong>
              </div>
              <div class="status-pill">
                <span class="label">session status</span>
                <strong id="status-value">{status}</strong>
              </div>
              <div class="status-pill">
                <span class="label">wallet status</span>
                <strong>{wallet_status}</strong>
              </div>
              <div class="status-pill">
                <span class="label">signer kind</span>
                <strong>{signer_kind}</strong>
              </div>
              <div class="status-pill">
                <span class="label">expires_at</span>
                <strong>{expires_at}</strong>
              </div>
              <div class="status-pill">
                <span class="label">verified_at</span>
                <strong id="verified-value">{verified_at}</strong>
              </div>
            </div>
          </section>
          <section class="panel">
            <p class="label">{challenge_label}</p>
            <pre>{challenge}</pre>
          </section>
        </div>
        <div class="stack">
          <section class="panel">
            <p class="label">{payload_label}</p>
            <textarea id="signed-payload" placeholder="{html.escape(payload_placeholder)}" {disabled_attr}></textarea>
            <div style="height:10px"></div>
            <button id="submit-btn" {disabled_attr}>{submit_label}</button>
            <p class="note">{status_note}</p>
            <p id="result" class="result">{html.escape(disabled_copy if expired else "")}</p>
          </section>
          <section class="panel">
            <a class="cta" href="https://t.me/PolymarketPulse_trader_bot">{open_bot}</a>
            <div style="height:10px"></div>
            <a class="ghost" href="{base}/trader-bot">{open_trader_page}</a>
            <p class="note">{html.escape(success_wait)}</p>
          </section>
        </div>
      </div>
    </article>
  </div>
  <script>
    const token = {json.dumps(session.get("session_token") or "")};
    const lang = {json.dumps(lang)};
    const resultEl = document.getElementById("result");
    const statusEl = document.getElementById("status-value");
    const verifiedEl = document.getElementById("verified-value");
    const submitBtn = document.getElementById("submit-btn");
    const textarea = document.getElementById("signed-payload");

    async function submitPayload() {{
      const signedPayload = textarea.value.trim();
      if (!signedPayload) {{
        resultEl.className = "result err";
        resultEl.textContent = lang === "en"
          ? "Paste the signed payload first."
          : "Сначала вставьте signed payload.";
        return;
      }}
      submitBtn.disabled = true;
      resultEl.className = "result";
      resultEl.textContent = lang === "en" ? "Saving..." : "Сохраняю...";
      try {{
        const res = await fetch("/api/trader-signer/submit", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ token, signed_payload: signedPayload }})
        }});
        const data = await res.json();
        if (!res.ok) {{
          throw new Error(data.detail || "request_failed");
        }}
        statusEl.textContent = data.status || "signed";
        verifiedEl.textContent = data.verified_at || "n/a";
        resultEl.className = "result ok";
        resultEl.textContent = lang === "en"
          ? "Payload stored. Session is now signed."
          : "Payload сохранён. Сессия теперь в статусе signed.";
      }} catch (err) {{
        resultEl.className = "result err";
        resultEl.textContent = (lang === "en"
          ? "Could not save signer payload: "
          : "Не удалось сохранить signer payload: ") + err.message;
      }} finally {{
        submitBtn.disabled = false;
      }}
    }}

    submitBtn?.addEventListener("click", submitPayload);
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
    path_override: str | None = None,
) -> None:
    if not PG_CONN:
        return
    event_path = (path_override or "").strip()[:512] or resolve_site_event_path(request, details)
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
                        event_path,
                        request.headers.get("user-agent"),
                        request.client.host if request.client else None,
                        Jsonb(details or {}),
                    ),
                )
            conn.commit()
    except Exception:
        # analytics must never break user-facing flow
        return


def resolve_site_event_path(request: Request, details: dict | None = None) -> str:
    payload = details or {}

    raw_page_path = str(payload.get("page_path") or "").strip()
    if raw_page_path:
        return raw_page_path[:512]

    raw_page_url = str(payload.get("page_url") or "").strip()
    if raw_page_url:
        try:
            parsed = urlparse(raw_page_url)
            candidate = parsed.path or request.url.path
            if parsed.query:
                candidate = f"{candidate}?{parsed.query}"
            return candidate[:512]
        except Exception:
            pass

    referer = (request.headers.get("referer") or "").strip()
    if referer:
        try:
            parsed = urlparse(referer)
            candidate = parsed.path or request.url.path
            if parsed.query:
                candidate = f"{candidate}?{parsed.query}"
            return candidate[:512]
        except Exception:
            pass

    return request.url.path[:512]


def render_email_shell(*, title: str, body_html: str, cta_label: str, cta_url: str, footer_html: str = "") -> str:
    return f"""
    <div style="margin:0;padding:24px;background:#0d0f0e;color:#e8ede9;font-family:'JetBrains Mono','SFMono-Regular',Consolas,monospace;">
      <div style="max-width:640px;margin:0 auto;background:#131714;border:1px solid #1e2520;border-radius:16px;padding:28px;">
        <div style="color:#6b7a6e;font-size:12px;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:14px;">Polymarket Pulse // email backup</div>
        <h1 style="margin:0 0 16px;font-size:28px;line-height:1.05;color:#e8ede9;">{title}</h1>
        <div style="font-size:14px;line-height:1.65;color:#8fa88f;">{body_html}</div>
        <p style="margin:24px 0 0;">
          <a href="{cta_url}" style="display:inline-block;background:#00ff88;color:#0a0c0b;text-decoration:none;font-weight:700;border-radius:12px;padding:13px 18px;">{cta_label}</a>
        </p>
        {footer_html}
      </div>
    </div>
    """


def render_status_page(*, title: str, body_html: str, primary_label: str, primary_url: str, secondary_html: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="robots" content="noindex,follow" />
  <title>{title}</title>
  <style>
    :root {{
      --bg: #0d0f0e;
      --panel: #131714;
      --line: #1e2520;
      --text: #e8ede9;
      --muted: #8fa88f;
      --muted-soft: #6b7a6e;
      --accent: #00ff88;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 24px;
      background:
        radial-gradient(1200px 800px at 85% -20%, rgba(0, 255, 136, 0.08) 0%, transparent 60%),
        linear-gradient(180deg, #0a0c0b 0%, var(--bg) 100%);
      color: var(--text);
      font-family: "Space Grotesk", "Segoe UI", sans-serif;
    }}
    .card {{
      width: min(640px, 100%);
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 28px;
      box-shadow: 0 24px 72px rgba(0,0,0,0.38);
    }}
    .kicker {{
      margin: 0 0 12px;
      color: var(--muted-soft);
      font: 12px/1.4 "JetBrains Mono", monospace;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 0 0 14px;
      font-size: clamp(28px, 5vw, 42px);
      line-height: 0.98;
      text-transform: uppercase;
    }}
    .body {{
      color: var(--muted);
      font: 15px/1.65 "JetBrains Mono", monospace;
    }}
    .cta {{
      display: inline-block;
      margin-top: 22px;
      padding: 14px 18px;
      border-radius: 12px;
      background: var(--accent);
      color: #0a0c0b;
      text-decoration: none;
      font-weight: 700;
    }}
    .secondary {{
      margin-top: 16px;
      color: var(--muted-soft);
      font: 13px/1.6 "JetBrains Mono", monospace;
    }}
    .secondary a {{ color: var(--text); }}
  </style>
</head>
<body>
  <div class="card">
    <p class="kicker">Polymarket Pulse // email backup</p>
    <h1>{title}</h1>
    <div class="body">{body_html}</div>
    <a class="cta" href="{primary_url}">{primary_label}</a>
    <div class="secondary">{secondary_html}</div>
  </div>
</body>
</html>"""


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


def stripe_enabled() -> bool:
    return bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID_MONTHLY)


def stripe_api_call(path: str, data: dict[str, str | int | None]) -> dict:
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured")
    payload = {k: v for k, v in data.items() if v is not None}
    resp = requests.post(
        f"https://api.stripe.com{path}",
        auth=(STRIPE_SECRET_KEY, ""),
        data=payload,
        timeout=20,
    )
    if resp.status_code >= 300:
        raise HTTPException(status_code=502, detail=f"Stripe API error: {resp.text[:200]}")
    return resp.json()


def stripe_get(path: str, params: dict[str, str] | None = None) -> dict:
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured")
    resp = requests.get(
        f"https://api.stripe.com{path}",
        auth=(STRIPE_SECRET_KEY, ""),
        params=params or {},
        timeout=20,
    )
    if resp.status_code >= 300:
        raise HTTPException(status_code=502, detail=f"Stripe API error: {resp.text[:200]}")
    return resp.json()


def verify_stripe_signature(payload: bytes, signature_header: str) -> bool:
    if not STRIPE_WEBHOOK_SECRET:
        return False
    if not signature_header:
        return False
    fields = {}
    for part in signature_header.split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            fields.setdefault(k.strip(), []).append(v.strip())
    ts = (fields.get("t") or [None])[0]
    sigs = fields.get("v1") or []
    if not ts or not sigs:
        return False
    signed_payload = f"{ts}.{payload.decode('utf-8')}".encode("utf-8")
    expected = hmac.new(STRIPE_WEBHOOK_SECRET.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, s) for s in sigs)


def ensure_payment_schema(cur) -> None:
    cur.execute(SQL_ENSURE_PAYMENT_EVENTS)


def ensure_trade_alpha_schema(cur) -> None:
    cur.execute(SQL_ENSURE_TRADE_ALPHA_WAITLIST)


def resolve_user_id_for_email(cur, email: str, preferred_user_id: str | None = None) -> str:
    clean_email = email.strip().lower()
    if preferred_user_id:
        cur.execute("select id from app.users where id = %s::uuid", (preferred_user_id,))
        row = cur.fetchone()
        if row:
            user_id = str(row[0])
            cur.execute(
                """
                insert into app.identities (user_id, provider, provider_user_id)
                values (%s::uuid, 'email', %s)
                on conflict (provider, provider_user_id) do update
                set user_id = excluded.user_id
                """,
                (user_id, clean_email),
            )
            cur.execute(
                """
                insert into app.email_subscribers (email, user_id, source)
                values (%s, %s::uuid, 'site')
                on conflict (email) do update
                set user_id = coalesce(app.email_subscribers.user_id, excluded.user_id),
                    updated_at = now()
                """,
                (clean_email, user_id),
            )
            return user_id

    cur.execute("select user_id from app.email_subscribers where email = %s", (clean_email,))
    row = cur.fetchone()
    if row and row[0]:
        return str(row[0])

    cur.execute(
        "select user_id from app.identities where provider = 'email' and provider_user_id = %s limit 1",
        (clean_email,),
    )
    row = cur.fetchone()
    if row and row[0]:
        user_id = str(row[0])
    else:
        cur.execute(
            """
            insert into app.users (legacy_user_key)
            values (%s)
            on conflict (legacy_user_key) do update
            set updated_at = now()
            returning id
            """,
            (f"email:{clean_email}",),
        )
        user_id = str(cur.fetchone()[0])
        cur.execute(
            """
            insert into app.identities (user_id, provider, provider_user_id)
            values (%s::uuid, 'email', %s)
            on conflict (provider, provider_user_id) do update
            set user_id = excluded.user_id
            """,
            (user_id, clean_email),
        )

    cur.execute(
        """
        insert into app.email_subscribers (email, user_id, source)
        values (%s, %s::uuid, 'site')
        on conflict (email) do update
        set user_id = coalesce(app.email_subscribers.user_id, excluded.user_id),
            updated_at = now()
        """,
        (clean_email, user_id),
    )
    return user_id


def activate_pro_from_payment(
    *,
    provider: str,
    external_id: str,
    event_type: str,
    email: str,
    preferred_user_id: str | None,
    amount_cents: int | None,
    currency: str | None,
    source: str,
    payload: dict,
) -> tuple[bool, str]:
    if not PG_CONN:
        raise HTTPException(status_code=500, detail="PG_CONN is not configured")
    with psycopg.connect(PG_CONN, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '10000ms'")
            ensure_payment_schema(cur)
            cur.execute(SQL_PAYMENT_EVENT_EXISTS, (provider, external_id))
            if cur.fetchone():
                conn.commit()
                return False, "already_processed"

            user_id = resolve_user_id_for_email(cur, email, preferred_user_id=preferred_user_id)
            cur.execute(
                SQL_PAYMENT_EVENT_INSERT,
                (
                    provider,
                    external_id,
                    event_type,
                    "succeeded",
                    user_id,
                    email.strip().lower(),
                    amount_cents,
                    currency,
                    Jsonb(payload),
                ),
            )
            cur.execute(SQL_SUBSCRIPTION_INSERT_PRO, (user_id, source, PRO_SUBSCRIPTION_DAYS))
            cur.execute(SQL_PROFILE_SET_PRO, (user_id,))
        conn.commit()
    return True, user_id


def upsert_trade_alpha_waitlist(data: TraderAlphaRequest) -> int:
    if not PG_CONN:
        raise HTTPException(status_code=500, detail="PG_CONN is not configured")

    clean_email = data.email.strip().lower()
    with psycopg.connect(PG_CONN, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '8000ms'")
            ensure_trade_alpha_schema(cur)
            cur.execute(
                SQL_TRADE_ALPHA_WAITLIST_UPSERT,
                (
                    clean_email,
                    data.user_id,
                    data.telegram_id,
                    data.chat_id,
                    data.source,
                    Jsonb(data.details or {}),
                ),
            )
            row_id = int(cur.fetchone()[0])
        conn.commit()
    return row_id


def _to_iso(v: datetime | None) -> str | None:
    if v is None:
        return None
    try:
        return v.astimezone(timezone.utc).isoformat()
    except Exception:
        return str(v)


def _compact_series(values: list[float], max_points: int) -> list[float]:
    if len(values) <= max_points:
        return values
    if max_points <= 1:
        return [values[-1]]
    step = (len(values) - 1) / (max_points - 1)
    return [values[round(i * step)] for i in range(max_points)]


def _safe_market_token(value: str | None, *, max_len: int = 24) -> str:
    return "".join(ch for ch in str(value or "") if ch.isalnum() or ch in {"_", "-"})[:max_len]


def _polymarket_market_url(slug: str | None) -> str | None:
    clean_slug = (slug or "").strip().strip("/")
    if not clean_slug:
        return None
    return f"https://polymarket.com/market/{quote(clean_slug, safe='-_~')}"


def _pulse_track_market_url(market_id: str | None) -> str:
    token = _safe_market_token(market_id)
    payload = f"site_track_{token}" if token else "site_track"
    return f"https://t.me/polymarket_pulse_bot?start={payload}"


def _fmt_live_pct(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "n/a"


def _fmt_live_pp(value: object, *, signed: bool = True) -> str:
    try:
        num = float(value) * 100
        prefix = "+" if signed and num >= 0 else ""
        return f"{prefix}{num:.1f}pp"
    except (TypeError, ValueError):
        return "n/a"


def _fmt_live_liquidity(value: object) -> str | None:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if num <= 0:
        return None
    if num >= 1_000_000:
        return f"${num / 1_000_000:.1f}m liq"
    if num >= 1_000:
        return f"${round(num / 1_000)}k liq"
    return f"${round(num)} liq"


def _fmt_live_age(value: object) -> str | None:
    try:
        seconds = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    if seconds < 60:
        return f"{seconds}s quote"
    return f"{seconds // 60}m quote"


def _watchlist_category(question: str | None) -> str:
    text = (question or "").lower()
    if any(token in text for token in ("trump", "biden", "election", "senate", "house", "president", "iran", "putin", "zelensky", "congress", "war", "ceasefire", "nato", "israel", "ukraine", "rfk")):
        return "politics"
    if any(token in text for token in ("fed", "inflation", "recession", "gdp", "cpi", "interest rate", "oil", "yield", "tariff", "unemployment", "jobs report", "treasury")):
        return "macro"
    if any(token in text for token in ("bitcoin", "ethereum", "solana", "xrp", "bnb", "dogecoin", "crypto", "fdv", "btc", "eth", "memecoin")):
        return "crypto"
    return "other"


def _clean_watchlist_market_ids(market_ids: list[str]) -> list[str]:
    clean_ids: list[str] = []
    seen: set[str] = set()
    for market_id in market_ids:
        token = _safe_market_token(market_id, max_len=48)
        if token and token not in seen:
            seen.add(token)
            clean_ids.append(token)
    return clean_ids


def _workspace_rows_from_query(query: str, params: tuple) -> list[dict]:
    if not PG_CONN:
        return []
    with psycopg.connect(PG_CONN, connect_timeout=5, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '8000ms'")
            cur.execute(query, params)
            return cur.fetchall()


def _workspace_spark_map(row_map: dict[str, dict]) -> dict[str, list[float]]:
    market_ids = [market_id for market_id in row_map if market_id]
    if not PG_CONN or not market_ids:
        return {}
    with psycopg.connect(PG_CONN, connect_timeout=5) as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("set statement_timeout = '8000ms'")
            cur.execute(SQL_LIVE_SPARKLINE_POINTS, (market_ids, max(2, WATCHLIST_WORKSPACE_SPARK_SNAPSHOTS)))
            points = cur.fetchall()

    series_by_market: dict[str, list[float]] = defaultdict(list)
    for row in points:
        market_id = str(row.get("market_id") or "")
        mid = row.get("mid")
        if market_id and mid is not None:
            series_by_market[market_id].append(float(mid))

    out: dict[str, list[float]] = {}
    for market_id, payload in row_map.items():
        spark_source = list(series_by_market.get(market_id, []))
        now_mid = payload.get("yes_mid_now")
        if now_mid is not None:
            now_mid_f = float(now_mid)
            if not spark_source or abs(float(spark_source[-1]) - now_mid_f) > 1e-9:
                spark_source.append(now_mid_f)
        spark = _compact_series(spark_source, max_points=max(4, WATCHLIST_WORKSPACE_SPARK_POINTS))
        if len(spark) < 2 or len({round(v, 6) for v in spark}) < 2:
            spark = []
        out[market_id] = spark
    return out


def fetch_watchlist_workspace(market_ids: list[str]) -> list[dict]:
    clean_ids = _clean_watchlist_market_ids(market_ids)
    if not clean_ids:
        return []

    rows = _workspace_rows_from_query(
        SQL_WATCHLIST_WORKSPACE,
        (
            clean_ids,
            HOT_PREVIEW_MAX_FRESHNESS_SECONDS,
            HOT_PREVIEW_MAX_SPREAD,
            HOT_PREVIEW_MIN_LIQUIDITY,
            HOT_PREVIEW_MAX_FRESHNESS_SECONDS,
            HOT_PREVIEW_MAX_SPREAD,
            HOT_PREVIEW_MIN_LIQUIDITY,
        ),
    )
    return _hydrate_watchlist_workspace_rows(rows, ordered_market_ids=clean_ids)


def fetch_watchlist_workspace_for_user(user_id: str) -> list[dict]:
    safe_user_id = str(user_id or "").strip()
    if not safe_user_id:
        return []

    rows = _workspace_rows_from_query(
        SQL_WATCHLIST_WORKSPACE_USER,
        (
            safe_user_id,
            safe_user_id,
            HOT_PREVIEW_MAX_FRESHNESS_SECONDS,
            HOT_PREVIEW_MAX_SPREAD,
            HOT_PREVIEW_MIN_LIQUIDITY,
            HOT_PREVIEW_MAX_FRESHNESS_SECONDS,
            HOT_PREVIEW_MAX_SPREAD,
            HOT_PREVIEW_MIN_LIQUIDITY,
            safe_user_id,
            safe_user_id,
        ),
    )
    ordered_market_ids = [str(row.get("market_id") or "") for row in rows if row.get("market_id")]
    return _hydrate_watchlist_workspace_rows(rows, ordered_market_ids=ordered_market_ids)


def _hydrate_watchlist_workspace_rows(rows: list[dict], *, ordered_market_ids: list[str]) -> list[dict]:
    row_map: dict[str, dict] = {}
    for row in rows:
        market_id = str(row.get("market_id") or "")
        if not market_id:
            continue
        question = str(row.get("question") or market_id)
        raw_threshold = _float_or_none(row.get("alert_threshold_value"))
        effective_threshold = _float_or_none(row.get("effective_threshold_value"))
        alert_enabled = bool(row.get("alert_enabled"))
        alert_paused = bool(row.get("alert_paused"))
        alert_state = "paused" if alert_enabled and alert_paused else "on" if alert_enabled else "off"
        payload = {
            "market_id": market_id,
            "question": question,
            "slug": row.get("slug") or "",
            "market_url": _polymarket_market_url(row.get("slug")),
            "track_url": _pulse_track_market_url(market_id),
            "market_status": str(row.get("market_status") or "unknown"),
            "status": str(row.get("row_state") or "saved"),
            "signal_quality": str(row.get("signal_quality") or "legacy_fallback"),
            "category": _watchlist_category(question),
            "quote_ts": _to_iso(row.get("quote_ts")),
            "yes_mid_now": _float_or_none(row.get("yes_mid_now")),
            "yes_mid_prev_5m": _float_or_none(row.get("yes_mid_prev_5m")),
            "delta_primary": _float_or_none(row.get("delta_primary")),
            "delta_1m": _float_or_none(row.get("delta_1m")),
            "delta_5m": _float_or_none(row.get("delta_5m")),
            "liquidity": _float_or_none(row.get("liquidity")),
            "spread": _float_or_none(row.get("spread")),
            "freshness_seconds": _float_or_none(row.get("freshness_seconds")),
            "has_two_sided_quote": bool(row.get("has_two_sided_quote")),
            "saved_at": _to_iso(row.get("saved_at")),
            "alert_enabled": alert_enabled,
            "alert_paused": alert_paused,
            "alert_state": alert_state,
            "alert_threshold_value": raw_threshold,
            "effective_threshold_value": effective_threshold,
            "last_alert_at": _to_iso(row.get("last_alert_at")),
        }
        row_map[market_id] = payload

    spark_map = _workspace_spark_map(row_map)
    for market_id, payload in row_map.items():
        payload["spark"] = spark_map.get(market_id, [])

    out: list[dict] = []
    for market_id in ordered_market_ids:
        payload = row_map.get(market_id)
        if payload:
            out.append(payload)
        else:
            out.append(
                {
                    "market_id": market_id,
                    "question": market_id,
                    "slug": "",
                    "market_url": None,
                    "track_url": _pulse_track_market_url(market_id),
                    "market_status": "unknown",
                    "status": "no_quotes",
                    "signal_quality": "no_quotes",
                    "category": "other",
                    "quote_ts": None,
                    "yes_mid_now": None,
                    "yes_mid_prev_5m": None,
                    "delta_primary": None,
                    "delta_1m": None,
                    "delta_5m": None,
                    "liquidity": None,
                    "spread": None,
                    "freshness_seconds": None,
                    "has_two_sided_quote": False,
                    "saved_at": None,
                    "alert_enabled": False,
                    "alert_paused": False,
                    "alert_state": "off",
                    "alert_threshold_value": None,
                    "effective_threshold_value": None,
                    "last_alert_at": None,
                    "spark": [],
                }
            )
    return out


def save_site_watchlist_market(
    *,
    user_id: str,
    market_id: str,
    source: str,
    default_alert_enabled: bool = False,
) -> None:
    saved = save_site_watchlist_markets(
        user_id=user_id,
        market_ids=[market_id],
        source=source,
        default_alert_enabled=default_alert_enabled,
    )
    if not saved:
        raise HTTPException(status_code=400, detail="invalid_market_id")


def save_site_watchlist_markets(
    *,
    user_id: str,
    market_ids: list[str],
    source: str,
    default_alert_enabled: bool = False,
) -> list[str]:
    safe_market_ids: list[str] = []
    seen: set[str] = set()
    for market_id in market_ids:
        safe_market_id = _safe_market_token(market_id, max_len=48)
        if not safe_market_id or safe_market_id in seen:
            continue
        safe_market_ids.append(safe_market_id)
        seen.add(safe_market_id)
    if not safe_market_ids:
        return []
    if not PG_CONN:
        raise HTTPException(status_code=500, detail="PG_CONN is not configured")
    with psycopg.connect(PG_CONN, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '6000ms'")
            for safe_market_id in safe_market_ids:
                cur.execute(SQL_SITE_WATCHLIST_ADD, (user_id, safe_market_id))
                cur.execute(
                    SQL_SITE_ALERT_SETTINGS_UPSERT,
                    (
                        user_id,
                        safe_market_id,
                        default_alert_enabled,
                        False,
                        None,
                        source,
                    ),
                )
        conn.commit()
    return safe_market_ids


def remove_site_watchlist_market(*, user_id: str, market_id: str) -> int:
    safe_market_id = _safe_market_token(market_id, max_len=48)
    if not safe_market_id or not PG_CONN:
        return 0
    with psycopg.connect(PG_CONN, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '6000ms'")
            cur.execute(SQL_SITE_WATCHLIST_REMOVE, (user_id, safe_market_id))
            removed = int(cur.rowcount or 0)
        conn.commit()
    return removed


def _render_watchlist_workspace_block(lang: Literal["ru", "en"]) -> str:
    title = "Watchlist workspace" if lang == "en" else "Watchlist workspace"
    subtitle = (
        "Your actual saved-market workspace lives here: sort by delta, liquidity, spread, freshness, and bell state. Telegram only finishes identity and alert delivery."
        if lang == "en"
        else "Именно здесь живёт ваш реальный workspace сохранённых рынков: сортировки по delta, liquidity, spread, freshness и bell state. Telegram нужен только для identity и доставки алертов."
    )
    login_copy = (
        "Log in with Telegram to persist this watchlist across devices."
        if lang == "en"
        else "Войдите через Telegram, чтобы закрепить этот watchlist между устройствами."
    )
    login_cta = "Open Telegram Bot" if lang == "en" else "Открыть Telegram-бота"
    return f"""
    <section class="watchlist-workspace reveal delay-3">
      <div class="watchlist-workspace-head">
        <div>
          <p class="links-title">{title}</p>
          <p class="watchlist-workspace-copy">{subtitle}</p>
        </div>
        <div class="watchlist-login-inline">
          <p class="watchlist-login-copy" data-watchlist-session-copy="logged-out">{login_copy}</p>
          <a class="site-cta" href="{PULSE_BOT_URL}" target="_blank" rel="noopener noreferrer" data-watchlist-auth="login" data-watchlist-return="/watchlist">{login_cta}</a>
        </div>
      </div>
      <div id="watchlist-workspace-root" data-watchlist-workspace="true" data-watchlist-lang="{lang}"></div>
    </section>
"""


def _render_signal_quality_block(slug: str, lang: Literal["ru", "en"]) -> str:
    if slug not in {"signals", "telegram-bot", "top-movers", "analytics"}:
        return ""

    limit = 4
    if slug == "top-movers":
        limit = 5
    elif slug == "analytics":
        limit = 6

    try:
        rows = fetch_live_movers_preview(limit=limit, spark_snapshots=12, max_points=12, min_distinct_points=2)
    except Exception:
        logger.exception("live signal block render failed")
        rows = []

    if not rows:
        empty_title = "Live board is quiet right now" if lang == "en" else "Live board сейчас тихий"
        empty_copy = (
            "No mover cleared the current quality gates, or the API is catching up. Retry in a minute or open Telegram for thresholded alerts."
            if lang == "en"
            else "Сейчас ни один mover не прошёл quality gates, либо API догоняет поток. Повторите через минуту или откройте Telegram для threshold-алертов."
        )
        return f"""
    <section id="live-signal-surface" class="live-signal-board reveal delay-3">
      <div class="live-signal-head">
        <p class="links-title">Live signal board</p>
      </div>
      <div class="live-signal-empty">
        <strong>{html.escape(empty_title)}</strong>
        <p>{html.escape(empty_copy)}</p>
      </div>
    </section>
"""

    if slug == "telegram-bot":
        title = "Markets you can track right now" if lang == "en" else "Рынки, которые можно отслеживать сейчас"
        subtitle = (
            "Open one current mover in Telegram and turn it into a watchlist alert."
            if lang == "en"
            else "Откройте текущий mover в Telegram и превратите его в watchlist-алерт."
        )
    elif slug == "top-movers":
        title = "Top movers board" if lang == "en" else "Top movers board"
        subtitle = (
            "The strongest current repricing ranked with open, save, and bell actions directly on the row."
            if lang == "en"
            else "Самые сильные текущие движения с действиями прямо из строки."
        )
    elif slug == "analytics":
        title = "Live analytics tape" if lang == "en" else "Live analytics tape"
        subtitle = (
            "Current markets worth reading with movement quality and execution-ready context."
            if lang == "en"
            else "Текущие рынки с качеством движения и контекстом для действия."
        )
    else:
        title = "Live signal board" if lang == "en" else "Live-доска сигналов"
        subtitle = (
            "Current candidates with freshness, liquidity, spread, and threshold-aware context."
            if lang == "en"
            else "Текущие кандидаты со свежестью, ликвидностью и spread-контекстом."
        )
    track_label = "Track in Telegram" if lang == "en" else "Отслеживать в Telegram"
    open_label = "Open market" if lang == "en" else "Открыть рынок"
    save_label = "Add to watchlist" if lang == "en" else "Add to watchlist"
    bell_label = "🔔 Alerts" if lang == "en" else "🔔 Alerts"

    cards: list[str] = []
    for row in rows:
        question = html.escape(str(row.get("question") or "n/a"))
        market_id = html.escape(str(row.get("market_id") or ""))
        market_url = html.escape(str(row.get("market_url") or ""))
        track_url = html.escape(str(row.get("track_url") or ""))
        market_slug = html.escape(str(row.get("slug") or ""))
        source = str(row.get("source") or "")
        delta = float(row.get("delta_yes") or 0.0)
        delta_cls = "up" if delta >= 0 else "down"
        delta_1m = float(row.get("delta_1m") or 0.0)
        age = _fmt_live_age(row.get("freshness_seconds"))
        liq = _fmt_live_liquidity(row.get("liquidity"))
        spread = _fmt_live_pp(row.get("spread"), signed=False) if row.get("spread") is not None else None
        quality: list[tuple[str, str]] = [
            (
                "live gated" if source == "hot" else "historical fallback",
                "Current row passed the live quality gates." if source == "hot" else "Fallback data is shown while hot data catches up.",
            )
        ]
        if age:
            quality.append((age, "Quote freshness. Older quotes weaken urgency."))
        if liq:
            quality.append((liq, "Higher liquidity usually means cleaner execution."))
        if spread:
            quality.append((f"{spread} spread", "Lower spread is better. Wide spread can distort urgency."))
        quality_html = "".join(
            f'<span class="live-signal-pill{" strong" if idx == 0 else ""}" title="{html.escape(tooltip)}">{html.escape(label)}</span>'
            for idx, (label, tooltip) in enumerate(quality)
        )
        tape_html = (
            f'<span class="live-signal-tape" title="Fast 1 minute cue for urgency.">1m {_fmt_live_pp(delta_1m)}</span>'
            if abs(delta_1m) > 0
            else ""
        )
        actions = ""
        if market_url:
            actions += (
                f'<a class="live-signal-link" href="{market_url}" target="_blank" rel="noopener noreferrer" '
                f'title="Open this market on Polymarket." data-market-action="open_polymarket" data-market-id="{market_id}">{open_label}</a>'
            )
        if track_url:
            actions += (
                f'<a class="live-signal-link primary" href="{track_url}" target="_blank" rel="noopener noreferrer" '
                f'title="Open Telegram for the alert layer." data-market-action="track_telegram" data-market-id="{market_id}">{track_label}</a>'
            )
        actions += (
            f'<button type="button" class="live-signal-link watchlist-toggle" '
            f'title="Save this market to your website watchlist." '
            f'data-watchlist-action="toggle_save" '
            f'data-market-id="{market_id}" '
            f'data-market-question="{question}" '
            f'data-market-url="{market_url}" '
            f'data-track-url="{track_url}" '
            f'data-market-slug="{market_slug}" '
            f'data-market-source="{html.escape(source)}">{save_label}</button>'
        )
        actions += (
            f'<button type="button" class="live-signal-link" '
            f'title="Turn Telegram alerts on only when this market deserves interruption." '
            f'data-watchlist-action="toggle_alert" '
            f'data-market-id="{market_id}" '
            f'data-market-question="{question}" '
            f'data-market-url="{market_url}" '
            f'data-track-url="{track_url}" '
            f'data-market-slug="{market_slug}" '
            f'data-market-source="{html.escape(source)}">{bell_label}</button>'
        )
        cards.append(
            f"""
        <article class="live-signal-row">
          <div>
            <p class="live-signal-question">{question}</p>
            <p class="live-signal-meta">market {market_id} · {_fmt_live_pct(row.get("yes_mid_prev"))} → {_fmt_live_pct(row.get("yes_mid_now"))}</p>
            <div class="live-signal-quality">{quality_html}</div>
          </div>
          <div class="live-signal-side">
            <div>
              <span class="live-signal-delta {delta_cls}" title="Current move in percentage points.">{_fmt_live_pp(row.get("delta_yes"))}</span>
              {tape_html}
            </div>
            <div class="live-signal-actions">{actions}</div>
          </div>
        </article>
"""
        )

    return f"""
    <section id="live-signal-surface" class="live-signal-board reveal delay-3">
      <div class="live-signal-head">
        <p class="links-title">{title}</p>
        <p class="live-signal-subtitle">{subtitle}</p>
      </div>
      <div class="live-signal-list">
        {''.join(cards)}
      </div>
    </section>
"""


def _seo_page_stats(slug: str, lang: Literal["ru", "en"]) -> list[tuple[str, str, str]]:
    if lang != "en":
        return [
            ("Задержка сигнала", "< 12 сек", "движение рынка -> inbox бота"),
            ("Путь активации", "1 тап", "лендинг -> /start -> watchlist"),
            ("Live-охват", "200 рынков", "active-only сбалансированный universe"),
        ]

    page_stats: dict[str, list[tuple[str, str, str]]] = {
        "signals": [
            ("Threshold", "0.03 = 3pp", "Inbox fires only when abs(delta) clears your level."),
            ("Quiet state", "intentional", "Watchlist can move while Inbox stays empty by design."),
            ("Quality gates", "live filtered", "Freshness, liquidity, and spread help cut false urgency."),
        ],
        "top-movers": [
            ("Sort key", "|delta| first", "The strongest repricing rises fastest in the current live window."),
            ("Live tape", "1m + now", "Read the freshest move before it degrades into stale context."),
            ("Row actions", "save / bell / open", "Every mover row should be actionable, not just descriptive."),
        ],
        "analytics": [
            ("Category lens", "market grouped", "See whether politics, macro, or crypto is waking up first."),
            ("Research flow", "site → bell", "Research happens on the web before Telegram becomes relevant."),
            ("Live scope", "200 markets", "Balanced active-only universe without dashboard sprawl."),
        ],
        "telegram-bot": [
            ("First value", "< 60 sec", "/start → /movers → one market → one useful alert path."),
            ("Free plan", "3 / 20", "Three tracked markets and twenty alerts per day before upgrade."),
            ("Telegram role", "bell + inbox", "The bot is for activation and delivery, not endless browsing."),
        ],
        "watchlist-alerts": [
            ("Saved first", "watchlist != bell", "A market can stay saved even while alerts stay off."),
            ("Threshold", "your own", "Telegram pings only above the level you configured."),
            ("Delivery", "low-noise", "Quiet windows are product behavior, not a broken inbox."),
        ],
        "dashboard": [
            ("Tab count", "20 → 1", "Move from widget sprawl into one research and alert workflow."),
            ("Workspace split", "site + Telegram", "Watchlist lives on the web, bell behavior lives in Telegram."),
            ("Quiet state", "honest", "If nothing meaningful moved, Pulse stays quiet on purpose."),
        ],
        "watchlist": [
            ("Watchlist", "saved layer", "Saving a market does not automatically opt you into noise."),
            ("Bell", "optional", "Turn alerts on only for markets that deserve interruption."),
            ("Workflow", "site first", "Research and compare on the site before using Telegram."),
        ],
    }
    return page_stats.get(
        slug,
        [
            ("Signal delay", "< 12 sec", "market move -> bot inbox"),
            ("Activation path", "1 tap", "landing -> /start -> watchlist"),
            ("Live scope", "200 markets", "active-only balanced universe"),
        ],
    )


def _render_page_focus_block(slug: str, lang: Literal["ru", "en"]) -> str:
    if lang != "en":
        return ""

    if slug == "signals":
        title = "Signal filters"
        cards = [
            ("Threshold first", "A signal is not every move. It is a move large enough to clear the threshold you set."),
            ("Quality matters", "Fresh quotes, better liquidity, and tighter spread make a move more worth trusting."),
            ("Quiet is useful", "If the market is flat or below threshold, an empty Inbox is the correct product outcome."),
        ]
    elif slug == "top-movers":
        title = "Top movers workflow"
        cards = [
            ("Rank by current repricing", "This page is for finding the strongest live move first, not reading a generic market list."),
            ("Decide from the row", "Open the market, save it to watchlist, or turn the bell on without leaving the movers surface."),
            ("Use speed as a filter", "If the 1m tape is flat or stale, the row should lose urgency even if the longer move still looks large."),
        ]
    elif slug == "analytics":
        title = "Category view"
        try:
            rows = fetch_live_movers_preview(limit=8, spark_snapshots=8, max_points=8, min_distinct_points=1)
        except Exception:
            logger.exception("analytics focus block render failed")
            rows = []
        grouped: dict[str, dict[str, float | int]] = defaultdict(lambda: {"count": 0, "max_abs": 0.0})
        for row in rows:
            tag = _watchlist_category(str(row.get("question") or ""))
            grouped[tag]["count"] = int(grouped[tag]["count"]) + 1
            grouped[tag]["max_abs"] = max(float(grouped[tag]["max_abs"]), abs(float(row.get("delta_yes") or 0.0)))
        cards = []
        for tag, label in (("politics", "Politics"), ("macro", "Macro"), ("crypto", "Crypto")):
            entry = grouped.get(tag) or {"count": 0, "max_abs": 0.0}
            cards.append(
                (
                    label,
                    f"{int(entry['count'])} active mover(s) in the current sample · strongest shift {_fmt_live_pp(entry['max_abs']) if float(entry['max_abs']) else 'quiet'}."
                )
            )
        if not rows:
            cards = [
                ("Politics", "Follow narrative repricing without opening a dashboard full of election tabs."),
                ("Macro", "See rate, recession, and policy repricing in one place."),
                ("Crypto", "Surface the fastest token and headline-driven shifts without scanning the whole board."),
            ]
    elif slug == "watchlist-alerts":
        title = "Watchlist -> bell -> alert"
        cards = [
            ("1. Save on the site", "A watchlist market stays saved even when you are not ready for alerts yet."),
            ("2. Bell is separate", "Turning on alerts is a second decision, not something hidden inside the save action."),
            ("3. Configure in Telegram", "Sensitivity lives in Telegram because the bell and Inbox do too."),
            ("4. Quiet is still a state", "The market may move while the Inbox stays empty if it remains below threshold."),
            ("5. Return with context", "The alert should bring you back to the market, not back into dashboard wandering."),
        ]
        return (
            f"""
    <section class="command-flow reveal delay-3">
      <div class="command-flow-head">
        <p class="links-title">{title}</p>
        <p class="command-flow-subtitle">Watchlist and alerts are intentionally separate product objects now.</p>
      </div>
      <div class="command-grid">
        {''.join(f'<article class="command-card{" strong" if idx == 2 else ""}"><p class="command-name">STEP {idx + 1}</p><h3 class="command-title">{html.escape(card_title)}</h3><p class="command-copy">{html.escape(card_copy)}</p></article>' for idx, (card_title, card_copy) in enumerate(cards))}
      </div>
    </section>
"""
        )
    elif slug == "dashboard":
        title = "Why this is not another dashboard"
        cards = [
            ("Dashboard habit", "A normal dashboard asks you to keep browsing until you find a move worth caring about."),
            ("Pulse site", "Pulse should show what moved, let you save it, and explain whether it still looks actionable."),
            ("Telegram bell", "Telegram only enters when the move deserves interruption, not as the whole product surface."),
        ]
    else:
        return ""

    return (
        f"""
    <section class="preview reveal delay-3">
      <p class="links-title">{title}</p>
      <div class="preview-grid">
        {''.join(f'<article class="preview-card"><p class="preview-kicker">{idx + 1:02d}</p><h3 class="preview-title">{html.escape(card_title)}</h3><p class="preview-copy">{html.escape(card_copy)}</p></article>' for idx, (card_title, card_copy) in enumerate(cards))}
      </div>
    </section>
"""
    )


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_live_movers_preview(
    limit: int = 3,
    spark_snapshots: int = 16,
    max_points: int = 16,
    min_distinct_points: int = 6,
) -> list[dict]:
    if not PG_CONN:
        return []

    with psycopg.connect(PG_CONN, connect_timeout=5) as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("set statement_timeout = '8000ms'")
            candidate_limit = min(36, max(limit, limit * 12))
            cur.execute(
                SQL_HOT_LIVE_MOVERS_PREVIEW,
                (
                    HOT_PREVIEW_MAX_FRESHNESS_SECONDS,
                    HOT_PREVIEW_MIN_LIQUIDITY,
                    HOT_PREVIEW_MAX_SPREAD,
                    candidate_limit,
                ),
            )
            movers = cur.fetchall()
            source = "hot"
            if not movers:
                cur.execute(SQL_LIVE_MOVERS_PREVIEW_LEGACY, (candidate_limit,))
                movers = cur.fetchall()
                source = "legacy"
            if not movers:
                return []

            market_ids = [str(r["market_id"]) for r in movers if r.get("market_id")]
            cur.execute(SQL_LIVE_SPARKLINE_POINTS, (market_ids, max(2, int(spark_snapshots))))
            points = cur.fetchall()

    series_by_market: dict[str, list[float]] = defaultdict(list)
    for row in points:
        market_id = str(row.get("market_id") or "")
        mid = row.get("mid")
        if market_id and mid is not None:
            series_by_market[market_id].append(float(mid))

    rich_rows: list[dict] = []
    fallback_rows: list[dict] = []
    for row in movers:
        market_id = str(row.get("market_id") or "")
        spark_source = list(series_by_market.get(market_id, []))
        hot_now = row.get("yes_mid_now")
        if source == "hot" and hot_now is not None:
            hot_now_f = float(hot_now)
            if not spark_source or abs(float(spark_source[-1]) - hot_now_f) > 1e-9:
                spark_source.append(hot_now_f)
        spark = _compact_series(spark_source, max_points=max_points)
        if len(spark) < 2:
            spark = []
        distinct_points = len({round(v, 6) for v in spark})

        payload = {
            "market_id": market_id,
            "question": row.get("question") or "",
            "slug": row.get("slug") or "",
            "last_bucket": _to_iso(row.get("last_bucket")),
            "prev_bucket": _to_iso(row.get("prev_bucket")),
            "yes_mid_now": float(row.get("yes_mid_now") or 0.0),
            "yes_mid_prev": float(row.get("yes_mid_prev") or 0.0),
            "delta_yes": float(row.get("delta_yes") or 0.0),
            "delta_1m": float(row.get("delta_1m") or 0.0),
            "liquidity": _float_or_none(row.get("liquidity")),
            "spread": _float_or_none(row.get("spread")),
            "freshness_seconds": _float_or_none(row.get("freshness_seconds")),
            "source": row.get("source") or source,
            "signal_quality": row.get("signal_quality") or ("hot_quality_gated" if source == "hot" else "legacy_fallback"),
            "spark": spark,
            "market_url": _polymarket_market_url(row.get("slug")),
            "track_url": _pulse_track_market_url(market_id),
        }

        if distinct_points >= min_distinct_points:
            rich_rows.append(payload)
        else:
            fallback_rows.append(payload)

    out = (rich_rows + fallback_rows)[:limit]
    return out


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

    def sitemap_entry(path: str) -> str:
        resolved_path = path or "/"
        href = f"{u}{resolved_path}"
        return f"  <url><loc>{href}</loc></url>\n"

    content_urls = ["", *[f"/{slug}" for slug in SEO_PAGES], "/how-it-works", "/commands", "/trader-bot"]
    entries = "".join(sitemap_entry(path) for path in content_urls)
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}"
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
    lang = detect_site_lang(request)
    return HTMLResponse(load_page("index", lang))


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request) -> HTMLResponse:
    lang = detect_site_lang(request)
    return HTMLResponse(load_page("privacy", lang))


@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request) -> HTMLResponse:
    lang = detect_site_lang(request)
    return HTMLResponse(load_page("terms", lang))


@app.get("/how-it-works", response_class=HTMLResponse)
def how_it_works(request: Request) -> HTMLResponse:
    lang = detect_site_lang(request)
    return HTMLResponse(load_page("how-it-works", lang))


@app.get("/commands", response_class=HTMLResponse)
def commands_page(request: Request) -> HTMLResponse:
    lang = detect_site_lang(request)
    return HTMLResponse(load_page("commands", lang))


@app.get("/trader-bot", response_class=HTMLResponse)
def trader_bot_page(request: Request) -> HTMLResponse:
    lang = detect_site_lang(request)
    return HTMLResponse(load_page("trader-bot", lang))


@app.get("/trader-connect", response_class=HTMLResponse)
def trader_connect_page(request: Request, token: str) -> HTMLResponse:
    lang = detect_lang(request)
    session = fetch_signer_session(token)
    if not session:
        raise HTTPException(status_code=404, detail="signer_session_not_found")
    if session.get("status") == "new":
        touch_signer_session_open(int(session["id"]))
        session = fetch_signer_session(token) or session

    log_site_event(
        event_type="page_view",
        request=request,
        lang=lang,
        source="site",
        details={
            "placement": "trader_signer_page",
            "product": "trader",
            "session_status": session.get("status"),
        },
    )
    return HTMLResponse(render_trader_connect_page(session, lang))


@app.post("/api/events")
def site_event(data: SiteEventRequest, request: Request) -> JSONResponse:
    req_lang = detect_lang(request)
    merged_details = enrich_details(request, data.details, fallback_lang=req_lang)
    detail_lang = merged_details.get("lang")
    event_lang = detail_lang if detail_lang in {"ru", "en"} else req_lang
    resolved_event_path = resolve_site_event_path(request, merged_details)
    allowed = {
        "tg_click",
        "page_view",
        "live_board_impression",
        "waitlist_intent",
        "checkout_intent",
        "market_click",
        "watchlist_add",
        "watchlist_add_click",
        "watchlist_add_success",
        "watchlist_remove",
        "watchlist_alert_toggle",
        "bell_click",
        "telegram_login_click",
        "watchlist_auth_complete",
        "watchlist_prompt_open",
        "watchlist_sensitivity_change",
        "pricing_seen",
        "pricing_cta_click",
        "alert_click_back_to_site",
    }
    event_type = (data.event_type or "").strip().lower()
    if event_type not in allowed:
        raise HTTPException(status_code=400, detail="unsupported event_type")

    log_site_event(
        event_type=event_type,
        request=request,
        lang=event_lang,
        source=(data.source or "site").strip()[:64] or "site",
        details=merged_details,
        path_override=resolved_event_path,
    )
    return JSONResponse({"ok": True})


@app.post("/api/trader-alpha")
def trader_alpha(data: TraderAlphaRequest, request: Request) -> JSONResponse:
    req_lang = detect_lang(request)
    details = enrich_details(request, data.details, fallback_lang=req_lang, fallback_placement="trader_alpha_form")
    row_id = upsert_trade_alpha_waitlist(data)
    log_site_event(
        event_type="waitlist_submit",
        request=request,
        lang=req_lang,
        email=data.email,
        source=(data.source or "site").strip()[:64] or "site",
        details={**details, "product": "trader_alpha", "alpha_id": row_id},
    )
    return JSONResponse({"ok": True, "message": "alpha_waitlist_saved", "id": row_id})


@app.post("/api/trader-signer/submit")
def trader_signer_submit(data: TraderSignerSubmitRequest, request: Request) -> JSONResponse:
    req_lang = detect_lang(request)
    saved = save_signer_payload(data.token, data.signed_payload, request)
    log_site_event(
        event_type="page_view",
        request=request,
        lang=req_lang,
        source="site",
        details={
            "placement": "trader_signer_submit",
            "product": "trader",
            "status": saved["status"],
            "wallet": saved["wallet"],
        },
    )
    return JSONResponse({"ok": True, **saved})


@app.get("/api/live-movers-preview")
def live_movers_preview(limit: int = 3) -> JSONResponse:
    safe_limit = max(1, min(int(limit), 6))
    try:
        rows = fetch_live_movers_preview(limit=safe_limit, spark_snapshots=16, max_points=16)
    except Exception:
        rows = []
    return JSONResponse(
        {
            "ok": True,
            "rows": rows,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.get("/api/watchlist-workspace")
def watchlist_workspace(request: Request, market_ids: str = "") -> JSONResponse:
    session = current_site_session(request)
    raw_ids = [part.strip() for part in market_ids.split(",") if part.strip()]
    safe_ids = raw_ids[:40]
    try:
        if session and str(session.get("user_id") or "").strip():
            rows = fetch_watchlist_workspace_for_user(str(session["user_id"]))
        else:
            rows = fetch_watchlist_workspace(safe_ids)
    except Exception:
        rows = []
    return JSONResponse(
        {
            "ok": True,
            "rows": rows,
            "market_ids": safe_ids,
            "session": {
                "logged_in": bool(session),
                "user_id": str(session.get("user_id") or "") if session else None,
                "username": session.get("username") if session else None,
                "first_name": session.get("first_name") if session else None,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.get("/api/watchlist/session")
def watchlist_session(request: Request) -> JSONResponse:
    session = current_site_session(request)
    return JSONResponse(
        {
            "ok": True,
            "logged_in": bool(session),
            "user": (
                {
                    "user_id": str(session.get("user_id") or ""),
                    "telegram_id": session.get("telegram_id"),
                    "username": session.get("username"),
                    "first_name": session.get("first_name"),
                    "locale": session.get("locale"),
                }
                if session
                else None
            ),
        }
    )


@app.post("/api/watchlist/auth/start")
def watchlist_auth_start(data: WatchlistAuthStartRequest, request: Request) -> JSONResponse:
    locale = data.locale or ("ru" if "lang=ru" in str(request.url) else "en")
    return_path = _safe_return_path(data.return_path or request.headers.get("referer") or "/watchlist")
    market_id = _safe_market_token(data.market_id, max_len=48) or None
    payload = {
        "question": (data.question or "")[:280] or None,
        "source": data.source,
        "page_path": return_path,
    }
    token = create_web_auth_request(
        intent=data.intent,
        market_id=market_id,
        return_path=return_path,
        locale=locale,
        payload=payload,
    )
    telegram_url = build_site_telegram_url(intent=data.intent, market_id=market_id, token=token)
    log_site_event(
        event_type="watchlist_auth_start",
        request=request,
        lang=locale,
        source=data.source,
        details={"intent": data.intent, "market_id": market_id, "request_token": token[:8], "return_path": return_path},
        path_override=return_path,
    )
    return JSONResponse({"ok": True, "telegram_url": telegram_url, "request_token": token})


@app.post("/api/watchlist/save")
def watchlist_save(data: WatchlistSaveRequest, request: Request) -> JSONResponse:
    session = current_site_session(request)
    if not session or not session.get("user_id"):
        raise HTTPException(status_code=401, detail="telegram_login_required")
    safe_market_id = _safe_market_token(data.market_id, max_len=48)
    if not safe_market_id:
        raise HTTPException(status_code=400, detail="invalid_market_id")
    save_site_watchlist_market(
        user_id=str(session["user_id"]),
        market_id=safe_market_id,
        source="web",
        default_alert_enabled=False,
    )
    log_site_event(
        event_type="watchlist_save_site",
        request=request,
        lang=str(session.get("locale") or "en"),
        source=data.source,
        details={"market_id": safe_market_id, "question": data.question, "slug": data.slug},
        path_override=request.url.path,
    )
    return JSONResponse({"ok": True, "market_id": safe_market_id, "saved": True})


@app.post("/api/watchlist/sync")
def watchlist_sync(data: WatchlistSyncRequest, request: Request) -> JSONResponse:
    session = current_site_session(request)
    if not session or not session.get("user_id"):
        raise HTTPException(status_code=401, detail="telegram_login_required")
    raw_items = list(data.items or [])[:24]
    safe_market_ids = save_site_watchlist_markets(
        user_id=str(session["user_id"]),
        market_ids=[str(item.market_id or "") for item in raw_items],
        source="web",
        default_alert_enabled=False,
    )
    log_site_event(
        event_type="watchlist_sync_site",
        request=request,
        lang=str(session.get("locale") or "en"),
        source="site",
        details={
            "saved_count": len(safe_market_ids),
            "saved_market_ids": safe_market_ids[:12],
            "requested_count": len(raw_items),
        },
        path_override=request.url.path,
    )
    return JSONResponse(
        {
            "ok": True,
            "saved_market_ids": safe_market_ids,
            "saved_count": len(safe_market_ids),
        }
    )


@app.post("/api/watchlist/remove")
def watchlist_remove(data: WatchlistSaveRequest, request: Request) -> JSONResponse:
    session = current_site_session(request)
    if not session or not session.get("user_id"):
        raise HTTPException(status_code=401, detail="telegram_login_required")
    safe_market_id = _safe_market_token(data.market_id, max_len=48)
    if not safe_market_id:
        raise HTTPException(status_code=400, detail="invalid_market_id")
    removed = remove_site_watchlist_market(user_id=str(session["user_id"]), market_id=safe_market_id)
    log_site_event(
        event_type="watchlist_remove_site",
        request=request,
        lang=str(session.get("locale") or "en"),
        source=data.source,
        details={"market_id": safe_market_id, "removed": bool(removed)},
        path_override=request.url.path,
    )
    return JSONResponse({"ok": True, "market_id": safe_market_id, "removed": bool(removed)})


@app.get("/auth/telegram/complete")
def watchlist_auth_complete(token: str, request: Request) -> Response:
    if not PG_CONN:
        raise HTTPException(status_code=500, detail="PG_CONN is not configured")
    with psycopg.connect(PG_CONN, connect_timeout=5, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '6000ms'")
            cur.execute(SQL_WEB_AUTH_REQUEST_CLAIM, (token,))
            auth_request = cur.fetchone()
        conn.commit()
    if not auth_request:
        raise HTTPException(status_code=400, detail="auth_request_not_ready")
    auth_request_dict = dict(auth_request)
    user_id = str(auth_request_dict.get("user_id") or "").strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="auth_request_missing_user")
    session_token = create_site_session(user_id=user_id, request=request, auth_request=auth_request_dict)
    return_path = _safe_return_path(auth_request_dict.get("return_path") or "/watchlist")
    separator = "&" if "?" in return_path else "?"
    redirect_url = f"{return_path}{separator}tg_auth=1"
    return site_session_response_redirect(redirect_url, session_token=session_token)


@app.get("/watchlist-client.js")
def watchlist_client_script() -> Response:
    path = WEB_DIR / "watchlist-client.js"
    if not path.exists():
        return Response(status_code=404)
    return Response(
        content=path.read_text(encoding="utf-8"),
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=300"},
    )


@app.get("/api/watchlist-client")
def watchlist_client_script_api() -> Response:
    return watchlist_client_script()


@app.post("/api/stripe/checkout-session")
def stripe_checkout_session(data: StripeCheckoutRequest, request: Request) -> JSONResponse:
    if not stripe_enabled():
        raise HTTPException(status_code=503, detail="Stripe checkout is not configured")

    req_lang = detect_lang(request, explicit=data.lang)
    details = enrich_details(request, fallback_lang=req_lang, fallback_placement="stripe_checkout")
    email = data.email.strip().lower()
    source = (data.source or "site").strip()[:64] or "site"
    success_url = STRIPE_SUCCESS_URL or f"{base_url()}/stripe/success?session_id={{CHECKOUT_SESSION_ID}}&lang={req_lang}"
    cancel_url = STRIPE_CANCEL_URL or f"{base_url()}/?lang={req_lang}&checkout=cancel"

    session = stripe_api_call(
        "/v1/checkout/sessions",
        {
            "mode": "subscription",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "customer_email": email,
            "line_items[0][price]": STRIPE_PRICE_ID_MONTHLY,
            "line_items[0][quantity]": "1",
            "allow_promotion_codes": "true",
            "metadata[email]": email,
            "metadata[user_id]": data.user_id or "",
            "metadata[source]": source,
            "metadata[lang]": req_lang,
            "metadata[plan]": "pro_monthly",
        },
    )

    log_site_event(
        event_type="checkout_intent",
        request=request,
        lang=req_lang,
        email=email,
        source=source,
        details={**details, "provider": "stripe", "session_id": session.get("id")},
    )
    return JSONResponse(
        {
            "ok": True,
            "provider": "stripe",
            "session_id": session.get("id"),
            "url": session.get("url"),
            "publishable_key": STRIPE_PUBLISHABLE_KEY,
        }
    )


@app.get("/stripe/success", response_class=HTMLResponse)
def stripe_success(session_id: str, request: Request) -> HTMLResponse:
    req_lang = detect_lang(request)
    if not stripe_enabled():
        if req_lang == "ru":
            return HTMLResponse("<h3>Stripe пока не настроен.</h3>", status_code=503)
        return HTMLResponse("<h3>Stripe is not configured yet.</h3>", status_code=503)

    session = stripe_get(
        f"/v1/checkout/sessions/{session_id}",
        params={"expand[]": "subscription"},
    )
    status = (session.get("status") or "").lower()
    payment_status = (session.get("payment_status") or "").lower()
    metadata = session.get("metadata") or {}
    email = (
        metadata.get("email")
        or session.get("customer_email")
        or ((session.get("customer_details") or {}).get("email"))
        or ""
    ).strip().lower()
    preferred_user_id = (metadata.get("user_id") or "").strip() or None
    currency = (session.get("currency") or "").upper() or None
    amount_total = session.get("amount_total")

    if not email or status != "complete" or payment_status not in {"paid", "no_payment_required"}:
        if req_lang == "ru":
            return HTMLResponse("<h3>Платеж не подтвержден. Если списание было, напишите в поддержку.</h3>", status_code=400)
        return HTMLResponse("<h3>Payment is not confirmed yet. If charged, contact support.</h3>", status_code=400)

    applied, _user_id = activate_pro_from_payment(
        provider="stripe_checkout",
        external_id=str(session.get("id") or session_id),
        event_type="checkout.session.completed",
        email=email,
        preferred_user_id=preferred_user_id,
        amount_cents=int(amount_total) if amount_total is not None else None,
        currency=currency,
        source="stripe_checkout",
        payload=session,
    )

    if req_lang == "ru":
        if applied:
            return HTMLResponse("<h3>Оплата подтверждена. PRO активирован.</h3>")
        return HTMLResponse("<h3>Оплата уже обработана ранее. PRO активен.</h3>")
    if applied:
        return HTMLResponse("<h3>Payment confirmed. PRO is active.</h3>")
    return HTMLResponse("<h3>Payment was already processed. PRO is active.</h3>")


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request) -> JSONResponse:
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe webhook secret is not configured")

    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    if not verify_stripe_signature(payload, signature):
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    event = json.loads(payload.decode("utf-8"))
    event_type = (event.get("type") or "").strip()
    data_obj = ((event.get("data") or {}).get("object")) or {}
    event_id = str(event.get("id") or "")

    if event_type == "checkout.session.completed":
        metadata = data_obj.get("metadata") or {}
        email = (
            metadata.get("email")
            or data_obj.get("customer_email")
            or ((data_obj.get("customer_details") or {}).get("email"))
            or ""
        ).strip().lower()
        if email:
            activate_pro_from_payment(
                provider="stripe_event",
                external_id=event_id or str(data_obj.get("id") or ""),
                event_type=event_type,
                email=email,
                preferred_user_id=(metadata.get("user_id") or "").strip() or None,
                amount_cents=data_obj.get("amount_total"),
                currency=(data_obj.get("currency") or "").upper() or None,
                source="stripe_webhook",
                payload=event,
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
        html = render_email_shell(
            title="Подтвердите email backup",
            body_html=(
                "<p>Подтвердите email, чтобы включить резервный канал Polymarket Pulse.</p>"
                "<p>Что дальше:</p>"
                "<ul>"
                "<li>Telegram остаётся основным live-каналом</li>"
                "<li>Email будет нужен для дайджеста и product updates</li>"
                "<li>Подписку можно выключить из любого письма</li>"
                "</ul>"
            ),
            cta_label="Подтвердить email",
            cta_url=confirm_link,
            footer_html='<p style="margin:20px 0 0;color:#6b7a6e;font-size:12px;line-height:1.6;">Сначала бот для live-сигналов. Email нужен как backup и для digest.</p>',
        )
        subject = "Подтвердите подписку Polymarket Pulse"
        message = "Письмо отправлено. Подтвердите email, чтобы включить backup и digest."
    else:
        html = render_email_shell(
            title="Confirm your email backup",
            body_html=(
                "<p>Confirm your email to enable the backup channel for Polymarket Pulse.</p>"
                "<p>What this does:</p>"
                "<ul>"
                "<li>Telegram stays the primary live signal loop</li>"
                "<li>Email handles digest delivery and launch updates</li>"
                "<li>You can unsubscribe from any message</li>"
                "</ul>"
            ),
            cta_label="Confirm email",
            cta_url=confirm_link,
            footer_html='<p style="margin:20px 0 0;color:#6b7a6e;font-size:12px;line-height:1.6;">Use Telegram for action now. Keep email as backup for digest and updates.</p>',
        )
        subject = "Confirm your Polymarket Pulse subscription"
        message = "Confirmation email sent. Check your inbox to enable digest backup."

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
            return HTMLResponse(
                render_status_page(
                    title="Ссылка недействительна",
                    body_html="Токен подтверждения недействителен или уже использован. Если нужно, просто отправьте email заново с главной страницы.",
                    primary_label="Открыть Telegram-бота",
                    primary_url=PULSE_BOT_URL,
                    secondary_html=f'Вернитесь на <a href="{base_url()}">главную</a> и отправьте email ещё раз.',
                ),
                status_code=400,
            )
        return HTMLResponse(
            render_status_page(
                title="Link expired",
                body_html="This confirmation token is invalid or already used. If needed, resubmit your email from the homepage and we will send a fresh link.",
                primary_label="Open Telegram Bot",
                primary_url=PULSE_BOT_URL,
                secondary_html=f'Go back to the <a href="{base_url()}">homepage</a> and request a fresh email.',
            ),
            status_code=400,
        )

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
                render_email_shell(
                    title="Email подтверждён",
                    body_html=(
                        "<p>Подписка подтверждена. Email-дайджест включён.</p>"
                        "<p>Что теперь:</p>"
                        "<ul>"
                        "<li>Следите за live-сигналами в Telegram</li>"
                        "<li>Email будет приходить как backup и digest</li>"
                        "<li>Если сигналов нет, это нормально: quiet-state тоже часть продукта</li>"
                        "</ul>"
                    ),
                    cta_label="Открыть Telegram-бота",
                    cta_url=PULSE_BOT_URL,
                    footer_html=f'<p style="margin:20px 0 0;color:#6b7a6e;font-size:12px;line-height:1.6;"><a href="{unsub}" style="color:#8fa88f;">Отписаться</a></p>',
                ),
            )
        except Exception:
            pass
        return HTMLResponse(
            render_status_page(
                title="Email подтверждён",
                body_html="Дайджест включён. Лучше всего использовать Telegram как основной live-канал, а email оставить как backup для digest и updates.",
                primary_label="Открыть Telegram-бота",
                primary_url=PULSE_BOT_URL,
                secondary_html=f'<a href="{unsub}">Отписаться</a>',
            )
        )
    try:
        send_email(
            email,
            "Welcome to Polymarket Pulse",
            render_email_shell(
                title="Email confirmed",
                body_html=(
                    "<p>You are now confirmed for Polymarket Pulse email updates.</p>"
                    "<p>What to expect:</p>"
                    "<ul>"
                    "<li>Telegram stays your primary live signal loop</li>"
                    "<li>Email works as backup for digest and launch updates</li>"
                    "<li>Quiet days are expected; we do not force noise into the feed</li>"
                    "</ul>"
                ),
                cta_label="Open Telegram Bot",
                cta_url=PULSE_BOT_URL,
                footer_html=f'<p style="margin:20px 0 0;color:#6b7a6e;font-size:12px;line-height:1.6;"><a href="{unsub}" style="color:#8fa88f;">Unsubscribe</a></p>',
            ),
        )
    except Exception:
        pass
    return HTMLResponse(
        render_status_page(
            title="Email confirmed",
            body_html="Daily digest is enabled. Use Telegram for the live loop now, and keep email as backup for digest and updates.",
            primary_label="Open Telegram Bot",
            primary_url=PULSE_BOT_URL,
            secondary_html=f'<a href="{unsub}">Unsubscribe</a>',
        )
    )


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
            return HTMLResponse(
                render_status_page(
                    title="Отписка не сработала",
                    body_html="Токен не найден или этот email уже был отписан.",
                    primary_label="Открыть Telegram-бота",
                    primary_url=PULSE_BOT_URL,
                    secondary_html=f'<a href="{base_url()}">Вернуться на сайт</a>',
                ),
                status_code=400,
            )
        return HTMLResponse(
            render_status_page(
                title="Unsubscribe failed",
                body_html="This token was not found or the email was already unsubscribed.",
                primary_label="Open Telegram Bot",
                primary_url=PULSE_BOT_URL,
                secondary_html=f'<a href="{base_url()}">Back to homepage</a>',
            ),
            status_code=400,
        )

    log_site_event(
        event_type="unsubscribe_success",
        request=request,
        lang=req_lang,
        email=row[0],
        details=details,
    )
    if req_lang == "ru":
        return HTMLResponse(
            render_status_page(
                title="Вы отписаны",
                body_html="Email-дайджест и product updates больше не будут приходить на этот адрес.",
                primary_label="Открыть Telegram-бота",
                primary_url=PULSE_BOT_URL,
                secondary_html=f'<a href="{base_url()}">Вернуться на сайт</a>',
            )
        )
    return HTMLResponse(
        render_status_page(
            title="You are unsubscribed",
            body_html="Daily digest and product updates will no longer be sent to this email.",
            primary_label="Open Telegram Bot",
            primary_url=PULSE_BOT_URL,
            secondary_html=f'<a href="{base_url()}">Back to homepage</a>',
        )
    )


@app.get("/{slug}", response_class=HTMLResponse)
def seo_page(slug: str, request: Request) -> HTMLResponse:
    if slug not in SEO_PAGES:
        raise HTTPException(status_code=404, detail="Not found")
    lang = detect_site_lang(request)
    return HTMLResponse(render_seo_page(slug, lang, noindex_override=bool(request.query_params)))
