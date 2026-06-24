(function () {
  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  function videoMime(url) {
    return /\.mov$/i.test(url) ? "video/quicktime" : "video/mp4";
  }

  function renderVideo(video, options) {
    const label = (options && options.label) || video.label || "Видео";
    if (video.embedUrl) {
      return `<div class="video-block"><iframe title="${escapeHtml(label)}" src="${escapeHtml(video.embedUrl)}" allowfullscreen loading="lazy"></iframe></div>`;
    }
    if (video.fileUrl) {
      return `<div class="video-block media-guard"><video controls controlsList="nodownload noplaybackrate" disablePictureInPicture playsinline preload="none" poster="${escapeHtml(video.poster || "")}"><source src="${escapeHtml(video.fileUrl)}" type="${videoMime(video.fileUrl)}" />Ваш браузер не поддерживает видео.</video></div>`;
    }
    let inner = "";
    if (video.externalUrl) {
      inner += `<p><a class="btn btn--primary" href="${escapeHtml(video.externalUrl)}" target="_blank" rel="noopener noreferrer">Смотреть видео</a></p>`;
    }
    if (video.note) {
      inner += `<div class="video-fallback"><p>${escapeHtml(video.note)}</p></div>`;
    }
    return inner;
  }

  function formatDuration(seconds) {
    if (!seconds || seconds <= 0) return "";
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${String(s).padStart(2, "0")}`;
  }

  window.ZKMediaUtils = {
    escapeHtml,
    videoMime,
    renderVideo,
    formatDuration,
  };
})();
