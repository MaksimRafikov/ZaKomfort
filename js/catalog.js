(function () {
  const COMPLEX_PARAM = "complex";

  const state = {
    complex: "",
  };

  function matchesFilters(c) {
    if (state.complex && c.complex !== state.complex) return false;
    return true;
  }

  function readComplexFromUrl() {
    const val = new URLSearchParams(window.location.search).get(COMPLEX_PARAM) || "";
    return getComplexes().includes(val) ? val : "";
  }

  function syncComplexToUrl() {
    const url = new URL(window.location.href);
    if (state.complex) {
      url.searchParams.set(COMPLEX_PARAM, state.complex);
    } else {
      url.searchParams.delete(COMPLEX_PARAM);
    }
    history.replaceState(null, "", url);
  }

  function updateFilterStatus(count) {
    const el = document.getElementById("filter-status");
    if (!el) return;

    const total = CASES.length;
    if (state.complex) {
      el.textContent = `Показано ${count} из ${total}: ${state.complex}`;
    } else {
      el.textContent = `Все объекты: ${count}`;
    }
  }

  function setActiveChip(complexRow, value) {
    complexRow.querySelectorAll(".chip[data-value]").forEach((chip) => {
      const chipValue = chip.getAttribute("data-value") || "";
      const isActive = state.complex === chipValue;
      chip.classList.toggle("chip--active", isActive);
      chip.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
  }

  function applyFilters() {
    const list = CASES.filter(matchesFilters);
    renderCards(list);
    updateFilterStatus(list.length);
    syncComplexToUrl();
  }

  function caseHref(id) {
    return `case.html?id=${encodeURIComponent(id)}`;
  }

  function bindCardNavigation(grid) {
    if (!grid || grid.dataset.navBound === "1") return;
    grid.dataset.navBound = "1";

    grid.addEventListener("click", (e) => {
      const card = e.target.closest("a.card, article.card[data-id]");
      if (!card) return;
      if (e.button !== 0) return;
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;

      const href =
        card.tagName === "A" && card.href
          ? card.href
          : caseHref(card.getAttribute("data-id") || "");

      const innerLink = e.target.closest("a[href]");
      if (innerLink && innerLink !== card) return;

      if (card.tagName === "A") return;

      e.preventDefault();
      window.location.assign(href);
    });
  }

  function renderCards(list) {
    const grid = document.getElementById("case-grid");
    if (!grid) return;

    if (!list.length) {
      grid.innerHTML =
        '<p class="empty-state">Нет кейсов по выбранному ЖК. Выберите «Все ЖК» или другой комплекс.</p>';
      return;
    }

    grid.innerHTML = list
      .map(
        (c) => `
      <a class="card" href="${caseHref(c.id)}" data-id="${escapeHtml(c.id)}" aria-label="Смотреть кейс: ${escapeHtml(c.title)}">
        <div class="card__media">
          <img src="${escapeHtml(c.cover)}" alt="${escapeHtml(c.title)} — интерьер после ремонта" width="600" height="450" loading="lazy" decoding="async" />
        </div>
        <div class="card__body">
          <h3 class="card__title">${escapeHtml(c.title)}</h3>
          <p class="card__meta">${escapeHtml(c.areaLabel)} · ${escapeHtml(c.format)}</p>
          <p class="card__summary">${escapeHtml(c.summary)}</p>
          <div class="tags" aria-label="Теги">
            ${c.tags
              .slice(0, 4)
              .map((t) => `<span class="tag">${escapeHtml(t)}</span>`)
              .join("")}
          </div>
          <span class="btn btn--primary">Смотреть кейс</span>
        </div>
      </a>
    `
      )
      .join("");

    bindCardNavigation(grid);
    if (window.ZKMediaGuard) {
      window.ZKMediaGuard.protect(grid);
    }
  }

  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  function initFilters() {
    state.complex = readComplexFromUrl();

    const complexes = getComplexes();
    const complexRow = document.getElementById("filter-complex");
    if (complexRow) {
      complexRow.innerHTML =
        '<button type="button" class="chip" data-value="" aria-pressed="false">Все ЖК</button>' +
        complexes
          .map(
            (x) =>
              `<button type="button" class="chip" data-value="${escapeHtml(x)}" aria-pressed="false">${escapeHtml(x)}</button>`
          )
          .join("");

      setActiveChip(complexRow, state.complex);

      complexRow.querySelectorAll(".chip[data-value]").forEach((chip) => {
        chip.addEventListener("click", () => {
          state.complex = chip.getAttribute("data-value") || "";
          setActiveChip(complexRow, state.complex);
          applyFilters();
        });
      });
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    initFilters();
    applyFilters();
  });
})();
