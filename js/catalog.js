(function () {
  const state = {
    complex: "",
  };

  function matchesFilters(c) {
    if (state.complex && c.complex !== state.complex) return false;
    return true;
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
      <a class="card" href="case.html?id=${encodeURIComponent(c.id)}" data-id="${escapeHtml(c.id)}" aria-label="Смотреть кейс: ${escapeHtml(c.title)}">
        <div class="card__media">
          <img src="${escapeHtml(c.cover)}" alt="" width="600" height="450" loading="lazy" />
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
  }

  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  function initFilters() {
    const complexes = getComplexes();
    const complexRow = document.getElementById("filter-complex");
    if (complexRow) {
      complexRow.innerHTML =
        '<button type="button" class="chip chip--active" data-value="">Все ЖК</button>' +
        complexes
          .map(
            (x) =>
              `<button type="button" class="chip" data-value="${escapeHtml(x)}">${escapeHtml(x)}</button>`
          )
          .join("");
      complexRow.querySelectorAll(".chip[data-value]").forEach((chip) => {
        chip.addEventListener("click", () => {
          const val = chip.getAttribute("data-value") || "";
          state.complex = val;
          complexRow.querySelectorAll(".chip[data-value]").forEach((c) => {
            const v = c.getAttribute("data-value") || "";
            c.classList.toggle("chip--active", state.complex === v);
          });
          renderCards(CASES.filter(matchesFilters));
        });
      });
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    initFilters();
    renderCards(CASES.filter(matchesFilters));
  });
})();
