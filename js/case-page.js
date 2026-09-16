/* Прогрессивное улучшение статических страниц кейсов (cases/<slug>/index.html):
   лайтбокс со стрелками, клавиатурой, свайпом, focus trap, swipe-down,
   pinch/pan для плана. Разметка страницы генерируется scripts/build-pages.py. */
(function () {
  const ARROW_SVG = {
    prev: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="15 18 9 12 15 6"></polyline></svg>',
    next: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9 18 15 12 9 6"></polyline></svg>',
  };

  const OPEN_CHIP_SVG =
    '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linecap="square" aria-hidden="true"><path d="M2 6V2h4M14 6V2h-4M2 10v4h4M14 10v4h-4"></path></svg>';

  const FOCUSABLE_SELECTOR =
    'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

  const SWIPE_X = 56;
  const DISMISS_Y = 96;
  const MIN_SCALE = 1;
  const MAX_SCALE = 4;
  const PINCH_EPS = 0.02;

  function fullSizeSrc(img) {
    // Базовый src в <img> — это полноразмерный JPEG 1440px; currentSrc может
    // указывать на уменьшенный вариант из srcset.
    return img.getAttribute("src") || img.currentSrc || "";
  }

  function isPlanImage(img) {
    const src = (img.getAttribute("src") || img.currentSrc || "").toLowerCase();
    return /(?:^|\/)plan(?:[-.]|$)/.test(src) || /plan\.(?:png|jpe?g|webp)/.test(src);
  }

  function isVisible(el) {
    return el.getClientRects().length > 0;
  }

  function distance(a, b) {
    return Math.hypot(a.x - b.x, a.y - b.y);
  }

  function midpoint(a, b) {
    return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
  }

  function touchPoint(touch) {
    return { x: touch.clientX, y: touch.clientY };
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
      '<p class="lightbox__hint sr-only">Свайп влево или вправо — листать, вниз — закрыть. На плане: щипок — увеличить.</p>' +
      '<button type="button" class="lightbox__close" aria-label="Закрыть">&times;</button>' +
      `<button type="button" class="lightbox__nav lightbox__nav--prev" aria-label="Предыдущее фото">${ARROW_SVG.prev}</button>` +
      '<div class="lightbox__stage">' +
      '<img class="lightbox__img" alt="" draggable="false" />' +
      "</div>" +
      `<button type="button" class="lightbox__nav lightbox__nav--next" aria-label="Следующее фото">${ARROW_SVG.next}</button>` +
      '<p class="lightbox__counter" aria-live="polite"></p>';
    document.body.appendChild(overlay);
    return overlay;
  }

  function attachOpenChip(host, label) {
    if (!host || host.querySelector(".media-open")) return;
    const chip = document.createElement("span");
    chip.className = "media-open";
    chip.setAttribute("aria-hidden", "true");
    chip.innerHTML = OPEN_CHIP_SVG + `<span class="media-open__label">${label}</span>`;
    host.appendChild(chip);
  }

  function initLightbox(root) {
    const images = Array.from(root.querySelectorAll(".gallery img, .case-hero__img"));
    if (!images.length) return;

    const overlay = createLightbox();
    const stageEl = overlay.querySelector(".lightbox__stage");
    const imgEl = overlay.querySelector(".lightbox__img");
    const counterEl = overlay.querySelector(".lightbox__counter");
    const closeBtn = overlay.querySelector(".lightbox__close");
    const prevBtn = overlay.querySelector(".lightbox__nav--prev");
    const nextBtn = overlay.querySelector(".lightbox__nav--next");

    let index = 0;
    let lastFocused = null;
    let allowPinch = false;

    const transform = { scale: 1, x: 0, y: 0, dragging: false };
    let mode = "none";
    let start = null;
    let origin = { scale: 1, x: 0, y: 0 };
    let pinchStartDist = 1;
    let pinchMid = { x: 0, y: 0 };
    let axisLock = null;

    function applyTransform() {
      const { scale, x, y, dragging } = transform;
      stageEl.style.transform = `translate3d(${x}px, ${y}px, 0) scale(${scale})`;
      stageEl.style.transition = dragging ? "none" : "transform 180ms ease-out";
      const zoomed = scale > MIN_SCALE + PINCH_EPS;
      overlay.classList.toggle("lightbox--zoomed", zoomed);
      const opacity =
        zoomed ? 1 : Math.max(0.35, 1 - Math.abs(y) / 280);
      overlay.style.setProperty("--lightbox-bg-opacity", String(0.92 * opacity));
    }

    function resetZoom() {
      mode = "none";
      start = null;
      axisLock = null;
      transform.scale = 1;
      transform.x = 0;
      transform.y = 0;
      transform.dragging = false;
      applyTransform();
    }

    function focusables() {
      return Array.from(overlay.querySelectorAll(FOCUSABLE_SELECTOR)).filter(
        (el) => isVisible(el) && !el.hidden
      );
    }

    function updateNavVisibility() {
      const showNav = images.length > 1 && transform.scale <= MIN_SCALE + PINCH_EPS;
      prevBtn.hidden = !showNav;
      nextBtn.hidden = !showNav;
    }

    function show(i) {
      index = (i + images.length) % images.length;
      const img = images[index];
      imgEl.src = fullSizeSrc(img);
      imgEl.alt = img.getAttribute("alt") || "";
      counterEl.textContent = images.length > 1 ? `${index + 1} / ${images.length}` : "";
      allowPinch = isPlanImage(img);
      overlay.classList.toggle("lightbox--plan", allowPinch);
      resetZoom();
      updateNavVisibility();
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
      resetZoom();
      overlay.style.removeProperty("--lightbox-bg-opacity");
      if (lastFocused && typeof lastFocused.focus === "function") lastFocused.focus();
      lastFocused = null;
    }

    function goPrev() {
      show(index - 1);
    }

    function goNext() {
      show(index + 1);
    }

    closeBtn.addEventListener("click", close);
    prevBtn.addEventListener("click", goPrev);
    nextBtn.addEventListener("click", goNext);
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay && transform.scale <= MIN_SCALE + PINCH_EPS) close();
    });

    document.addEventListener("keydown", (e) => {
      if (overlay.hidden) return;
      if (e.key === "Escape") {
        close();
        return;
      }
      if (e.key === "ArrowLeft") {
        goPrev();
        return;
      }
      if (e.key === "ArrowRight") {
        goNext();
        return;
      }
      if (e.key !== "Tab") return;

      const items = focusables();
      if (!items.length) {
        e.preventDefault();
        return;
      }
      const first = items[0];
      const last = items[items.length - 1];
      const active = document.activeElement;

      if (e.shiftKey) {
        if (active === first || !overlay.contains(active)) {
          e.preventDefault();
          last.focus();
        }
        return;
      }
      if (active === last || !overlay.contains(active)) {
        e.preventDefault();
        first.focus();
      }
    });

    overlay.addEventListener(
      "touchstart",
      (e) => {
        const touches = e.touches;
        if (touches.length === 2 && allowPinch) {
          e.preventDefault();
          const a = touchPoint(touches[0]);
          const b = touchPoint(touches[1]);
          mode = "pinch";
          pinchStartDist = Math.max(distance(a, b), 1);
          pinchMid = midpoint(a, b);
          origin = { scale: transform.scale, x: transform.x, y: transform.y };
          transform.dragging = true;
          applyTransform();
          return;
        }

        if (touches.length !== 1) return;

        const point = touchPoint(touches[0]);
        start = point;
        axisLock = null;
        origin = { scale: transform.scale, x: transform.x, y: transform.y };

        if (allowPinch && transform.scale > MIN_SCALE + PINCH_EPS) {
          mode = "pan";
          transform.dragging = true;
          applyTransform();
        } else {
          mode = "swipe";
        }
      },
      { passive: false }
    );

    overlay.addEventListener(
      "touchmove",
      (e) => {
        const touches = e.touches;

        if (mode === "pinch" && touches.length === 2 && allowPinch) {
          e.preventDefault();
          const a = touchPoint(touches[0]);
          const b = touchPoint(touches[1]);
          const dist = Math.max(distance(a, b), 1);
          const mid = midpoint(a, b);
          const nextScale = Math.min(
            MAX_SCALE,
            Math.max(MIN_SCALE, origin.scale * (dist / pinchStartDist))
          );
          const midDelta = { x: mid.x - pinchMid.x, y: mid.y - pinchMid.y };
          const scaleRatio = nextScale / Math.max(origin.scale, MIN_SCALE);
          transform.scale = nextScale;
          transform.x =
            nextScale <= MIN_SCALE + PINCH_EPS ? 0 : origin.x * scaleRatio + midDelta.x;
          transform.y =
            nextScale <= MIN_SCALE + PINCH_EPS ? 0 : origin.y * scaleRatio + midDelta.y;
          transform.dragging = true;
          applyTransform();
          updateNavVisibility();
          return;
        }

        if (touches.length !== 1 || !start) return;

        const point = touchPoint(touches[0]);
        const dx = point.x - start.x;
        const dy = point.y - start.y;

        if (mode === "pan") {
          e.preventDefault();
          transform.scale = origin.scale;
          transform.x = origin.x + dx;
          transform.y = origin.y + dy;
          transform.dragging = true;
          applyTransform();
          return;
        }

        if (mode !== "swipe") return;

        if (!axisLock) {
          if (Math.abs(dx) < 10 && Math.abs(dy) < 10) return;
          axisLock = Math.abs(dx) >= Math.abs(dy) ? "x" : "y";
          transform.dragging = true;
        }

        e.preventDefault();

        if (axisLock === "x") {
          if (images.length <= 1) {
            transform.scale = 1;
            transform.x = 0;
            transform.y = 0;
          } else {
            transform.scale = 1;
            transform.x = dx;
            transform.y = 0;
          }
          transform.dragging = true;
          applyTransform();
          return;
        }

        const dismissY = Math.max(dy, dy < 0 ? dy * 0.2 : 0);
        transform.scale = 1;
        transform.x = 0;
        transform.y = dismissY;
        transform.dragging = true;
        applyTransform();
      },
      { passive: false }
    );

    function endGesture(e) {
      const current = transform;

      if (e.touches && e.touches.length >= 2) return;

      if (e.touches && e.touches.length === 1 && mode === "pinch") {
        start = touchPoint(e.touches[0]);
        origin = { scale: current.scale, x: current.x, y: current.y };
        mode = current.scale > MIN_SCALE + PINCH_EPS ? "pan" : "swipe";
        return;
      }

      if (mode === "pinch") {
        if (current.scale <= MIN_SCALE + PINCH_EPS) {
          resetZoom();
        } else {
          transform.dragging = false;
          applyTransform();
          mode = "none";
          start = null;
        }
        updateNavVisibility();
        return;
      }

      if (mode === "pan") {
        transform.dragging = false;
        applyTransform();
        mode = "none";
        start = null;
        return;
      }

      if (mode === "swipe" && start) {
        const axis = axisLock;
        const dx = current.x;
        const dy = current.y;

        if (axis === "y" && dy >= DISMISS_Y) {
          resetZoom();
          close();
          return;
        }

        if (axis === "x" && images.length > 1) {
          if (dx <= -SWIPE_X) {
            goNext();
            return;
          }
          if (dx >= SWIPE_X) {
            goPrev();
            return;
          }
        }
      }

      resetZoom();
      updateNavVisibility();
    }

    overlay.addEventListener("touchend", endGesture);
    overlay.addEventListener("touchcancel", () => {
      resetZoom();
      updateNavVisibility();
    });

    images.forEach((img, i) => {
      img.style.cursor = "zoom-in";
      if (!img.hasAttribute("tabindex")) img.setAttribute("tabindex", "0");

      const figure = img.closest("figure");
      if (figure) {
        attachOpenChip(figure, isPlanImage(img) ? "Открыть план" : "Открыть");
      } else if (img.classList.contains("case-hero__img")) {
        const hero = img.closest(".case-hero");
        attachOpenChip(hero, "Открыть");
      }

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
