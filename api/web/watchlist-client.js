(function () {
  const STORAGE_KEY = "pulse_watchlist_v1";
  const DEFAULT_SENSITIVITY = 0.03;
  const TELEGRAM_BOT_URL = "https://t.me/polymarket_pulse_bot?start=email_backup";
  const LOCALE = document.documentElement.lang === "ru" ? "ru" : "en";
  const TEXT = {
    en: {
      add: "Add to watchlist",
      saved: "Saved",
      watchlist: "Watchlist",
      emptyTitle: "No saved markets yet.",
      emptyCopy: "Start from Live Movers or Signals, save one market, then shape your watchlist here.",
      openMovers: "Open Live Movers",
      openBot: "Open Telegram Bot",
      loginTitle: "Log in with Telegram to save your watchlist.",
      loginCopy: "Your selected market stays in this browser for now. Open Telegram to persist identity, alert behavior, and the return loop.",
      keepLocal: "Keep local only",
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
      colAlert: "Alert state",
      colSensitivity: "Sensitivity",
      colActions: "Actions",
      openMarket: "Open market",
      remove: "Remove",
      enableAlerts: "Enable alerts",
      pauseAlerts: "Pause alerts",
      turnOffAlerts: "Turn off",
      resumeAlerts: "Resume alerts",
      configureTelegram: "Configure in Telegram",
      loginRequired: "Telegram login required",
      alertsOff: "Alerts off",
      alertOn: "Alert on",
      alertPaused: "Alert paused",
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
      loginBannerTitle: "Telegram is still the identity and alert layer.",
      loginBannerCopy: "Use the website to save and compare markets. Use Telegram to persist alert behavior cleanly.",
      statusUnknown: "Unknown",
    },
    ru: {
      add: "Add to watchlist",
      saved: "Saved",
      watchlist: "Watchlist",
      emptyTitle: "Сохранённых рынков пока нет.",
      emptyCopy: "Начните с Live Movers или Signals, сохраните один рынок и затем собирайте workspace здесь.",
      openMovers: "Открыть Live Movers",
      openBot: "Открыть Telegram-бота",
      loginTitle: "Войдите через Telegram, чтобы сохранить watchlist.",
      loginCopy: "Выбранный рынок пока останется в этом браузере. Откройте Telegram, чтобы закрепить identity, alert-поведение и return loop.",
      keepLocal: "Оставить локально",
      search: "Поиск рынков",
      category: "Категория",
      status: "Статус",
      alertState: "Alert state",
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
      colAlert: "Alert state",
      colSensitivity: "Sensitivity",
      colActions: "Действия",
      openMarket: "Открыть рынок",
      remove: "Удалить",
      enableAlerts: "Enable alerts",
      pauseAlerts: "Pause alerts",
      turnOffAlerts: "Turn off",
      resumeAlerts: "Resume alerts",
      configureTelegram: "Configure in Telegram",
      loginRequired: "Telegram login required",
      alertsOff: "Alerts off",
      alertOn: "Alert on",
      alertPaused: "Alert paused",
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
      loginBannerTitle: "Telegram пока остаётся identity и alert-слоем.",
      loginBannerCopy: "Сайт нужен, чтобы сохранять и сравнивать рынки. Telegram нужен, чтобы чисто закреплять alert-поведение.",
      statusUnknown: "Unknown",
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
        version: 1,
        telegramLinked: Boolean(parsed.telegramLinked),
        pendingContext: parsed.pendingContext || null,
        items: parsed.items && typeof parsed.items === "object" ? parsed.items : {},
      };
    } catch (_) {
      return { version: 1, telegramLinked: false, pendingContext: null, items: {} };
    }
  }

  function writeState(state) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function nowIso() {
    return new Date().toISOString();
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
      if (typeof window.gtag === "function") {
        window.gtag("event", eventType, payload.details);
      }
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

  function sensitivityLabel(value) {
    const num = Number(value);
    if (!Number.isFinite(num)) return "--";
    return `${(num * 100).toFixed(1)}${copy.sensitivityShort}`;
  }

  function localItems(state) {
    return Object.values(state.items || {}).sort((a, b) => String(b.saved_at || "").localeCompare(String(a.saved_at || "")));
  }

  function isSaved(marketId) {
    return Boolean(readState().items[String(marketId || "")]);
  }

  function defaultTrackUrl(marketId) {
    const safe = String(marketId || "").replace(/[^a-zA-Z0-9_-]/g, "").slice(0, 48);
    return safe ? `https://t.me/polymarket_pulse_bot?start=site_track_${safe}` : TELEGRAM_BOT_URL;
  }

  function upsertItem(market) {
    const state = readState();
    const marketId = String(market.market_id || "");
    if (!marketId) return null;
    const prev = state.items[marketId] || {};
    const next = {
      market_id: marketId,
      question: market.question || marketId,
      slug: market.slug || "",
      market_url: market.market_url || prev.market_url || "",
      track_url: market.track_url || prev.track_url || defaultTrackUrl(marketId),
      source: market.source || prev.source || "site",
      saved_at: prev.saved_at || nowIso(),
      alert_state: prev.alert_state || "off",
      sensitivity: Number.isFinite(Number(prev.sensitivity)) ? Number(prev.sensitivity) : DEFAULT_SENSITIVITY,
    };
    state.items[marketId] = next;
    writeState(state);
    return next;
  }

  function removeItem(marketId) {
    const state = readState();
    delete state.items[String(marketId || "")];
    writeState(state);
  }

  function updateItem(marketId, patch) {
    const state = readState();
    const current = state.items[String(marketId || "")];
    if (!current) return null;
    state.items[String(marketId || "")] = Object.assign({}, current, patch);
    writeState(state);
    return state.items[String(marketId || "")];
  }

  function deriveAlertLabel(item, statusCode) {
    const alertState = item.alert_state || "off";
    if (alertState === "on") return copy.alertOn;
    if (alertState === "paused") return copy.alertPaused;
    if (statusCode === "alert_limit_reached") return "Alert limit reached";
    return copy.loginRequired;
  }

  function deriveStatusCode(row, item) {
    const base = String(row.status || "saved");
    if ((item.alert_state === "on" || item.alert_state === "paused") && Number.isFinite(Number(row.delta_primary)) && Math.abs(Number(row.delta_primary)) < Number(item.sensitivity || DEFAULT_SENSITIVITY) && base === "saved") {
      return "below_threshold";
    }
    return base;
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
    }[code] || copy.statusUnknown;
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

  function syncWatchlistButtons(root) {
    const scope = root || document;
    scope.querySelectorAll('[data-watchlist-action="toggle_save"]').forEach((button) => {
      const marketId = String(button.getAttribute("data-market-id") || "");
      const saved = isSaved(marketId);
      button.classList.toggle("saved", saved);
      button.setAttribute("aria-pressed", saved ? "true" : "false");
      button.textContent = saved ? copy.saved : copy.add;
    });
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
      `<h3>${esc(copy.loginTitle)}</h3>`,
      `<p id="watchlist-login-market"></p>`,
      `<p>${esc(copy.loginCopy)}</p>`,
      '<div class="watchlist-login-actions">',
      `<a id="watchlist-login-open" class="watchlist-login-btn" target="_blank" rel="noopener noreferrer" href="${TELEGRAM_BOT_URL}">${esc(copy.openBot)}</a>`,
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

  function showLoginPrompt(market, intent) {
    ensurePromptUi();
    const prompt = document.getElementById("watchlist-login-prompt");
    const marketEl = document.getElementById("watchlist-login-market");
    const openEl = document.getElementById("watchlist-login-open");
    const state = readState();
    state.pendingContext = {
      intent: intent || "watchlist",
      market_id: market.market_id || "",
      question: market.question || "",
      track_url: market.track_url || defaultTrackUrl(market.market_id),
      ts: nowIso(),
    };
    writeState(state);
    marketEl.textContent = market.question ? `${copy.watchlist}: ${market.question}` : "";
    openEl.href = market.track_url || defaultTrackUrl(market.market_id);
    prompt.classList.add("open");
    trackEvent("watchlist_prompt_open", {
      placement: window.location.pathname,
      intent: intent || "watchlist",
      market_id: market.market_id || "",
    });
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

  function renderWorkspace(root, rows) {
    const state = readState();
    const savedItems = localItems(state);
    const rowMap = new Map(rows.map((row) => [String(row.market_id), row]));
    const merged = savedItems.map((item) => {
      const row = Object.assign({}, rowMap.get(String(item.market_id)) || {});
      return {
        market_id: item.market_id,
        question: row.question || item.question || item.market_id,
        market_url: row.market_url || item.market_url || "",
        track_url: row.track_url || item.track_url || defaultTrackUrl(item.market_id),
        category: row.category || "other",
        status: deriveStatusCode(row, item),
        market_status: row.market_status || "unknown",
        signal_quality: row.signal_quality || "legacy_fallback",
        yes_mid_now: row.yes_mid_now,
        delta_primary: row.delta_primary,
        delta_1m: row.delta_1m,
        delta_5m: row.delta_5m,
        liquidity: row.liquidity,
        spread: row.spread,
        freshness_seconds: row.freshness_seconds,
        quote_ts: row.quote_ts,
        alert_state: item.alert_state || "off",
        sensitivity: Number(item.sensitivity || DEFAULT_SENSITIVITY),
        saved_at: item.saved_at || nowIso(),
      };
    });

    const filtered = merged.filter((row) => {
      const query = VIEW_STATE.query.trim().toLowerCase();
      if (query && !String(row.question || "").toLowerCase().includes(query)) return false;
      if (VIEW_STATE.category !== "all" && row.category !== VIEW_STATE.category) return false;
      if (VIEW_STATE.status !== "all" && row.status !== VIEW_STATE.status) return false;
      if (VIEW_STATE.alertState !== "all" && row.alert_state !== VIEW_STATE.alertState) return false;
      return true;
    }).sort((a, b) => {
      if (VIEW_STATE.sort === "saved_at") return String(b.saved_at || "").localeCompare(String(a.saved_at || ""));
      if (VIEW_STATE.sort === "delta") return Math.abs(Number(b.delta_primary || 0)) - Math.abs(Number(a.delta_primary || 0));
      if (VIEW_STATE.sort === "liquidity") return Number(b.liquidity || -1) - Number(a.liquidity || -1);
      if (VIEW_STATE.sort === "spread") return Number(a.spread || 999) - Number(b.spread || 999);
      if (VIEW_STATE.sort === "freshness") return Number(a.freshness_seconds || 999999) - Number(b.freshness_seconds || 999999);
      return 0;
    });

    const banner = !state.telegramLinked ? [
      '<section class="watchlist-banner">',
      `<h3>${esc(copy.loginBannerTitle)}</h3>`,
      `<p>${esc(copy.loginBannerCopy)}</p>`,
      '<div class="watchlist-banner-actions">',
      `<a class="watchlist-action primary" href="${TELEGRAM_BOT_URL}" target="_blank" rel="noopener noreferrer">${esc(copy.openBot)}</a>`,
      "</div>",
      "</section>",
    ].join("") : "";

    const controls = [
      '<section class="watchlist-controls">',
      `<input id="watchlist-search" class="watchlist-input" type="search" value="${esc(VIEW_STATE.query)}" placeholder="${esc(copy.search)}" />`,
      `<select id="watchlist-category" class="watchlist-select">${optionHtml([[copy.all, "all"], [copy.politics, "politics"], [copy.macro, "macro"], [copy.crypto, "crypto"], [copy.other, "other"]], VIEW_STATE.category)}</select>`,
      `<select id="watchlist-status" class="watchlist-select">${optionHtml([[copy.all, "all"], [copy.savedState, "saved"], [copy.belowThreshold, "below_threshold"], [copy.marketClosed, "market_closed"], [copy.staleQuotes, "stale_quotes"], [copy.noQuotes, "no_quotes"], [copy.filteredSpread, "filtered_by_spread"], [copy.filteredLiquidity, "filtered_by_liquidity"]], VIEW_STATE.status)}</select>`,
      `<select id="watchlist-alert-state" class="watchlist-select">${optionHtml([[copy.all, "all"], [copy.alertsOff, "off"], [copy.alertOn, "on"], [copy.alertPaused, "paused"]], VIEW_STATE.alertState)}</select>`,
      `<select id="watchlist-sort" class="watchlist-select">${optionHtml([[copy.sortSaved, "saved_at"], [copy.sortDelta, "delta"], [copy.sortLiquidity, "liquidity"], [copy.sortSpread, "spread"], [copy.sortFreshness, "freshness"]], VIEW_STATE.sort)}</select>`,
      `<button id="watchlist-compact-toggle" class="watchlist-view-btn" type="button">${esc(VIEW_STATE.compact ? copy.full : copy.compact)}</button>`,
      "</section>",
    ].join("");

    const tableRows = filtered.map((row) => tableRow(row)).join("");
    const cardRows = filtered.map((row) => cardRow(row)).join("");
    root.className = "watchlist-root";
    root.innerHTML = [
      banner,
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
      `<tbody>${tableRows || `<tr><td colspan="13">${esc(copy.emptyCopy)}</td></tr>`}</tbody>`,
      "</table>",
      "</section>",
      `<section class="watchlist-card-grid">${cardRows || `<div class="watchlist-card"><p>${esc(copy.emptyCopy)}</p></div>`}</section>`,
    ].join("");
  }

  function optionHtml(entries, selected) {
    return entries.map((entry) => {
      const label = entry[0];
      const value = entry[1];
      const sel = value === selected ? " selected" : "";
      return `<option value="${esc(value)}"${sel}>${esc(label)}</option>`;
    }).join("");
  }

  function tableRow(row) {
    const alertLabel = deriveAlertLabel(row, row.status);
    return [
      "<tr>",
      `<td><p class="watchlist-question">${esc(row.question)}</p><p class="watchlist-question-meta">market ${esc(row.market_id)} · ${esc(copy[row.category] || row.category)}</p></td>`,
      `<td>${esc(formatPct(row.yes_mid_now))}</td>`,
      `<td>${esc(formatPp(row.delta_primary))}</td>`,
      `<td>${esc(formatPp(row.delta_1m))}</td>`,
      `<td>${esc(formatPp(row.delta_5m))}</td>`,
      `<td>${esc(formatLiq(row.liquidity))}</td>`,
      `<td>${esc(formatSpread(row.spread))}</td>`,
      `<td>${esc(formatFreshness(row.freshness_seconds))}</td>`,
      `<td><div class="watchlist-chip-row">${chip(statusLabel(row.status), row.status === "saved" ? "strong" : row.status === "market_closed" ? "down" : "")}</div></td>`,
      `<td><div class="watchlist-chip-row">${chip(qualityLabel(row.signal_quality), row.signal_quality === "live_quality_gated" ? "strong" : "")}</div></td>`,
      `<td><div class="watchlist-chip-row">${chip(alertLabel, row.alert_state === "on" ? "strong" : "")}</div></td>`,
      `<td>${esc(row.alert_state === "off" ? "--" : sensitivityLabel(row.sensitivity))}</td>`,
      `<td>${actionRow(row)}</td>`,
      "</tr>",
    ].join("");
  }

  function cardRow(row) {
    return [
      '<article class="watchlist-card">',
      '<div class="watchlist-card-top">',
      `<p class="watchlist-question">${esc(row.question)}</p>`,
      `<span class="watchlist-chip${row.alert_state === "on" ? " strong" : ""}">${esc(deriveAlertLabel(row, row.status))}</span>`,
      "</div>",
      `<p class="watchlist-question-meta">market ${esc(row.market_id)} · ${esc(copy[row.category] || row.category)}</p>`,
      `<div class="watchlist-chip-row">${chip(formatPct(row.yes_mid_now), "strong")}${chip(formatPp(row.delta_primary), Number(row.delta_primary || 0) < 0 ? "down" : "")}${chip(formatPp(row.delta_1m), "")}${chip(formatPp(row.delta_5m), "")}</div>`,
      `<div class="watchlist-chip-row">${chip(`${formatLiq(row.liquidity)} ${copy.liqUnit}`, "")}${chip(`${formatSpread(row.spread)} ${copy.spreadUnit}`, "")}${chip(`${formatFreshness(row.freshness_seconds)} ${copy.quote}`, "")}</div>`,
      `<div class="watchlist-chip-row">${chip(statusLabel(row.status), row.status === "saved" ? "strong" : "")}${chip(qualityLabel(row.signal_quality), row.signal_quality === "live_quality_gated" ? "strong" : "")}${chip(row.alert_state === "off" ? "--" : sensitivityLabel(row.sensitivity), "")}</div>`,
      actionRow(row),
      "</article>",
    ].join("");
  }

  function chip(label, extraClass) {
    return `<span class="watchlist-chip${extraClass ? ` ${extraClass}` : ""}">${esc(label)}</span>`;
  }

  function actionRow(row) {
    const toggleText = row.alert_state === "off"
      ? copy.enableAlerts
      : row.alert_state === "on"
        ? copy.pauseAlerts
        : copy.turnOffAlerts;
    const sensitivityOptions = [0.01, 0.03, 0.05, 0.08].map((value) => {
      const selected = Math.abs(Number(row.sensitivity || DEFAULT_SENSITIVITY) - value) < 1e-9 ? " selected" : "";
      return `<option value="${value}"${selected}>${esc(sensitivityLabel(value))}</option>`;
    }).join("");
    return [
      '<div class="watchlist-action-row">',
      row.market_url ? `<a class="watchlist-action" href="${esc(row.market_url)}" target="_blank" rel="noopener noreferrer">${esc(copy.openMarket)}</a>` : "",
      `<button type="button" class="watchlist-action" data-watchlist-action="toggle_alert" data-market-id="${esc(row.market_id)}">${esc(toggleText)}</button>`,
      `<select class="watchlist-action" data-watchlist-action="set_sensitivity" data-market-id="${esc(row.market_id)}">${sensitivityOptions}</select>`,
      `<a class="watchlist-action primary" href="${esc(row.track_url)}" target="_blank" rel="noopener noreferrer" data-watchlist-action="configure_telegram" data-market-id="${esc(row.market_id)}">${esc(copy.configureTelegram)}</a>`,
      `<button type="button" class="watchlist-action" data-watchlist-action="remove" data-market-id="${esc(row.market_id)}">${esc(copy.remove)}</button>`,
      "</div>",
    ].join("");
  }

  async function refreshWorkspace() {
    const root = document.querySelector("[data-watchlist-workspace]");
    if (!root) return;
    const state = readState();
    const items = localItems(state);
    if (!items.length) {
      root.className = "watchlist-root";
      root.innerHTML = [
        '<section class="watchlist-empty">',
        `<h3>${esc(copy.emptyTitle)}</h3>`,
        `<p>${esc(copy.emptyCopy)}</p>`,
        '<div class="watchlist-banner-actions">',
        `<a class="watchlist-action" href="/top-movers">${esc(copy.openMovers)}</a>`,
        `<a class="watchlist-action primary" href="${TELEGRAM_BOT_URL}" target="_blank" rel="noopener noreferrer">${esc(copy.openBot)}</a>`,
        "</div>",
        "</section>",
      ].join("");
      return;
    }
    root.className = "watchlist-root";
    root.innerHTML = `<section class="watchlist-banner"><h3>${esc(copy.watchlist)}</h3><p>${esc(copy.search)}...</p></section>`;
    const ids = items.map((item) => item.market_id).join(",");
    try {
      const res = await fetch(`/api/watchlist-workspace?market_ids=${encodeURIComponent(ids)}`, { cache: "no-store" });
      const data = await res.json();
      renderWorkspace(root, Array.isArray(data.rows) ? data.rows : []);
    } catch (_) {
      root.innerHTML = `<section class="watchlist-empty"><h3>${esc(copy.watchlist)}</h3><p>${esc(copy.statusUnknown)}</p></section>`;
    }
  }

  document.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target.closest("[data-watchlist-action]") : null;
    if (!target) return;
    const action = target.getAttribute("data-watchlist-action") || "";

    if (action === "toggle_save") {
      const market = marketFromElement(target);
      if (!market.market_id) return;
      if (isSaved(market.market_id)) {
        window.location.href = "/watchlist";
        return;
      }
      upsertItem(market);
      syncWatchlistButtons(document);
      refreshWorkspace();
      trackEvent("watchlist_add", { market_id: market.market_id, question: market.question, placement: window.location.pathname });
      if (!readState().telegramLinked) {
        showLoginPrompt(market, "watchlist_add");
      }
      return;
    }

    const marketId = String(target.getAttribute("data-market-id") || "");
    if (!marketId) return;

    if (action === "remove") {
      removeItem(marketId);
      syncWatchlistButtons(document);
      refreshWorkspace();
      trackEvent("watchlist_remove", { market_id: marketId, placement: window.location.pathname });
      return;
    }

    if (action === "toggle_alert") {
      const state = readState();
      const item = state.items[marketId];
      if (!item) return;
      const next = item.alert_state === "off" ? "on" : item.alert_state === "on" ? "paused" : "off";
      updateItem(marketId, { alert_state: next });
      refreshWorkspace();
      trackEvent("watchlist_alert_toggle", { market_id: marketId, alert_state: next, placement: window.location.pathname });
      if (!state.telegramLinked) {
        showLoginPrompt(item, "alert_toggle");
      }
      return;
    }

    if (action === "configure_telegram") {
      trackEvent("tg_click", { market_id: marketId, placement: "watchlist_configure_telegram" });
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
    if (target.matches('[data-watchlist-action="set_sensitivity"]')) {
      const marketId = String(target.getAttribute("data-market-id") || "");
      const nextValue = Number(target.value || DEFAULT_SENSITIVITY);
      updateItem(marketId, { sensitivity: nextValue });
      refreshWorkspace();
      trackEvent("watchlist_sensitivity_change", { market_id: marketId, sensitivity: nextValue, placement: window.location.pathname });
      if (!readState().telegramLinked) {
        const item = readState().items[marketId];
        if (item) showLoginPrompt(item, "sensitivity_change");
      }
      return;
    }
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

  window.addEventListener("storage", () => {
    syncWatchlistButtons(document);
    refreshWorkspace();
  });

  window.addEventListener("pulse:watchlist-sync", () => {
    syncWatchlistButtons(document);
    refreshWorkspace();
  });

  document.addEventListener("DOMContentLoaded", () => {
    syncWatchlistButtons(document);
    refreshWorkspace();
  });
})();
