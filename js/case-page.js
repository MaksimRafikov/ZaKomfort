/* Прогрессивное улучшение статических страниц кейсов (cases/<slug>/index.html):
   лайтбокс с листанием стрелками, клавиатурой и свайпом. Разметка страницы
   генерируется scripts/build-pages.py, этот скрипт данных не рендерит. */
(function () {
  const ARROW_SVG = {
    prev: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="15 18 9 12 15 6"></polyline></svg>',
    next: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9 18 15 12 9 6"></polyline></svg>',
  };

  function fullSizeSrc(img) {
    // Базовый src в <img> — это полноразмерный JPEG 1440px; currentSrc может
    // указывать на уменьшенный вариант из srcset.
    return img.getAttribute("src") || img.currentSrc || "";
  }

  function createLightbox() {
    const overlay = document.createElement("div");
    overlay.id = "case-lightbox";
    overlay.className = "lightbox";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "Фото в полном размере");
    overlay.hidden = true;
    overlay.innerHTML =
      '<button type="button" class="lightbox__close" aria-label="Закрыть">&times;</button>' +
      `<button type="button" class="lightbox__nav lightbox__nav--prev" aria-label="Предыдущее фото">${ARROW_SVG.prev}</button>` +
      '<img class="lightbox__img" alt="" />' +
      `<button type="button" class="lightbox__nav lightbox__nav--next" aria-label="Следующее фото">${ARROW_SVG.next}</button>` +
      '<p class="lightbox__counter" aria-live="polite"></p>';
    document.body.appendChild(overlay);
    return overlay;
  }

  function initLightbox(root) {
    const images = Array.from(root.querySelectorAll(".gallery img, .case-hero__img"));
    if (!images.length) return;

    const overlay = createLightbox();
    const imgEl = overlay.querySelector(".lightbox__img");
    const counterEl = overlay.querySelector(".lightbox__counter");
    const closeBtn = overlay.querySelector(".lightbox__close");
    const prevBtn = overlay.querySelector(".lightbox__nav--prev");
    const nextBtn = overlay.querySelector(".lightbox__nav--next");

    let index = 0;
    let lastFocused = null;

    function show(i) {
      index = (i + images.length) % images.length;
      const img = images[index];
      imgEl.src = fullSizeSrc(img);
      imgEl.alt = img.getAttribute("alt") || "";
      counterEl.textContent = images.length > 1 ? `${index + 1} / ${images.length}` : "";
      const showNav = images.length > 1;
      prevBtn.hidden = !showNav;
      nextBtn.hidden = !showNav;
    }

    function open(i) {
      lastFocused = document.activeElement;
      show(i);
      overlay.hidden = false;
      document.body.style.overflow = "hidden";
      closeBtn.focus();
    }

    function close() {
      overlay.hidden = true;
      imgEl.removeAttribute("src");
      document.body.style.overflow = "";
      if (lastFocused && typeof lastFocused.focus === "function") lastFocused.focus();
      lastFocused = null;
    }

    closeBtn.addEventListener("click", close);
    prevBtn.addEventListener("click", () => show(index - 1));
    nextBtn.addEventListener("click", () => show(index + 1));
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) close();
    });

    document.addEventListener("keydown", (e) => {
      if (overlay.hidden) return;
      if (e.key === "Escape") close();
      else if (e.key === "ArrowLeft") show(index - 1);
      else if (e.key === "ArrowRight") show(index + 1);
    });

    let touchStartX = null;
    let touchStartY = null;
    overlay.addEventListener(
      "touchstart",
      (e) => {
        if (e.touches.length !== 1) return;
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
      },
      { passive: true }
    );
    overlay.addEventListener(
      "touchend",
      (e) => {
        if (touchStartX === null) return;
        const dx = e.changedTouches[0].clientX - touchStartX;
        const dy = e.changedTouches[0].clientY - touchStartY;
        touchStartX = null;
        touchStartY = null;
        if (Math.abs(dx) < 45 || Math.abs(dx) < Math.abs(dy)) return;
        show(dx > 0 ? index - 1 : index + 1);
      },
      { passive: true }
    );

    images.forEach((img, i) => {
      img.style.cursor = "zoom-in";
      if (!img.hasAttribute("tabindex")) img.setAttribute("tabindex", "0");
      img.addEventListener("click", () => open(i));
      img.addEventListener("keydown", (e) => {
        if (e.key !== "Enter" && e.key !== " ") return;
        e.preventDefault();
        open(i);
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    const root = document.getElementById("case-root");
    if (!root) return;
    initLightbox(root);
  });
})();
