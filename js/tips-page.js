(function () {
  const { escapeHtml, formatDuration } = window.ZKMediaUtils;

  const CATEGORY_PARAM = "category";

  const state = {
    category: "",
  };

  function tipHref(id) {
    // Статические страницы советов генерирует scripts/build-pages.py.
    return `tips/${encodeURIComponent(id)}/`;
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

  function renderTipCard(tip) {
    const duration = formatDuration(tip.durationSec);
    const durationHtml = duration
      ? `<span class="tip-card__duration" aria-label="Длительность ${escapeHtml(duration)}">${escapeHtml(duration)}</span>`
      : "";
    return `
      <a class="tip-card" href="${tipHref(tip.id)}" aria-label="Смотреть: ${escapeHtml(tip.title)}">
        <div class="tip-card__media">
          <img src="${escapeHtml(tip.cover)}" alt="" width="404" height="720" loading="lazy" decoding="async" />
          <span class="tip-card__play" aria-hidden="true"></span>
          ${durationHtml}
        </div>
        <div class="tip-card__body">
          <span class="tip-card__category">${escapeHtml(tip.category)}</span>
          <h3 class="tip-card__title">${escapeHtml(tip.title)}</h3>
          <p class="tip-card__summary">${escapeHtml(tip.summary)}</p>
        </div>
      </a>
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

  document.addEventListener("DOMContentLoaded", () => {
    const root = document.getElementById("tips-root");
    if (!root || typeof EXPERT_TIPS === "undefined") return;

    const params = new URLSearchParams(window.location.search);
    const id = params.get("id");

    if (id) {
      // Старый формат tips.html?id=<slug> редиректит на статические страницы.
      if (getTipById(id)) {
        window.location.replace(tipHref(id));
        return;
      }
      root.innerHTML =
        '<div class="container section"><p>Совет не найден. <a href="tips.html">К списку советов</a></p></div>';
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
