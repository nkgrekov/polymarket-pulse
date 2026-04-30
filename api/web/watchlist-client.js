(function () {
  const STORAGE_KEY = "pulse_watchlist_v2";
  const DEFAULT_SENSITIVITY = 0.03;
  const DEFAULT_TELEGRAM_URL = "https://t.me/polymarket_pulse_bot?start=email_backup";
  const LOCALE = document.documentElement.lang === "ru" ? "ru" : "en";
  const TEXT = {
    en: {
      add: "Add to watchlist",
      saved: "Saved",
      savedShort: "Saved",
      pending: "Pending login",
      pendingShort: "Pending",
      bellOff: "🔕 Bell off",
      bellOn: "🔔 Bell on",
      bellPaused: "⏸ Bell paused",
      bellLocked: "⚠ Limit",
      bellLogin: "🔒 Log in",
      watchlist: "Watchlist",
      emptyTitle: "No saved markets yet.",
      emptyCopy: "Start from Live Movers, save one market on the site, then come back here to manage bells and sort the list.",
      openMovers: "Open Live Movers",
      openBot: "Open Telegram Bot",
      loginTitle: "Log in with Telegram to save your watchlist.",
      loginCopy: "We keep the market context and route you through Telegram so the return loop lands back on the website with real persistence.",
      keepLocal: "Stay here",
      continueTelegram: "Continue in Telegram",
      connectedAs: "Connected via Telegram",
      search: "Search markets",
      category: "Category",
      status: "Status",
      alertState: "Alert state",
      sort: "Sort",
      compact: "Compact table",
      full: "Comfortable table",
      all: "All",
      politics: "Politics",
      macro: "Macro",
      crypto: "Crypto",
      other: "Other",
      sortSaved: "Saved recently",
      sortDelta: "Delta",
      sortLiquidity: "Liquidity",
      sortSpread: "Spread",
      sortFreshness: "Freshness",
      colMarket: "Market",
      colMid: "Mid",
      colDelta: "Delta",
      col1m: "1m",
      col5m: "5m",
      colLiquidity: "Liquidity",
      colSpread: "Spread",
      colFreshness: "Freshness",
      colStatus: "Status",
      colQuality: "Signal quality",
      colAlert: "Bell",
      colSensitivity: "Sensitivity",
      colActions: "Actions",
      openMarket: "Open market",
      turnOnBell: "Turn on in Telegram",
      pauseBell: "Pause bell",
      resumeBell: "Resume bell",
      turnOffBell: "Bell off",
      thresholdTelegram: "Threshold in Telegram",
      remove: "Remove",
      configureTelegram: "Configure in Telegram",
      alertSetup: "Set bell in Telegram",
      loginRequired: "Telegram login required",
      alertsOff: "Bell off",
      alertOn: "Bell on",
      alertPaused: "Bell paused",
      belowThreshold: "Below threshold",
      marketClosed: "Market closed",
      staleQuotes: "Stale quotes",
      noQuotes: "No quotes",
      filteredSpread: "Filtered by spread",
      filteredLiquidity: "Filtered by liquidity",
      savedState: "Saved",
      legacyFallback: "Legacy fallback",
      liveQuality: "Live quality gated",
      quote: "quote",
      spreadUnit: "spread",
      liqUnit: "liq",
      sensitivityShort: "pp",
      loginBannerTitle: "Telegram is the identity and bell layer.",
      loginBannerCopy: "Browse and compare freely on the site. Real persistence starts only after Telegram login and return-to-site completion.",
      pendingBannerTitle: "Some markets are still waiting for Telegram login.",
      pendingBannerCopy: "They are only stored in this browser right now. Finish Telegram login to persist them on the site and across devices.",
      statusUnknown: "Unknown",
      pendingSaved: "Pending after Telegram login",
      lastAlert: "Last alert",
      noAlertYet: "No alert yet",
      majorMoves: "Major moves only",
      syncSaved: "Saved to your watchlist",
      loadingTitle: "Loading watchlist...",
      loadingCopy: "Refreshing saved markets and bell states from the current workspace.",
      unavailableTitle: "Watchlist is temporarily unavailable.",
      unavailableCopy: "The workspace API did not return cleanly. Retry in a few seconds or continue in Telegram.",
      filteredEmptyTitle: "No markets match these filters.",
      filteredEmptyCopy: "Clear one filter or open Live Movers to save a different market.",
      summarySaved: "saved",
      summaryBellOn: "bell on",
      summaryPaused: "paused",
      summaryPending: "pending login",
      loginFinishNote: "Finish login in Telegram, then tap Return to site in the bot.",
      pendingTooltip: "Saved only in this browser for now. Finish Telegram login to persist it on the site.",
      saveTooltip: "Save this market to your website watchlist.",
      syncSuccessTitle: "Telegram connected. Watchlist synced.",
      syncSuccessCopy: "Pending markets were persisted into your website watchlist.",
      loginSuccessTitle: "Telegram connected.",
      loginSuccessCopy: "This website is now linked to your Telegram identity.",
      pauseSuccessTitle: "Bell paused.",
      pauseSuccessCopy: "The market stays saved on the site, but Telegram will stay quiet for now.",
      resumeSuccessTitle: "Bell resumed.",
      resumeSuccessCopy: "Telegram can alert this market again when the move clears your threshold.",
      offSuccessTitle: "Bell turned off.",
      offSuccessCopy: "The market stays saved, but Telegram alerts are now disabled for this row.",
    },
    ru: {
      add: "Add to watchlist",
      saved: "Saved",
      savedShort: "Saved",
      pending: "Ждёт login",
      pendingShort: "Ждёт",
      bellOff: "🔕 Bell off",
      bellOn: "🔔 Bell on",
      bellPaused: "⏸ Bell paused",
      bellLocked: "⚠ Лимит",
      bellLogin: "🔒 Войти",
      watchlist: "Watchlist",
      emptyTitle: "Сохранённых рынков пока нет.",
      emptyCopy: "Начните с Live Movers, сохраните один рынок на сайте и затем возвращайтесь сюда, чтобы управлять bell и сортировкой.",
      openMovers: "Открыть Live Movers",
      openBot: "Открыть Telegram-бота",
      loginTitle: "Войдите через Telegram, чтобы сохранить watchlist.",
      loginCopy: "Мы сохраняем контекст рынка и отправляем вас в Telegram, чтобы после возврата сайт увидел реальную identity и persistence.",
      keepLocal: "Остаться здесь",
      continueTelegram: "Продолжить в Telegram",
      connectedAs: "Подключено через Telegram",
      search: "Поиск рынков",
      category: "Категория",
      status: "Статус",
      alertState: "Bell state",
      sort: "Сортировка",
      compact: "Компактная таблица",
      full: "Обычная таблица",
      all: "Все",
      politics: "Politics",
      macro: "Macro",
      crypto: "Crypto",
      other: "Other",
      sortSaved: "Сначала свежесохранённые",
      sortDelta: "Delta",
      sortLiquidity: "Liquidity",
      sortSpread: "Spread",
      sortFreshness: "Freshness",
      colMarket: "Рынок",
      colMid: "Mid",
      colDelta: "Delta",
      col1m: "1m",
      col5m: "5m",
      colLiquidity: "Liquidity",
      colSpread: "Spread",
      colFreshness: "Freshness",
      colStatus: "Статус",
      colQuality: "Signal quality",
      colAlert: "Bell",
      colSensitivity: "Sensitivity",
      colActions: "Действия",
      openMarket: "Открыть рынок",
      turnOnBell: "Включить в Telegram",
      pauseBell: "Пауза bell",
      resumeBell: "Возобновить bell",
      turnOffBell: "Bell off",
      thresholdTelegram: "Threshold в Telegram",
      remove: "Удалить",
      configureTelegram: "Настроить в Telegram",
      alertSetup: "Настроить bell в Telegram",
      loginRequired: "Нужен Telegram login",
      alertsOff: "Bell off",
      alertOn: "Bell on",
      alertPaused: "Bell paused",
      belowThreshold: "Below threshold",
      marketClosed: "Market closed",
      staleQuotes: "Stale quotes",
      noQuotes: "No quotes",
      filteredSpread: "Filtered by spread",
      filteredLiquidity: "Filtered by liquidity",
      savedState: "Saved",
      legacyFallback: "Legacy fallback",
      liveQuality: "Live quality gated",
      quote: "quote",
      spreadUnit: "spread",
      liqUnit: "liq",
      sensitivityShort: "pp",
      loginBannerTitle: "Telegram остаётся identity- и bell-слоем.",
      loginBannerCopy: "На сайте можно свободно смотреть и сравнивать рынки. Настоящее сохранение начинается только после Telegram login и возврата на сайт.",
      pendingBannerTitle: "Часть рынков всё ещё ждёт Telegram login.",
      pendingBannerCopy: "Пока они лежат только в этом браузере. Завершите Telegram login, чтобы закрепить их на сайте и между устройствами.",
      statusUnknown: "Unknown",
      pendingSaved: "Ждёт Telegram login",
      lastAlert: "Последний алерт",
      noAlertYet: "Алертов ещё не было",
      majorMoves: "Только major moves",
      syncSaved: "Сохранено в вашем watchlist",
      loadingTitle: "Загружаю watchlist...",
      loadingCopy: "Обновляю сохранённые рынки и bell-состояния из текущего workspace.",
      unavailableTitle: "Watchlist временно недоступен.",
      unavailableCopy: "Workspace API сейчас ответил неудачно. Повторите через несколько секунд или продолжайте через Telegram.",
      filteredEmptyTitle: "Под эти фильтры ничего не подходит.",
      filteredEmptyCopy: "Снимите один фильтр или откройте Live Movers и сохраните другой рынок.",
      summarySaved: "saved",
      summaryBellOn: "bell on",
      summaryPaused: "paused",
      summaryPending: "ждут login",
      loginFinishNote: "Завершите login в Telegram, затем нажмите Return to site в боте.",
      pendingTooltip: "Пока сохранено только в этом браузере. Завершите Telegram login, чтобы закрепить рынок на сайте.",
      saveTooltip: "Сохранить этот рынок в watchlist на сайте.",
      syncSuccessTitle: "Telegram подключён. Watchlist синхронизирован.",
      syncSuccessCopy: "Pending-рынки закреплены в website watchlist.",
      loginSuccessTitle: "Telegram подключён.",
      loginSuccessCopy: "Этот сайт теперь связан с вашей Telegram identity.",
      pauseSuccessTitle: "Bell поставлен на паузу.",
      pauseSuccessCopy: "Рынок остаётся сохранённым на сайте, но Telegram пока молчит.",
      resumeSuccessTitle: "Bell снова включён.",
      resumeSuccessCopy: "Теперь Telegram снова может прислать алерт, когда движение превысит ваш threshold.",
      offSuccessTitle: "Bell выключен.",
      offSuccessCopy: "Рынок остаётся в watchlist, но алерты Telegram для этой строки отключены.",
    },
  };
  const copy = TEXT[LOCALE];
  const VIEW_STATE = {
    query: "",
    category: "all",
    status: "all",
    alertState: "all",
    sort: "saved_at",
    compact: false,
  };
  const SESSION = { loaded: false, loggedIn: false, user: null };
  const FLASH = { title: "", copy: "", tone: "" };
  let SERVER_ROWS = [];

  function esc(value) {
    return String(value == null ? "" : value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function readState() {
    try {
      const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
      return {
        version: 2,
        pendingContext: parsed.pendingContext || null,
        pendingItems: parsed.pendingItems && typeof parsed.pendingItems === "object" ? parsed.pendingItems : {},
      };
    } catch (_) {
      return { version: 2, pendingContext: null, pendingItems: {} };
    }
  }

  function writeState(state) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function nowIso() {
    return new Date().toISOString();
  }

  function setFlash(title, copyText, tone) {
    FLASH.title = title || "";
    FLASH.copy = copyText || "";
    FLASH.tone = tone || "";
  }

  function trackEvent(eventType, details) {
    const payload = {
      event_type: eventType,
      source: "site",
      details: Object.assign(
        {
          page_path: window.location.pathname + window.location.search,
          page_url: window.location.href,
          lang: LOCALE,
        },
        details || {}
      ),
    };
    try {
      if (typeof window.gtag === "function") window.gtag("event", eventType, payload.details);
    } catch (_) {}
    try {
      fetch("/api/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        keepalive: true,
      });
    } catch (_) {}
  }

  function pagePlacement() {
    return window.location.pathname;
  }

  function baseEventDetails(details) {
    return Object.assign(
      {
        placement: pagePlacement(),
        source_page: pagePlacement(),
        user_logged_in: SESSION.loggedIn,
      },
      details || {}
    );
  }

  function formatPct(value) {
    const num = Number(value);
    return Number.isFinite(num) ? `${(num * 100).toFixed(1)}%` : "n/a";
  }

  function formatPp(value) {
    const num = Number(value);
    if (!Number.isFinite(num)) return "n/a";
    const points = num * 100;
    const prefix = points > 0 ? "+" : "";
    return `${prefix}${points.toFixed(1)}pp`;
  }

  function formatLiq(value) {
    const num = Number(value);
    if (!Number.isFinite(num) || num <= 0) return "n/a";
    if (num >= 1000000) return `$${(num / 1000000).toFixed(1)}m`;
    if (num >= 1000) return `$${Math.round(num / 1000)}k`;
    return `$${Math.round(num)}`;
  }

  function formatSpread(value) {
    const num = Number(value);
    return Number.isFinite(num) ? `${(num * 100).toFixed(1)}pp` : "n/a";
  }

  function formatFreshness(value) {
    const num = Number(value);
    if (!Number.isFinite(num)) return "n/a";
    if (num < 60) return `${Math.round(num)}s`;
    return `${Math.round(num / 60)}m`;
  }

  function formatLastAlert(value) {
    if (!value) return copy.noAlertYet;
    try {
      const date = new Date(value);
      return `${copy.lastAlert}: ${date.toLocaleString(LOCALE === "ru" ? "ru-RU" : "en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}`;
    } catch (_) {
      return `${copy.lastAlert}: ${value}`;
    }
  }

  function sensitivityLabel(value) {
    const num = Number(value);
    if (!Number.isFinite(num)) return "--";
    if (Math.abs(num - 0.15) < 1e-9) return copy.majorMoves;
    return `${(num * 100).toFixed(1)}${copy.sensitivityShort}`;
  }

  function statusLabel(code) {
    return {
      saved: copy.savedState,
      below_threshold: copy.belowThreshold,
      market_closed: copy.marketClosed,
      stale_quotes: copy.staleQuotes,
      no_quotes: copy.noQuotes,
      filtered_by_spread: copy.filteredSpread,
      filtered_by_liquidity: copy.filteredLiquidity,
      legacy_snapshot: copy.legacyFallback,
      pending: copy.pendingSaved,
    }[code] || copy.statusUnknown;
  }

  function statusTooltip(code) {
    return {
      saved: "Saved to the site watchlist. This alone does not turn Telegram alerts on.",
      below_threshold: "The market is still saved, but the move is below your threshold right now.",
      market_closed: "This market looks closed, so alerts may stay quiet until you replace it.",
      stale_quotes: "Quotes are too old right now. Treat this row as context, not urgency.",
      no_quotes: "No fresh two-sided quote is available in the current window.",
      filtered_by_spread: "Spread is too wide for a clean live signal right now.",
      filtered_by_liquidity: "Liquidity is too thin for a strong live signal right now.",
      legacy_snapshot: "This row is filled from fallback data while the hot surface is incomplete.",
      pending: "Saved locally for now. Log in with Telegram to persist it across devices.",
    }[code] || "Current row state.";
  }

  function qualityLabel(code) {
    return {
      live_quality_gated: copy.liveQuality,
      legacy_fallback: copy.legacyFallback,
      market_closed: copy.marketClosed,
      stale_quotes: copy.staleQuotes,
      no_quotes: copy.noQuotes,
      filtered_by_spread: copy.filteredSpread,
      filtered_by_liquidity: copy.filteredLiquidity,
    }[code] || copy.statusUnknown;
  }

  function qualityTooltip(code) {
    return {
      live_quality_gated: "Freshness, spread, and liquidity are good enough for the live workspace.",
      legacy_fallback: "Fallback data is shown so the row stays readable while hot data catches up.",
      market_closed: "Closed markets stay visible for context, but they should not drive new alerts.",
      stale_quotes: "Quotes are stale, so the move may no longer be actionable.",
      no_quotes: "No clean quote is available for this market right now.",
      filtered_by_spread: "Spread is too wide, so this move is filtered for quality.",
      filtered_by_liquidity: "Liquidity is too low, so this move is filtered for quality.",
    }[code] || "Signal quality state.";
  }

  function bellTooltip(row) {
    const state = String(row.alert_state || "off");
    if (state === "on") return "Telegram alerts are enabled for this saved market.";
    if (state === "paused") return "This bell is paused. The market stays saved, but Telegram stays quiet.";
    if (state === "limit") return "Your current plan hit an alert limit. Upgrade or free space before adding more bells.";
    if (!SESSION.loggedIn) return "Log in with Telegram to enable alerts for this saved market.";
    return "This market is saved, but Telegram alerts are still off until you turn the bell on.";
  }

  function bellLabel(row) {
    const state = String(row.alert_state || "off");
    if (state === "on") return copy.bellOn;
    if (state === "paused") return copy.bellPaused;
    if (state === "limit") return copy.bellLocked;
    if (!SESSION.loggedIn) return copy.bellLogin;
    return copy.bellOff;
  }

  function primaryBellControl(row) {
    const state = String(row.alert_state || "off");
    if (!SESSION.loggedIn) {
      return { action: "toggle_alert", label: copy.bellLogin, extraClass: "", title: bellTooltip(row) };
    }
    if (state === "on") {
      return { action: "pause_alert", label: copy.pauseBell, extraClass: "saved", title: "Pause Telegram alerts while keeping this market saved on the site." };
    }
    if (state === "paused") {
      return { action: "resume_alert", label: copy.resumeBell, extraClass: "primary", title: "Resume Telegram alerts for this saved market." };
    }
    return { action: "toggle_alert", label: copy.turnOnBell, extraClass: "", title: "Open Telegram and choose sensitivity to turn this bell on." };
  }

  function secondaryBellControl(row) {
    const state = String(row.alert_state || "off");
    if (!SESSION.loggedIn) {
      return { kind: "telegram", action: "configure_telegram", label: copy.configureTelegram, title: "Open Telegram to finish login and configure this market." };
    }
    if (state === "on") {
      return { kind: "telegram", action: "configure_telegram", label: copy.thresholdTelegram, title: "Open Telegram to change threshold for this market bell." };
    }
    if (state === "paused") {
      return { kind: "button", action: "off_alert", label: copy.turnOffBell, title: "Turn this bell fully off while keeping the market saved." };
    }
    return { kind: "telegram", action: "configure_telegram", label: copy.configureTelegram, title: "Open Telegram to configure this market bell." };
  }

  function alertStateLabel(state) {
    return {
      off: copy.alertsOff,
      on: copy.alertOn,
      paused: copy.alertPaused,
      login_required: copy.loginRequired,
      limit: copy.bellLocked,
    }[state] || copy.alertsOff;
  }

  function defaultTrackUrl(marketId) {
    const safe = String(marketId || "").replace(/[^a-zA-Z0-9_-]/g, "").slice(0, 48);
    return safe ? `https://t.me/polymarket_pulse_bot?start=site_track_${safe}` : DEFAULT_TELEGRAM_URL;
  }

  function buildPendingItem(market) {
    const marketId = String(market.market_id || "");
    return {
      market_id: marketId,
      question: market.question || marketId,
      slug: market.slug || "",
      market_url: market.market_url || "",
      track_url: market.track_url || defaultTrackUrl(marketId),
      source: market.source || "site",
      saved_at: nowIso(),
      status: "pending",
      alert_state: "login_required",
      effective_threshold_value: null,
      last_alert_at: null,
    };
  }

  function pendingItems(state) {
    return Object.values(state.pendingItems || {}).sort((a, b) => String(b.saved_at || "").localeCompare(String(a.saved_at || "")));
  }

  function pendingCount() {
    return pendingItems(readState()).length;
  }

  function savePendingMarket(market) {
    const state = readState();
    const next = buildPendingItem(market);
    state.pendingItems[next.market_id] = Object.assign({}, state.pendingItems[next.market_id] || {}, next);
    state.pendingContext = {
      intent: "watchlist_add",
      market_id: next.market_id,
      question: next.question,
      ts: nowIso(),
    };
    writeState(state);
    return next;
  }

  function clearPendingMarket(marketId) {
    const state = readState();
    delete state.pendingItems[String(marketId || "")];
    writeState(state);
  }

  function marketFromElement(element) {
    return {
      market_id: String(element.getAttribute("data-market-id") || ""),
      question: element.getAttribute("data-market-question") || "",
      slug: element.getAttribute("data-market-slug") || "",
      market_url: element.getAttribute("data-market-url") || "",
      track_url: element.getAttribute("data-track-url") || "",
      source: element.getAttribute("data-market-source") || "site",
    };
  }

  async function jsonFetch(url, options) {
    const res = await fetch(url, Object.assign({ headers: { "Content-Type": "application/json" } }, options || {}));
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const err = new Error(data.detail || "request_failed");
      err.payload = data;
      throw err;
    }
    return data;
  }

  async function loadSession() {
    try {
      const data = await jsonFetch("/api/watchlist/session", { method: "GET" });
      SESSION.loaded = true;
      SESSION.loggedIn = Boolean(data.logged_in);
      SESSION.user = data.user || null;
    } catch (_) {
      SESSION.loaded = true;
      SESSION.loggedIn = false;
      SESSION.user = null;
    }
  }

  async function startAuthFlow(intent, market) {
    const marketId = market && market.market_id ? String(market.market_id) : null;
    const payload = {
      intent: intent,
      market_id: marketId,
      question: market && market.question ? market.question : null,
      return_path: `${window.location.pathname}${window.location.search}`,
      locale: LOCALE,
      source: "site",
    };
    const data = await jsonFetch("/api/watchlist/auth/start", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return data.telegram_url || DEFAULT_TELEGRAM_URL;
  }

  function ensurePromptUi() {
    if (document.getElementById("watchlist-login-prompt")) return;
    const style = document.createElement("style");
    style.textContent = [
      ".watchlist-login-prompt{position:fixed;inset:0;display:none;align-items:flex-end;justify-content:flex-end;padding:18px;z-index:80;background:rgba(9,11,10,.42);backdrop-filter:blur(6px)}",
      ".watchlist-login-prompt.open{display:flex}",
      ".watchlist-login-card{width:min(420px,100%);border:1px solid #1e2520;border-radius:18px;background:#101511;box-shadow:0 24px 72px rgba(0,0,0,.42);padding:18px;color:#e8ede9;font-family:'JetBrains Mono',monospace}",
      ".watchlist-login-card h3{margin:0;font-size:18px;line-height:1.2;font-family:'Space Grotesk','Segoe UI',sans-serif}",
      ".watchlist-login-card p{margin:10px 0 0;color:#8fa88f;font-size:12px;line-height:1.55}",
      ".watchlist-login-actions{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px}",
      ".watchlist-login-btn,.watchlist-login-ghost{display:inline-flex;align-items:center;justify-content:center;min-height:42px;padding:10px 14px;border-radius:12px;text-decoration:none;font-size:12px;font-weight:700}",
      ".watchlist-login-btn{background:linear-gradient(180deg,#00ff88 0%,#00d874 100%);border:1px solid #00ff88;color:#0a0c0b}",
      ".watchlist-login-ghost{border:1px solid #2a332b;background:#131714;color:#8fa88f;cursor:pointer}",
    ].join("");
    document.head.appendChild(style);

    const prompt = document.createElement("div");
    prompt.id = "watchlist-login-prompt";
    prompt.className = "watchlist-login-prompt";
    prompt.innerHTML = [
      '<div class="watchlist-login-card" role="dialog" aria-modal="true" aria-live="polite">',
      `<h3 id="watchlist-login-title">${esc(copy.loginTitle)}</h3>`,
      `<p id="watchlist-login-market"></p>`,
      `<p id="watchlist-login-copy">${esc(copy.loginCopy)}</p>`,
      '<div class="watchlist-login-actions">',
      `<a id="watchlist-login-open" class="watchlist-login-btn" target="_blank" rel="noopener noreferrer" href="${DEFAULT_TELEGRAM_URL}">${esc(copy.continueTelegram)}</a>`,
      `<button id="watchlist-login-close" class="watchlist-login-ghost" type="button">${esc(copy.keepLocal)}</button>`,
      "</div>",
      "</div>",
    ].join("");
    document.body.appendChild(prompt);
    prompt.addEventListener("click", (event) => {
      if (event.target === prompt) prompt.classList.remove("open");
    });
    prompt.querySelector("#watchlist-login-close").addEventListener("click", () => {
      prompt.classList.remove("open");
    });
  }

  function showBridgePrompt(market, telegramUrl, intent) {
    ensurePromptUi();
    const prompt = document.getElementById("watchlist-login-prompt");
    const marketEl = document.getElementById("watchlist-login-market");
    const openEl = document.getElementById("watchlist-login-open");
    const titleEl = document.getElementById("watchlist-login-title");
    const copyEl = document.getElementById("watchlist-login-copy");
    const state = readState();
    state.pendingContext = {
      intent: intent,
      market_id: market && market.market_id ? market.market_id : null,
      question: market && market.question ? market.question : null,
      ts: nowIso(),
    };
    writeState(state);
    titleEl.textContent = intent === "alert" ? copy.alertSetup : copy.loginTitle;
    marketEl.textContent = market && market.question ? `${copy.watchlist}: ${market.question}` : "";
    copyEl.textContent = `${copy.loginCopy} ${copy.loginFinishNote}`;
    openEl.href = telegramUrl || DEFAULT_TELEGRAM_URL;
    prompt.classList.add("open");
    trackEvent("watchlist_prompt_open", {
      placement: window.location.pathname,
      intent: intent,
      market_id: market && market.market_id ? market.market_id : "",
    });
  }

  function syncSessionCopy() {
    const copyNode = document.querySelector("[data-watchlist-session-copy]");
    if (!copyNode) return;
    if (!SESSION.loggedIn) {
      copyNode.textContent = copy.loginTitle;
      return;
    }
    const user = SESSION.user || {};
    const name = user.username ? `@${user.username}` : user.first_name || copy.connectedAs;
    copyNode.textContent = `${copy.connectedAs}: ${name}`;
  }

  function serverRowsMap() {
    return new Map((SERVER_ROWS || []).map((row) => [String(row.market_id), row]));
  }

  function pendingRows() {
    return pendingItems(readState()).map((item) => ({
      market_id: item.market_id,
      question: item.question,
      slug: item.slug || "",
      market_url: item.market_url || "",
      track_url: item.track_url || defaultTrackUrl(item.market_id),
      category: "other",
      status: item.status || "pending",
      market_status: "unknown",
      signal_quality: "legacy_fallback",
      yes_mid_now: null,
      delta_primary: null,
      delta_1m: null,
      delta_5m: null,
      liquidity: null,
      spread: null,
      freshness_seconds: null,
      quote_ts: null,
      alert_enabled: false,
      alert_paused: false,
      alert_state: "login_required",
      effective_threshold_value: null,
      saved_at: item.saved_at,
      last_alert_at: null,
    }));
  }

  function currentRows() {
    return SESSION.loggedIn ? (SERVER_ROWS || []) : pendingRows();
  }

  function clearSyncedPending() {
    if (!SESSION.loggedIn || !SERVER_ROWS.length) return;
    const state = readState();
    let dirty = false;
    SERVER_ROWS.forEach((row) => {
      if (state.pendingItems[String(row.market_id)]) {
        delete state.pendingItems[String(row.market_id)];
        dirty = true;
      }
    });
    if (dirty) writeState(state);
  }

  function watchlistStateForMarket(marketId) {
    const key = String(marketId || "");
    if (SESSION.loggedIn && serverRowsMap().has(key)) return "saved";
    if (readState().pendingItems[key]) return "pending";
    return "new";
  }

  function isSaved(marketId) {
    return watchlistStateForMarket(marketId) !== "new";
  }

  function rowForMarket(marketId) {
    const key = String(marketId || "");
    if (SESSION.loggedIn) return serverRowsMap().get(key) || null;
    return readState().pendingItems[key] || null;
  }

  function syncWatchlistButtons(root) {
    const scope = root || document;
    scope.querySelectorAll('[data-watchlist-action="toggle_save"]').forEach((button) => {
      const marketId = String(button.getAttribute("data-market-id") || "");
      const state = watchlistStateForMarket(marketId);
      const saved = state !== "new";
      button.classList.toggle("saved", saved);
      button.classList.toggle("primary", state === "new");
      button.setAttribute("aria-pressed", saved ? "true" : "false");
      button.textContent = state === "saved" ? copy.saved : state === "pending" ? copy.pending : copy.add;
      button.title = state === "saved"
        ? copy.syncSaved
        : state === "pending"
          ? copy.pendingTooltip
          : copy.saveTooltip;
    });
    scope.querySelectorAll('[data-watchlist-action="toggle_alert"]').forEach((button) => {
      const marketId = String(button.getAttribute("data-market-id") || "");
      const row = rowForMarket(marketId) || {};
      const state = String(row.alert_state || "off");
      button.classList.toggle("primary", state === "on");
      button.classList.toggle("saved", state === "paused");
      button.textContent = bellLabel(row);
      button.title = bellTooltip(row);
    });
  }

  async function loadWorkspaceRows() {
    if (SESSION.loggedIn) {
      const data = await jsonFetch("/api/watchlist-workspace", { method: "GET" });
      SERVER_ROWS = Array.isArray(data.rows) ? data.rows : [];
      clearSyncedPending();
      const unsynced = pendingRows().filter((row) => !serverRowsMap().has(String(row.market_id || "")));
      if (unsynced.length) SERVER_ROWS = SERVER_ROWS.concat(unsynced);
      return;
    }
    const items = pendingItems(readState());
    if (!items.length) {
      SERVER_ROWS = [];
      return;
    }
    const ids = items.map((item) => item.market_id).join(",");
    const data = await jsonFetch(`/api/watchlist-workspace?market_ids=${encodeURIComponent(ids)}`, { method: "GET" });
    const rowMap = new Map((Array.isArray(data.rows) ? data.rows : []).map((row) => [String(row.market_id), row]));
    SERVER_ROWS = items.map((item) => Object.assign({}, rowMap.get(String(item.market_id)) || {}, {
      market_id: item.market_id,
      question: (rowMap.get(String(item.market_id)) || {}).question || item.question,
      market_url: (rowMap.get(String(item.market_id)) || {}).market_url || item.market_url,
      track_url: (rowMap.get(String(item.market_id)) || {}).track_url || item.track_url,
      saved_at: item.saved_at,
      alert_state: "login_required",
      alert_enabled: false,
      alert_paused: false,
      effective_threshold_value: null,
      last_alert_at: null,
      status: (rowMap.get(String(item.market_id)) || {}).status || "pending",
    }));
  }

  async function syncPendingToServer() {
    return syncPendingToServerWithOptions();
  }

  async function syncPendingToServerWithOptions(options) {
    if (!SESSION.loggedIn) return 0;
    const settings = options && typeof options === "object" ? options : {};
    const state = readState();
    const items = pendingItems(state);
    if (!items.length) return 0;
    let synced = 0;
    try {
      const data = await jsonFetch("/api/watchlist/sync", {
        method: "POST",
        body: JSON.stringify({
          items: items.map((item) => ({
            market_id: String(item.market_id || ""),
            question: item.question || "",
            slug: item.slug || "",
            source: item.source || "site",
          })),
        }),
      });
      const savedIds = new Set(Array.isArray(data.saved_market_ids) ? data.saved_market_ids.map((value) => String(value || "")) : []);
      if (Array.isArray(data.rows)) SERVER_ROWS = data.rows;
      synced = savedIds.size;
      if (savedIds.size) {
        Object.keys(state.pendingItems || {}).forEach((marketId) => {
          if (savedIds.has(String(marketId || ""))) delete state.pendingItems[marketId];
        });
      }
    } catch (_) {}
    if (synced > 0) {
      if (!pendingItems(state).length) state.pendingContext = null;
      writeState(state);
      clearSyncedPending();
      trackEvent("watchlist_pending_sync_success", baseEventDetails({ synced_count: synced, pending_left: pendingItems(state).length, watchlist_state: "saved" }));
      if (!settings.silent) window.dispatchEvent(new CustomEvent("pulse:watchlist-sync"));
    }
    return synced;
  }

  function optionHtml(entries, selected) {
    return entries.map((entry) => {
      const label = entry[0];
      const value = entry[1];
      const sel = value === selected ? " selected" : "";
      return `<option value="${esc(value)}"${sel}>${esc(label)}</option>`;
    }).join("");
  }

  function chip(label, extraClass) {
    return `<span class="watchlist-chip${extraClass ? ` ${extraClass}` : ""}">${esc(label)}</span>`;
  }

  function chipWithTitle(label, title, extraClass) {
    return `<span class="watchlist-chip${extraClass ? ` ${extraClass}` : ""}" title="${esc(title || "")}">${esc(label)}</span>`;
  }

  function renderEmptyBlock(title, copyText, actionsHtml) {
    return [
      '<section class="watchlist-empty">',
      `<h3>${esc(title)}</h3>`,
      `<p>${esc(copyText)}</p>`,
      actionsHtml || "",
      "</section>",
    ].join("");
  }

  function actionRow(row) {
    const primary = primaryBellControl(row);
    const secondary = secondaryBellControl(row);
    return [
      '<div class="watchlist-action-row">',
      `<button type="button" class="watchlist-action${primary.extraClass ? ` ${primary.extraClass}` : ""}" title="${esc(primary.title)}" data-watchlist-action="${esc(primary.action)}" data-market-id="${esc(row.market_id)}" data-market-question="${esc(row.question)}" data-market-url="${esc(row.market_url || "")}" data-track-url="${esc(row.track_url || defaultTrackUrl(row.market_id))}" data-market-slug="${esc(row.slug || "")}" data-market-source="workspace">${esc(primary.label)}</button>`,
      secondary.kind === "button"
        ? `<button type="button" class="watchlist-action" title="${esc(secondary.title)}" data-watchlist-action="${esc(secondary.action)}" data-market-id="${esc(row.market_id)}" data-market-question="${esc(row.question)}" data-market-url="${esc(row.market_url || "")}" data-track-url="${esc(row.track_url || defaultTrackUrl(row.market_id))}" data-market-slug="${esc(row.slug || "")}" data-market-source="workspace">${esc(secondary.label)}</button>`
        : `<a class="watchlist-action" href="${esc(row.track_url || defaultTrackUrl(row.market_id))}" target="_blank" rel="noopener noreferrer" title="${esc(secondary.title)}" data-watchlist-action="${esc(secondary.action)}" data-market-id="${esc(row.market_id)}">${esc(secondary.label)}</a>`,
      row.market_url ? `<a class="watchlist-action" href="${esc(row.market_url)}" target="_blank" rel="noopener noreferrer" title="Open this market on Polymarket.">${esc(copy.openMarket)}</a>` : "",
      `<button type="button" class="watchlist-action" data-watchlist-action="remove" data-market-id="${esc(row.market_id)}">${esc(copy.remove)}</button>`,
      "</div>",
    ].join("");
  }

  function sparkSvg(row) {
    const series = Array.isArray(row.spark) ? row.spark.map((value) => Number(value)).filter((value) => Number.isFinite(value)) : [];
    if (series.length < 2) return "";
    const width = 236;
    const height = 64;
    const padX = 8;
    const padY = 6;
    const min = Math.min(...series);
    const max = Math.max(...series);
    const span = Math.max(max - min, 0.0001);
    const points = series.map((value, index) => {
      const usableWidth = width - padX * 2;
      const usableHeight = height - padY * 2;
      const x = series.length === 1 ? width / 2 : padX + (index / (series.length - 1)) * usableWidth;
      const y = height - padY - (((value - min) / span) * usableHeight);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ");
    const tone = Number(row.delta_primary || 0) < 0 ? "down" : "up";
    const area = `${padX},${height - padY} ${points} ${width - padX},${height - padY}`;
    const midY = (height / 2).toFixed(1);
    return [
      `<svg class="watchlist-spark ${tone}" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true">`,
      `<rect class="spark-frame" x="0.5" y="0.5" width="${width - 1}" height="${height - 1}" rx="10"></rect>`,
      `<line class="spark-grid" x1="${padX}" y1="${midY}" x2="${width - padX}" y2="${midY}"></line>`,
      `<polygon class="spark-area" points="${esc(area)}"></polygon>`,
      `<polyline points="${esc(points)}"></polyline>`,
      `</svg>`,
    ].join("");
  }

  function tableRow(row) {
    const sensitivity = row.effective_threshold_value != null ? sensitivityLabel(row.effective_threshold_value) : "--";
    const lastAlert = formatLastAlert(row.last_alert_at);
    return [
      "<tr>",
      `<td><p class="watchlist-question">${esc(row.question)}</p><p class="watchlist-question-meta">market ${esc(row.market_id)} · ${esc(copy[row.category] || row.category || "other")}</p>${sparkSvg(row)}</td>`,
      `<td>${esc(formatPct(row.yes_mid_now))}</td>`,
      `<td title="Current move in percentage points.">${esc(formatPp(row.delta_primary))}</td>`,
      `<td title="Fast 1 minute cue for urgency.">${esc(formatPp(row.delta_1m))}</td>`,
      `<td title="Broader 5 minute move for context.">${esc(formatPp(row.delta_5m))}</td>`,
      `<td title="Higher liquidity usually means cleaner execution.">${esc(formatLiq(row.liquidity))}</td>`,
      `<td title="Lower spread is better. Wide spread can make signals less trustworthy.">${esc(formatSpread(row.spread))}</td>`,
      `<td title="Quote freshness. Stale quotes weaken urgency.">${esc(formatFreshness(row.freshness_seconds))}</td>`,
      `<td><div class="watchlist-chip-row">${chipWithTitle(statusLabel(row.status), statusTooltip(row.status), row.status === "saved" ? "strong" : row.status === "market_closed" ? "down" : "")}</div></td>`,
      `<td><div class="watchlist-chip-row">${chipWithTitle(qualityLabel(row.signal_quality), qualityTooltip(row.signal_quality), row.signal_quality === "live_quality_gated" ? "strong" : "")}</div></td>`,
      `<td><div class="watchlist-chip-row">${chipWithTitle(alertStateLabel(row.alert_state || "off"), bellTooltip(row), row.alert_state === "on" ? "strong" : "")}</div><p class="watchlist-question-meta">${esc(lastAlert)}</p></td>`,
      `<td>${esc(sensitivity)}</td>`,
      `<td>${actionRow(row)}</td>`,
      "</tr>",
    ].join("");
  }

  function cardRow(row) {
    const alertState = String(row.alert_state || "off");
    const lastAlert = formatLastAlert(row.last_alert_at);
    return [
      '<article class="watchlist-card">',
      '<div class="watchlist-card-top">',
      `<p class="watchlist-question">${esc(row.question)}</p>`,
      `<span class="watchlist-chip${alertState === "on" ? " strong" : alertState === "paused" ? " saved" : ""}" title="${esc(bellTooltip(row))}">${esc(alertStateLabel(alertState))}</span>`,
      "</div>",
      `<p class="watchlist-question-meta">market ${esc(row.market_id)} · ${esc(copy[row.category] || row.category || "other")}</p>`,
      `<div class="watchlist-card-statband"><div class="watchlist-card-stat"><span>${esc(copy.colMid)}</span><strong>${esc(formatPct(row.yes_mid_now))}</strong></div><div class="watchlist-card-stat"><span>${esc(copy.colDelta)}</span><strong>${esc(formatPp(row.delta_primary))}</strong></div><div class="watchlist-card-stat"><span>${esc(copy.colFreshness)}</span><strong>${esc(formatFreshness(row.freshness_seconds))}</strong></div></div>`,
      sparkSvg(row),
      `<div class="watchlist-chip-row">${chipWithTitle(formatPp(row.delta_1m), "1 minute cue for urgency.", "")}${chipWithTitle(formatPp(row.delta_5m), "5 minute move for context.", "")}${chipWithTitle(`${formatLiq(row.liquidity)} ${copy.liqUnit}`, "Higher liquidity usually means cleaner execution.", "")}${chipWithTitle(`${formatSpread(row.spread)} ${copy.spreadUnit}`, "Lower spread is better.", "")}${chipWithTitle(statusLabel(row.status), statusTooltip(row.status), row.status === "saved" ? "strong" : "")}${chipWithTitle(qualityLabel(row.signal_quality), qualityTooltip(row.signal_quality), row.signal_quality === "live_quality_gated" ? "strong" : "")}${chipWithTitle(row.effective_threshold_value != null ? sensitivityLabel(row.effective_threshold_value) : "--", "Current bell threshold for this market.", "")}${chipWithTitle(lastAlert, "Last alert for this row.", "")}</div>`,
      actionRow(row),
      "</article>",
    ].join("");
  }

  function workspaceSummary(rows) {
    const total = rows.length;
    const bellOn = rows.filter((row) => String(row.alert_state || "off") === "on").length;
    const paused = rows.filter((row) => String(row.alert_state || "off") === "paused").length;
    const pending = rows.filter((row) => String(row.status || "") === "pending").length;
    const thirdLabel = SESSION.loggedIn ? copy.summaryPaused : copy.summaryPending;
    const thirdValue = SESSION.loggedIn ? paused : pending;
    return [
      '<section class="watchlist-summary">',
      `<article class="watchlist-summary-card"><strong>${esc(String(total))}</strong><span>${esc(copy.summarySaved)}</span></article>`,
      `<article class="watchlist-summary-card"><strong>${esc(String(bellOn))}</strong><span>${esc(copy.summaryBellOn)}</span></article>`,
      `<article class="watchlist-summary-card"><strong>${esc(String(thirdValue))}</strong><span>${esc(thirdLabel)}</span></article>`,
      "</section>",
    ].join("");
  }

  function renderWorkspace(root, rows) {
    const filtered = rows.filter((row) => {
      const query = VIEW_STATE.query.trim().toLowerCase();
      if (query && !String(row.question || "").toLowerCase().includes(query)) return false;
      if (VIEW_STATE.category !== "all" && row.category !== VIEW_STATE.category) return false;
      if (VIEW_STATE.status !== "all" && row.status !== VIEW_STATE.status) return false;
      if (VIEW_STATE.alertState !== "all" && String(row.alert_state || "off") !== VIEW_STATE.alertState) return false;
      return true;
    }).sort((a, b) => {
      if (VIEW_STATE.sort === "saved_at") return String(b.saved_at || "").localeCompare(String(a.saved_at || ""));
      if (VIEW_STATE.sort === "delta") return Math.abs(Number(b.delta_primary || 0)) - Math.abs(Number(a.delta_primary || 0));
      if (VIEW_STATE.sort === "liquidity") return Number(b.liquidity || -1) - Number(a.liquidity || -1);
      if (VIEW_STATE.sort === "spread") return Number(a.spread || 999) - Number(b.spread || 999);
      if (VIEW_STATE.sort === "freshness") return Number(a.freshness_seconds || 999999) - Number(b.freshness_seconds || 999999);
      return 0;
    });

    const pendingLocal = pendingCount();
    const banner = !SESSION.loggedIn ? [
      '<section class="watchlist-banner">',
      `<h3>${esc(pendingLocal ? copy.pendingBannerTitle : copy.loginBannerTitle)}</h3>`,
      `<p>${esc(pendingLocal ? copy.pendingBannerCopy : copy.loginBannerCopy)}</p>`,
      '<div class="watchlist-banner-actions">',
      `<a class="watchlist-action primary" href="${DEFAULT_TELEGRAM_URL}" target="_blank" rel="noopener noreferrer" data-watchlist-auth="login" data-watchlist-return="/watchlist">${esc(copy.openBot)}</a>`,
      "</div>",
      "</section>",
    ].join("") : "";
    const flash = FLASH.title ? [
      `<section class="watchlist-banner success">`,
      `<h3>${esc(FLASH.title)}</h3>`,
      `<p>${esc(FLASH.copy)}</p>`,
      `</section>`,
    ].join("") : "";

    const controls = [
      '<section class="watchlist-controls">',
      `<input id="watchlist-search" class="watchlist-input" type="search" value="${esc(VIEW_STATE.query)}" placeholder="${esc(copy.search)}" />`,
      `<select id="watchlist-category" class="watchlist-select">${optionHtml([[copy.all, "all"], [copy.politics, "politics"], [copy.macro, "macro"], [copy.crypto, "crypto"], [copy.other, "other"]], VIEW_STATE.category)}</select>`,
      `<select id="watchlist-status" class="watchlist-select">${optionHtml([[copy.all, "all"], [copy.savedState, "saved"], [copy.pendingSaved, "pending"], [copy.belowThreshold, "below_threshold"], [copy.marketClosed, "market_closed"], [copy.staleQuotes, "stale_quotes"], [copy.noQuotes, "no_quotes"], [copy.filteredSpread, "filtered_by_spread"], [copy.filteredLiquidity, "filtered_by_liquidity"]], VIEW_STATE.status)}</select>`,
      `<select id="watchlist-alert-state" class="watchlist-select">${optionHtml([[copy.all, "all"], [copy.alertsOff, "off"], [copy.alertOn, "on"], [copy.alertPaused, "paused"], [copy.loginRequired, "login_required"]], VIEW_STATE.alertState)}</select>`,
      `<select id="watchlist-sort" class="watchlist-select">${optionHtml([[copy.sortSaved, "saved_at"], [copy.sortDelta, "delta"], [copy.sortLiquidity, "liquidity"], [copy.sortSpread, "spread"], [copy.sortFreshness, "freshness"]], VIEW_STATE.sort)}</select>`,
      `<button id="watchlist-compact-toggle" class="watchlist-view-btn" type="button">${esc(VIEW_STATE.compact ? copy.full : copy.compact)}</button>`,
      "</section>",
    ].join("");

    const tableRows = filtered.map((row) => tableRow(row)).join("");
    const cardRows = filtered.map((row) => cardRow(row)).join("");
    const noMatchBlock = renderEmptyBlock(copy.filteredEmptyTitle, copy.filteredEmptyCopy, "");
    root.className = "watchlist-root";
    root.innerHTML = [
      flash,
      banner,
      workspaceSummary(rows),
      controls,
      '<section class="watchlist-table-wrap">',
      `<table class="watchlist-table${VIEW_STATE.compact ? " compact" : ""}">`,
      "<thead><tr>",
      `<th>${esc(copy.colMarket)}</th>`,
      `<th>${esc(copy.colMid)}</th>`,
      `<th>${esc(copy.colDelta)}</th>`,
      `<th>${esc(copy.col1m)}</th>`,
      `<th>${esc(copy.col5m)}</th>`,
      `<th>${esc(copy.colLiquidity)}</th>`,
      `<th>${esc(copy.colSpread)}</th>`,
      `<th>${esc(copy.colFreshness)}</th>`,
      `<th>${esc(copy.colStatus)}</th>`,
      `<th>${esc(copy.colQuality)}</th>`,
      `<th>${esc(copy.colAlert)}</th>`,
      `<th>${esc(copy.colSensitivity)}</th>`,
      `<th>${esc(copy.colActions)}</th>`,
      "</tr></thead>",
      `<tbody>${tableRows || `<tr><td colspan="13">${noMatchBlock}</td></tr>`}</tbody>`,
      "</table>",
      "</section>",
      `<section class="watchlist-card-grid">${cardRows || `<div class="watchlist-card"><h3>${esc(copy.filteredEmptyTitle)}</h3><p>${esc(copy.filteredEmptyCopy)}</p></div>`}</section>`,
    ].join("");
    syncWatchlistButtons(root);
  }

  async function refreshWorkspace(options) {
    const settings = options && typeof options === "object" ? options : {};
    const root = document.querySelector("[data-watchlist-workspace]");
    if (root) {
      root.className = "watchlist-root";
      root.innerHTML = `<section class="watchlist-banner"><h3>${esc(copy.loadingTitle)}</h3><p>${esc(copy.loadingCopy)}</p></section>`;
    }
    try {
      if (!settings.skipLoad) await loadWorkspaceRows();
      if (!root) {
        syncWatchlistButtons(document);
        return;
      }
      const rows = currentRows();
      if (!rows.length) {
        root.className = "watchlist-root";
        root.innerHTML = renderEmptyBlock(
          copy.emptyTitle,
          copy.emptyCopy,
          [
            '<div class="watchlist-banner-actions">',
            `<a class="watchlist-action primary" href="/top-movers">${esc(copy.openMovers)}</a>`,
            `<a class="watchlist-action" href="${DEFAULT_TELEGRAM_URL}" target="_blank" rel="noopener noreferrer" data-watchlist-auth="login" data-watchlist-return="/watchlist">${esc(copy.openBot)}</a>`,
            "</div>",
          ].join("")
        );
        return;
      }
      renderWorkspace(root, rows);
    } catch (_) {
      if (root) {
        root.innerHTML = renderEmptyBlock(
          copy.unavailableTitle,
          copy.unavailableCopy,
          [
            '<div class="watchlist-banner-actions">',
            `<a class="watchlist-action primary" href="/top-movers">${esc(copy.openMovers)}</a>`,
            `<a class="watchlist-action" href="${DEFAULT_TELEGRAM_URL}" target="_blank" rel="noopener noreferrer">${esc(copy.openBot)}</a>`,
            "</div>",
          ].join("")
        );
      }
    }
  }

  async function saveMarketServer(market, options) {
    await jsonFetch("/api/watchlist/save", {
      method: "POST",
      body: JSON.stringify({
        market_id: market.market_id,
        question: market.question || null,
        slug: market.slug || null,
        source: "site",
      }),
    });
    if (options && options.track === false) return;
    const watchlistState = options && options.watchlistState ? String(options.watchlistState) : "saved";
    trackEvent("watchlist_add", baseEventDetails({ market_id: market.market_id, question: market.question, slug: market.slug || "", watchlist_state: watchlistState }));
    trackEvent("watchlist_add_success", baseEventDetails({ market_id: market.market_id, question: market.question, slug: market.slug || "", watchlist_state: watchlistState }));
  }

  async function removeMarketServer(marketId) {
    await jsonFetch("/api/watchlist/remove", {
      method: "POST",
      body: JSON.stringify({ market_id: marketId, source: "site" }),
    });
    trackEvent("watchlist_remove", baseEventDetails({ market_id: marketId, watchlist_state: "removed" }));
  }

  async function updateAlertStateServer(marketId, desiredState) {
    const data = await jsonFetch("/api/watchlist/alert-state", {
      method: "POST",
      body: JSON.stringify({ market_id: marketId, desired_state: desiredState, source: "site" }),
    });
    SERVER_ROWS = Array.isArray(data.rows) ? data.rows : SERVER_ROWS;
    clearSyncedPending();
    return data;
  }

  async function handleAuthClick(anchor) {
    const returnPath = anchor.getAttribute("data-watchlist-return") || `${window.location.pathname}${window.location.search}`;
    const telegramUrl = await startAuthFlow("login", { market_id: null, question: "", return_path: returnPath });
    trackEvent("telegram_login_click", baseEventDetails({ intent: "login", watchlist_state: "logged_out" }));
    showBridgePrompt(null, telegramUrl, "login");
  }

  document.addEventListener("click", async (event) => {
    const authLink = event.target instanceof Element ? event.target.closest("[data-watchlist-auth]") : null;
    if (authLink) {
      event.preventDefault();
      try {
        await handleAuthClick(authLink);
      } catch (_) {
        window.open(DEFAULT_TELEGRAM_URL, "_blank", "noopener,noreferrer");
      }
      return;
    }

    const target = event.target instanceof Element ? event.target.closest("[data-watchlist-action]") : null;
    if (!target) return;
    const action = target.getAttribute("data-watchlist-action") || "";

    if (action === "toggle_save") {
      const market = marketFromElement(target);
      if (!market.market_id) return;
      const currentSaveState = watchlistStateForMarket(market.market_id);
      if (currentSaveState === "saved") {
        window.location.href = "/watchlist";
        return;
      }
      if (currentSaveState === "pending") {
        try {
          const telegramUrl = await startAuthFlow("watchlist_add", market);
          trackEvent("telegram_login_click", baseEventDetails({ intent: "watchlist_add", market_id: market.market_id, slug: market.slug || "", watchlist_state: "pending" }));
          showBridgePrompt(market, telegramUrl, "watchlist_add");
        } catch (_) {
          showBridgePrompt(market, defaultTrackUrl(market.market_id), "watchlist_add");
        }
        return;
      }
      trackEvent("watchlist_add_click", baseEventDetails({ market_id: market.market_id, question: market.question, slug: market.slug || "", watchlist_state: "new" }));
      if (!SESSION.loggedIn) {
        savePendingMarket(market);
        trackEvent("watchlist_add_success", baseEventDetails({ market_id: market.market_id, question: market.question, slug: market.slug || "", watchlist_state: "pending" }));
        syncWatchlistButtons(document);
        refreshWorkspace();
        try {
          const telegramUrl = await startAuthFlow("watchlist_add", market);
          trackEvent("telegram_login_click", baseEventDetails({ intent: "watchlist_add", market_id: market.market_id, slug: market.slug || "", watchlist_state: "pending" }));
          showBridgePrompt(market, telegramUrl, "watchlist_add");
        } catch (_) {
          showBridgePrompt(market, defaultTrackUrl(market.market_id), "watchlist_add");
        }
        return;
      }
      await saveMarketServer(market);
      await refreshWorkspace();
      syncWatchlistButtons(document);
      return;
    }

    const marketId = String(target.getAttribute("data-market-id") || "");
    const market = marketFromElement(target);
    if (!market.market_id && marketId) market.market_id = marketId;
    if (!market.question) {
      const existing = rowForMarket(marketId) || {};
      market.question = existing.question || "";
      market.market_url = market.market_url || existing.market_url || "";
      market.track_url = market.track_url || existing.track_url || defaultTrackUrl(marketId);
      market.slug = market.slug || existing.slug || "";
    }
    if (!marketId) return;

    if (action === "remove") {
      if (SESSION.loggedIn) {
        await removeMarketServer(marketId);
      } else {
        clearPendingMarket(marketId);
      }
      await refreshWorkspace();
      syncWatchlistButtons(document);
      return;
    }

    if (action === "pause_alert" || action === "resume_alert" || action === "off_alert") {
      if (!SESSION.loggedIn) return;
      const desiredState = action === "pause_alert" ? "paused" : action === "resume_alert" ? "on" : "off";
      await updateAlertStateServer(marketId, desiredState);
      trackEvent("watchlist_alert_state_change", baseEventDetails({ market_id: marketId, slug: market.slug || "", desired_state: desiredState, watchlist_state: "saved" }));
      if (desiredState === "paused") {
        setFlash(copy.pauseSuccessTitle, copy.pauseSuccessCopy, "success");
      } else if (desiredState === "on") {
        setFlash(copy.resumeSuccessTitle, copy.resumeSuccessCopy, "success");
      } else {
        setFlash(copy.offSuccessTitle, copy.offSuccessCopy, "success");
      }
      await refreshWorkspace({ skipLoad: true });
      syncWatchlistButtons(document);
      return;
    }

    if (action === "toggle_alert" || action === "configure_telegram") {
      const currentRow = rowForMarket(marketId) || {};
      trackEvent("watchlist_alert_toggle", baseEventDetails({ market_id: marketId, slug: market.slug || "", alert_state: String(currentRow.alert_state || "off") }));
      trackEvent("bell_click", baseEventDetails({ market_id: marketId, slug: market.slug || "", alert_state: String(currentRow.alert_state || "off"), watchlist_state: isSaved(marketId) ? "saved" : "pending" }));
      try {
        const telegramUrl = await startAuthFlow("alert", market);
        trackEvent("telegram_login_click", baseEventDetails({ intent: "alert", market_id: marketId, slug: market.slug || "", alert_state: String(currentRow.alert_state || "off") }));
        showBridgePrompt(market, telegramUrl, "alert");
      } catch (_) {
        showBridgePrompt(market, defaultTrackUrl(marketId), "alert");
      }
      return;
    }
  });

  document.addEventListener("change", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    if (target.id === "watchlist-category") VIEW_STATE.category = target.value;
    if (target.id === "watchlist-status") VIEW_STATE.status = target.value;
    if (target.id === "watchlist-alert-state") VIEW_STATE.alertState = target.value;
    if (target.id === "watchlist-sort") VIEW_STATE.sort = target.value;
    if (String(target.id || "").startsWith("watchlist-")) refreshWorkspace();
  });

  document.addEventListener("input", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    if (target.id === "watchlist-search") {
      VIEW_STATE.query = target.value || "";
      refreshWorkspace();
    }
  });

  document.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    if (target.id === "watchlist-compact-toggle") {
      VIEW_STATE.compact = !VIEW_STATE.compact;
      refreshWorkspace();
    }
  });

  window.addEventListener("storage", async () => {
    await loadSession();
    if (SESSION.loggedIn) await syncPendingToServerWithOptions({ silent: true });
    syncSessionCopy();
    syncWatchlistButtons(document);
    refreshWorkspace();
  });

  window.addEventListener("pulse:watchlist-sync", () => {
    syncWatchlistButtons(document);
    refreshWorkspace();
  });

  document.addEventListener("DOMContentLoaded", async () => {
    const root = document.querySelector("[data-watchlist-workspace]");
    if (root) {
      root.className = "watchlist-root";
      root.innerHTML = `<section class="watchlist-banner"><h3>${esc(copy.loadingTitle)}</h3><p>${esc(copy.loadingCopy)}</p></section>`;
    }
    await loadSession();
    let syncedCount = 0;
    if (SESSION.loggedIn) syncedCount = await syncPendingToServerWithOptions({ silent: true });
    if (window.location.search.includes("tg_auth=1") && SESSION.loggedIn) {
      if (syncedCount > 0) {
        setFlash(copy.syncSuccessTitle, copy.syncSuccessCopy, "success");
      } else {
        setFlash(copy.loginSuccessTitle, copy.loginSuccessCopy, "success");
      }
    }
    syncSessionCopy();
    await refreshWorkspace({ skipLoad: syncedCount > 0 && SERVER_ROWS.length > 0 });
    syncWatchlistButtons(document);
    try {
      const qs = new URLSearchParams(window.location.search);
      if (qs.get("from") === "alert") {
        trackEvent("alert_click_back_to_site", baseEventDetails({ placement: "watchlist_alert_return" }));
      }
    } catch (_) {}
    if (window.location.search.includes("tg_auth=1")) {
      trackEvent("watchlist_auth_complete", baseEventDetails({ placement: pagePlacement() }));
      try {
        const url = new URL(window.location.href);
        url.searchParams.delete("tg_auth");
        window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
      } catch (_) {}
    }
  });
})();
