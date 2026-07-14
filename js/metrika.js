(function () {
  const config = window.ZK_CONFIG || {};
  const counterId = config.metrikaId;

  // Счётчик подключается только когда в content/site.json задан metrikaId.
  if (counterId) {
    (function (m, e, t, r, i, k, a) {
      m[i] =
        m[i] ||
        function () {
          (m[i].a = m[i].a || []).push(arguments);
        };
      m[i].l = 1 * new Date();
      (k = e.createElement(t)), (a = e.getElementsByTagName(t)[0]);
      k.async = 1;
      k.src = r;
      a.parentNode.insertBefore(k, a);
    })(window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");

    window.ym(counterId, "init", {
      clickmap: true,
      trackLinks: true,
      accurateTrackBounce: true,
      webvisor: false,
    });
  }

  function goalFor(href) {
    if (!href) return null;
    if (href.startsWith("tel:")) return "cta_call";
    if (href.includes("wa.me")) return "cta_whatsapp";
    if (href.includes("t.me")) return "cta_telegram";
    if (href.includes("max.ru")) return "cta_max";
    if (href.includes("vk.com")) return "cta_vk";
    if (href.includes("design-project")) return "cta_quiz";
    if (href.includes("zakomfortom.com")) return "cta_calc";
    return null;
  }

  document.addEventListener(
    "click",
    (e) => {
      const link = e.target.closest("a[href]");
      if (!link) return;
      const goal = goalFor(link.getAttribute("href") || "");
      if (!goal) return;
      if (counterId && typeof window.ym === "function") {
        window.ym(counterId, "reachGoal", goal);
      }
    },
    true
  );
})();
