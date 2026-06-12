(function () {
  const BRAND_PATH = "/assets/brand/";

  function isBrandMedia(el) {
    const src = el.currentSrc || el.src || el.getAttribute("poster") || "";
    return src.includes(BRAND_PATH) || src.includes("assets/brand/");
  }

  function isProtectedMedia(el) {
    if (!(el instanceof HTMLImageElement || el instanceof HTMLVideoElement)) return false;
    if (isBrandMedia(el)) return false;
    return true;
  }

  function blockDrag(el) {
    el.draggable = false;
    el.addEventListener("dragstart", (e) => e.preventDefault());
  }

  function protectVideos(root) {
    root.querySelectorAll("video").forEach((video) => {
      if (isBrandMedia(video)) return;
      video.setAttribute("controlsList", "nodownload noplaybackrate");
      video.setAttribute("disablePictureInPicture", "");
      video.setAttribute("oncontextmenu", "return false;");
      blockDrag(video);
    });
  }

  function protectImages(root) {
    root.querySelectorAll("img").forEach((img) => {
      if (!isProtectedMedia(img)) return;
      blockDrag(img);
      img.setAttribute("referrerpolicy", "no-referrer");
    });
  }

  function addShields(root) {
    root.querySelectorAll(".gallery figure").forEach((figure) => {
      if (figure.querySelector(".media-guard__shield")) return;
      const img = figure.querySelector("img");
      if (!img || !isProtectedMedia(img)) return;
      const shield = document.createElement("div");
      shield.className = "media-guard__shield";
      shield.setAttribute("aria-hidden", "true");
      img.insertAdjacentElement("afterend", shield);
    });

    root.querySelectorAll(".card__media").forEach((mediaWrap) => {
      if (mediaWrap.querySelector(".media-guard__shield")) return;
      const img = mediaWrap.querySelector("img");
      if (!img || !isProtectedMedia(img)) return;
      const shield = document.createElement("div");
      shield.className = "media-guard__shield";
      shield.setAttribute("aria-hidden", "true");
      img.insertAdjacentElement("afterend", shield);
    });

    const hero = root.querySelector(".case-hero");
    if (hero && !hero.querySelector(".case-hero__shield")) {
      const img = hero.querySelector(".case-hero__img");
      if (img && isProtectedMedia(img)) {
        const shield = document.createElement("div");
        shield.className = "case-hero__shield media-guard__shield";
        shield.setAttribute("aria-hidden", "true");
        img.insertAdjacentElement("afterend", shield);
      }
    }
  }

  function protectContainer(root) {
    if (!root || root.dataset.mediaGuardBound === "1") return;
    root.dataset.mediaGuardBound = "1";
    root.classList.add("media-guard");

    root.addEventListener(
      "contextmenu",
      (e) => {
        const media = e.target.closest("img, video");
        if (media && root.contains(media) && isProtectedMedia(media)) {
          e.preventDefault();
        }
      },
      true
    );

    root.addEventListener(
      "dragstart",
      (e) => {
        const media = e.target.closest("img, video");
        if (media && root.contains(media) && isProtectedMedia(media)) {
          e.preventDefault();
        }
      },
      true
    );
  }

  function protect(root) {
    if (!root) return;
    protectContainer(root);
    addShields(root);
    protectImages(root);
    protectVideos(root);
  }

  function protectDocument() {
    protect(document.body);

    document.querySelectorAll(".gallery, .case-hero, .card__media, #case-lightbox").forEach((el) => {
      protect(el);
    });
  }

  document.addEventListener(
    "contextmenu",
    (e) => {
      const media = e.target.closest("img, video");
      if (media && isProtectedMedia(media)) {
        e.preventDefault();
      }
    },
    true
  );

  document.addEventListener("keydown", (e) => {
    if (!(e.ctrlKey || e.metaKey)) return;
    if (e.key.toLowerCase() !== "s") return;
    const active = document.activeElement;
    const inLightbox = document.getElementById("case-lightbox");
    if (inLightbox && !inLightbox.hidden) {
      e.preventDefault();
    }
    if (active && active.closest(".media-guard, .gallery, .case-hero, .card__media")) {
      e.preventDefault();
    }
  });

  document.addEventListener("DOMContentLoaded", protectDocument);

  window.ZKMediaGuard = { protect, protectDocument };
})();
