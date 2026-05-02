(function () {
  const state = {
    complex: "",
    area: "",
    style: "",
    room: "",
    project: false,
    video: false,
  };

  function areaBucket(sqm) {
    if (sqm <= 40) return "до 40";
    if (sqm <= 55) return "40–55";
    if (sqm <= 80) return "55–80";
    return "80+";
  }

  function matchesFilters(c) {
    if (state.complex && c.complex !== state.complex) return false;
    if (state.area && areaBucket(c.areaSqm) !== state.area) return false;
    if (state.style && c.style !== state.style) return false;
    if (state.room && !c.rooms.includes(state.room)) return false;
    if (state.project && !c.hasProjectRender) return false;
    if (state.video && !c.hasVideo) return false;
    return true;
  }

  function renderCards(list) {
    const grid = document.getElementById("case-grid");
    if (!grid) return;

    if (!list.length) {
      grid.innerHTML =
        '<p class="empty-state">Нет кейсов по выбранным фильтрам. Сбросьте фильтры или расширьте базу в <code>js/data.js</code>.</p>';
      return;
    }

    grid.innerHTML = list
      .map(
        (c) => `
      <article class="card" data-id="${escapeHtml(c.id)}">
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
          <a class="btn btn--primary" href="case.html?id=${encodeURIComponent(c.id)}">Смотреть кейс</a>
        </div>
      </article>
    `
      )
      .join("");
  }

  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  function wireChips(containerSelector, key, getValue) {
    const row = document.querySelector(containerSelector);
    if (!row) return;
    row.querySelectorAll(".chip[data-value]").forEach((chip) => {
      chip.addEventListener("click", () => {
        const val = chip.getAttribute("data-value");
        const current = state[key];
        const next = current === val ? "" : val;
        state[key] = getValue ? getValue(next, val) : next;
        row.querySelectorAll(".chip[data-value]").forEach((c) => {
          const v = c.getAttribute("data-value");
          const active = state[key] === v;
          c.classList.toggle("chip--active", active);
        });
        renderCards(CASES.filter(matchesFilters));
      });
    });
  }

  function wireToggle(chipSelector, key) {
    const chip = document.querySelector(chipSelector);
    if (!chip) return;
    chip.addEventListener("click", () => {
      state[key] = !state[key];
      chip.classList.toggle("chip--active", state[key]);
      renderCards(CASES.filter(matchesFilters));
    });
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

    wireChips("#filter-area", "area", null);
    wireChips("#filter-style", "style", null);
    wireChips("#filter-room", "room", null);
    wireToggle("#chip-filter-project", "project");
    wireToggle("#chip-filter-video", "video");
  }

  document.addEventListener("DOMContentLoaded", () => {
    initFilters();
    renderCards(CASES.filter(matchesFilters));
  });
})();
