/* Минимальная защита медиа: блокировка контекстного меню и перетаскивания
   для фото/видео кейсов (кроме брендовых из assets/brand/). Водяных знаков
   и наложенных «щитов» нет — делегирование на уровне документа. */
(function () {
  function isBrandMedia(el) {
    const src = el.currentSrc || el.src || el.getAttribute("poster") || "";
    return src.includes("assets/brand/");
  }

  function isProtectedMedia(el) {
    if (!(el instanceof HTMLImageElement || el instanceof HTMLVideoElement)) return false;
    return !isBrandMedia(el);
  }

  function block(e) {
    const media = e.target.closest("img, video");
    if (media && isProtectedMedia(media)) {
      e.preventDefault();
    }
  }

  document.addEventListener("contextmenu", block, true);
  document.addEventListener("dragstart", block, true);
})();
