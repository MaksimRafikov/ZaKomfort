(function () {
  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  function getCaseById(id) {
    return CASES.find((c) => c.id === id);
  }

  function renderVideo(video) {
    if (video.embedUrl) {
      return `<div class="video-block"><iframe title="${escapeHtml(video.label)}" src="${escapeHtml(video.embedUrl)}" allowfullscreen loading="lazy"></iframe></div>`;
    }
    if (video.fileUrl) {
      return `<div class="video-block"><video controls playsinline preload="metadata" poster="${escapeHtml(video.poster || "")}"><source src="${escapeHtml(video.fileUrl)}" type="video/mp4" />Ваш браузер не поддерживает видео.</video></div>`;
    }
    let inner = "";
    if (video.externalUrl) {
      inner += `<p><a class="btn btn--primary" href="${escapeHtml(video.externalUrl)}" target="_blank" rel="noopener">Смотреть видео</a></p>`;
    }
    inner += `<div class="video-fallback"><p>${escapeHtml(video.note)}</p></div>`;
    return inner;
  }

  document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const id = params.get("id");

    const c = id ? getCaseById(id) : null;
    const root = document.getElementById("case-root");
    if (!root) return;

    if (!c) {
      root.innerHTML =
        '<div class="container section"><p>Кейс не найден. <a href="index.html">На главную</a></p></div>';
      return;
    }

    document.title = `${c.title} · ${c.areaLabel} · Каталог работ`;

    const videoHtml = c.video ? renderVideo(c.video) : "";
    const budgetHtml = c.budgetLabel
      ? `<p><strong>Стоимость ремонта:</strong> ${escapeHtml(c.budgetLabel)}</p>`
      : "";
    const workListHtml = c.workList?.length
      ? `<ul class="list-check">${c.workList.map((x) => `<li>${escapeHtml(x)}</li>`).join("")}</ul>`
      : `<p>Состав работ уточняется под конкретный объект.</p>`;
    const planHtml = c.plan
      ? `<div class="gallery"><figure><img src="${escapeHtml(c.plan.src)}" alt="${escapeHtml(c.plan.alt || "План объекта")}" width="1200" height="800" loading="lazy" /><figcaption>${escapeHtml(c.plan.caption || "")}</figcaption></figure></div>`
      : "<p>План объекта будет добавлен.</p>";
    const beforeHtml = c.beforeGallery?.length
      ? `<div class="gallery">${c.beforeGallery
          .map(
            (g) => `
              <figure>
                <img src="${escapeHtml(g.src)}" alt="${escapeHtml(g.alt)}" width="800" height="600" loading="lazy" />
                <figcaption>${escapeHtml(g.caption)}</figcaption>
              </figure>
            `
          )
          .join("")}</div>`
      : "<p>Фото до ремонта не добавлены.</p>";
    const compareHtml = c.compareGallery?.length
      ? `<div class="gallery">${c.compareGallery
          .map(
            (g) => `
              <figure>
                <img src="${escapeHtml(g.src)}" alt="${escapeHtml(g.alt)}" width="800" height="600" loading="lazy" />
                <figcaption>${escapeHtml(g.caption)}</figcaption>
              </figure>
            `
          )
          .join("")}</div>`
      : "";
    const quizAction = c.cta?.quiz
      ? `<a class="btn btn--ghost" href="${escapeHtml(c.cta.quiz)}" target="_blank" rel="noopener">${escapeHtml(c.cta.buttonLabel)}</a>`
      : `<a class="btn btn--ghost" href="tel:${escapeHtml(c.cta.phone.replace(/\s/g, ""))}">${escapeHtml(c.cta.buttonLabel)}</a>`;

    root.innerHTML = `
      <div class="case-hero">
        <img class="case-hero__img" src="${escapeHtml(c.cover)}" alt="" width="1600" height="900" />
        <div class="case-hero__content container">
          <h1>${escapeHtml(c.title)}</h1>
          <p class="case-hero__meta">${escapeHtml(c.areaLabel)} · ${escapeHtml(c.format)} · ${escapeHtml(c.style)}</p>
          <div class="case-actions">
            <a class="btn btn--primary" href="#gallery">Смотреть фото</a>
            ${quizAction}
          </div>
        </div>
      </div>

      <div class="container">
        <section class="section">
          <h2>Паспорт объекта</h2>
          <p><strong>Площадь:</strong> ${escapeHtml(c.areaLabel)} · <strong>Тип:</strong> ${escapeHtml(c.roomsLabel || "квартира")} · <strong>Формат:</strong> ${escapeHtml(c.format)} · <strong>Сегмент:</strong> ${escapeHtml(c.segment)}</p>
          ${c.address ? `<p><strong>Адрес:</strong> ${escapeHtml(c.address)}</p>` : ""}
          ${budgetHtml}
        </section>

        <section class="section">
          <h2>Задача</h2>
          <p>${escapeHtml(c.task)}</p>
        </section>

        <section class="section">
          <h2>План и описание объекта</h2>
          <p>${escapeHtml(c.objectDescription || "")}</p>
          ${planHtml}
        </section>

        <section class="section">
          <h2>Краткий список работ</h2>
          ${workListHtml}
        </section>

        <section class="section">
          <h2>Проект и реализация</h2>
          <ul class="list-check">
            ${c.highlights.map((x) => `<li>${escapeHtml(x)}</li>`).join("")}
          </ul>
        </section>

        <section class="section" id="gallery">
          <h2>Галерея</h2>
          <div class="gallery">
            ${c.gallery
              .map(
                (g) => `
              <figure>
                <img src="${escapeHtml(g.src)}" alt="${escapeHtml(g.alt)}" width="800" height="600" loading="lazy" />
                <figcaption>${escapeHtml(g.caption)}</figcaption>
              </figure>
            `
              )
              .join("")}
          </div>
        </section>

        <section class="section">
          <h2>Фото до ремонта</h2>
          ${beforeHtml}
        </section>

        ${compareHtml ? `<section class="section"><h2>Проект / реализация</h2>${compareHtml}</section>` : ""}

        ${c.video && (c.video.embedUrl || c.video.fileUrl || c.video.externalUrl) ? `<section class="section"><h2>${escapeHtml(c.video.label || "Видео")}</h2>${videoHtml}</section>` : ""}

        <section class="section">
          <h2>Кому подходит</h2>
          <ul class="list-check">
            ${c.clientFit.map((x) => `<li>${escapeHtml(x)}</li>`).join("")}
          </ul>
        </section>
      </div>

      <div class="cta-bar">
        <div class="container cta-bar__inner">
          <p>Обсудить похожий ремонт</p>
          <div class="cta-bar__actions">
            ${c.cta.quiz ? `<a class="btn btn--primary" href="${escapeHtml(c.cta.quiz)}" target="_blank" rel="noopener">Пройти квиз</a>` : `<a class="btn btn--primary" href="tel:${escapeHtml(c.cta.phone.replace(/\s/g, ""))}">Позвонить</a>`}
            <a class="btn btn--ghost" href="tel:${escapeHtml(c.cta.phone.replace(/\s/g, ""))}">Позвонить</a>
            ${c.cta.whatsapp ? `<a class="btn btn--ghost" href="${escapeHtml(c.cta.whatsapp)}" target="_blank" rel="noopener">WhatsApp</a>` : ""}
            ${c.cta.telegram ? `<a class="btn btn--ghost" href="${escapeHtml(c.cta.telegram)}" target="_blank" rel="noopener">Telegram</a>` : ""}
            ${c.cta.max ? `<a class="btn btn--ghost" href="${escapeHtml(c.cta.max)}" target="_blank" rel="noopener">Max</a>` : ""}
            ${c.cta.vk ? `<a class="btn btn--ghost" href="${escapeHtml(c.cta.vk)}" target="_blank" rel="noopener">VK</a>` : ""}
          </div>
        </div>
      </div>
    `;
  });
})();
