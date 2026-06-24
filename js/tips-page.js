(function () {
  const { escapeHtml, renderVideo, formatDuration } = window.ZKMediaUtils;

  const CATEGORY_PARAM = "category";

  const state = {
    category: "",
  };

  function tipHref(id) {
    return `tips.html?id=${encodeURIComponent(id)}`;
  }

  function listHref(category) {
    const url = new URL("tips.html", window.location.href);
    url.searchParams.delete("id");
    if (category) {
      url.searchParams.set(CATEGORY_PARAM, category);
    } else {
      url.searchParams.delete(CATEGORY_PARAM);
    }
    return `${url.pathname}${url.search}`;
  }

  function matchesFilters(tip) {
    if (state.category && tip.category !== state.category) return false;
    return true;
  }

  function readCategoryFromUrl() {
    const val = new URLSearchParams(window.location.search).get(CATEGORY_PARAM) || "";
    return getTipCategories().includes(val) ? val : "";
  }

  function syncCategoryToUrl() {
    const url = new URL(window.location.href);
    if (url.searchParams.has("id")) return;
    if (state.category) {
      url.searchParams.set(CATEGORY_PARAM, state.category);
    } else {
      url.searchParams.delete(CATEGORY_PARAM);
    }
    history.replaceState(null, "", url);
  }

  function updateFilterStatus(count) {
    const el = document.getElementById("tips-filter-status");
    if (!el) return;
    const total = EXPERT_TIPS.length;
    if (state.category) {
      el.textContent = `Показано ${count} из ${total}`;
    } else {
      el.textContent = `Все советы: ${count}`;
    }
  }

  function setActiveChips(container) {
    container.querySelectorAll(".chip[data-value]").forEach((chip) => {
      const chipValue = chip.getAttribute("data-value") || "";
      const isActive = state.category === chipValue;
      chip.classList.toggle("chip--active", isActive);
      chip.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
  }

  function renderTipCard(tip, options) {
    const compact = options && options.compact;
    const duration = formatDuration(tip.durationSec);
    const durationHtml = duration
      ? `<span class="tip-card__duration" aria-label="Длительность ${escapeHtml(duration)}">${escapeHtml(duration)}</span>`
      : "";
    return `
      <a class="tip-card${compact ? " tip-card--compact" : ""}" href="${tipHref(tip.id)}" aria-label="Смотреть: ${escapeHtml(tip.title)}">
        <div class="tip-card__media">
          <img src="${escapeHtml(tip.cover)}" alt="" width="404" height="720" loading="lazy" decoding="async" />
          <span class="tip-card__play" aria-hidden="true"></span>
          ${durationHtml}
        </div>
        <div class="tip-card__body">
          <span class="tip-card__category">${escapeHtml(tip.category)}</span>
          <h3 class="tip-card__title">${escapeHtml(tip.title)}</h3>
          ${compact ? "" : `<p class="tip-card__summary">${escapeHtml(tip.summary)}</p>`}
        </div>
      </a>
    `;
  }

  function renderRelatedTips(current) {
    const related = EXPERT_TIPS.filter((t) => t.category === current.category && t.id !== current.id).slice(
      0,
      3
    );
    if (!related.length) return "";
    return `
      <section class="section">
        <h2>Похожие советы</h2>
        <div class="tip-grid tip-grid--related">
          ${related.map((t) => renderTipCard(t, { compact: true })).join("")}
        </div>
      </section>
    `;
  }

  function renderDetail(tip) {
    const videoHtml = tip.video ? renderVideo(tip.video, { label: tip.title }) : "";
    const categoryLink = listHref(tip.category);
    return `
      <div class="container tip-detail">
        <nav class="tip-breadcrumbs" aria-label="Навигация">
          <a href="${listHref("")}">Все советы</a>
          <span aria-hidden="true">/</span>
          <a href="${categoryLink}">${escapeHtml(tip.category)}</a>
        </nav>
        <h1>${escapeHtml(tip.title)}</h1>
        ${videoHtml}
        <p class="lead">${escapeHtml(tip.summary)}</p>
        <p class="tip-detail__actions">
          <a class="btn btn--primary" href="https://zakomfortom.com/" target="_blank" rel="noopener noreferrer">Обсудить ремонт</a>
          <a class="btn btn--ghost" href="${listHref("")}">Все советы</a>
        </p>
      </div>
      <div class="container">
        ${renderRelatedTips(tip)}
      </div>
    `;
  }

  function renderList(root) {
    const filtered = EXPERT_TIPS.filter(matchesFilters);
    const chipsHost = document.getElementById("tips-filter-chips");

    if (chipsHost && !chipsHost.dataset.bound) {
      chipsHost.dataset.bound = "1";
      const categories = getTipCategories();
      chipsHost.innerHTML = [
        `<button type="button" class="chip chip--active" data-value="" aria-pressed="true">Все</button>`,
        ...categories.map(
          (c) =>
            `<button type="button" class="chip" data-value="${escapeHtml(c)}" aria-pressed="false">${escapeHtml(c)}</button>`
        ),
      ].join("");
      chipsHost.addEventListener("click", (e) => {
        const chip = e.target.closest(".chip[data-value]");
        if (!chip) return;
        state.category = chip.getAttribute("data-value") || "";
        setActiveChips(chipsHost);
        applyList(root);
      });
    }

    setActiveChips(chipsHost);

    const grid = document.getElementById("tips-grid");
    if (!grid) return;

    if (!filtered.length) {
      grid.innerHTML =
        '<p class="empty-state">Нет советов по выбранной теме. Выберите другую категорию.</p>';
    } else {
      grid.innerHTML = filtered.map((t) => renderTipCard(t)).join("");
    }
    updateFilterStatus(filtered.length);
    syncCategoryToUrl();
  }

  function applyList(root) {
    renderList(root);
  }

  function setDetailMeta(tip) {
    const PUBLIC_SITE = "https://katalog.zakomfortom.com/";
    document.title = `${tip.title} · Советы эксперта · За Комфортом`;

    const setMeta = (selector, content) => {
      const el = document.querySelector(selector);
      if (el && content) el.setAttribute("content", content);
    };

    const canonical = document.querySelector('link[rel="canonical"]');
    if (canonical) {
      canonical.href = `${PUBLIC_SITE.replace(/\/$/, "")}/tips.html?id=${encodeURIComponent(tip.id)}`;
    }

    setMeta('meta[name="description"]', tip.summary);
    setMeta('meta[property="og:title"]', tip.title);
    setMeta('meta[property="og:description"]', tip.summary);
    try {
      const img = new URL(tip.cover.replace(/^\//, ""), PUBLIC_SITE).href;
      setMeta('meta[property="og:image"]', img);
      setMeta('meta[name="twitter:image"]', img);
    } catch {
      /* ignore */
    }
    setMeta(
      'meta[property="og:url"]',
      `${PUBLIC_SITE.replace(/\/$/, "")}/tips.html?id=${encodeURIComponent(tip.id)}`
    );
    setMeta('meta[name="twitter:title"]', tip.title);
    setMeta('meta[name="twitter:description"]', tip.summary);
  }

  document.addEventListener("DOMContentLoaded", () => {
    const root = document.getElementById("tips-root");
    if (!root || typeof EXPERT_TIPS === "undefined") return;

    const params = new URLSearchParams(window.location.search);
    const id = params.get("id");

    if (id) {
      const tip = getTipById(id);
      if (!tip) {
        root.innerHTML =
          '<div class="container section"><p>Совет не найден. <a href="tips.html">К списку советов</a></p></div>';
        return;
      }
      setDetailMeta(tip);
      root.innerHTML = renderDetail(tip);
      if (window.ZKMediaGuard) {
        window.ZKMediaGuard.protect(root);
      }
      return;
    }

    state.category = readCategoryFromUrl();
    root.innerHTML = `
      <div class="container page-flow">
        <header class="hero">
          <h1>Советы эксперта</h1>
          <p class="lead">
            Короткие видео о ремонте и дизайне от студии «За Комфортом»: практичные решения без лишней теории.
          </p>
          <p><a class="btn btn--primary" href="https://zakomfortom.com/" target="_blank" rel="noopener noreferrer">Рассчитать ремонт</a></p>
        </header>
        <section class="filters tips-filters" aria-label="Фильтр советов">
          <div class="filter-row filter-row--complex">
            <span class="filter-label">Тема</span>
            <div id="tips-filter-chips" class="filter-complex-chips"></div>
          </div>
          <p id="tips-filter-status" class="filter-status" aria-live="polite"></p>
        </section>
        <div id="tips-grid" class="tip-grid" aria-live="polite"></div>
      </div>
    `;
    renderList(root);
  });
})();
