(function () {
  "use strict";

  var THEME_KEY = "new-project-theme";
  var root = document.documentElement;
  var toggle = document.getElementById("theme-toggle");

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    if (toggle) {
      toggle.setAttribute("aria-pressed", String(theme === "dark"));
    }
  }

  function initTheme() {
    var saved = null;
    try {
      saved = localStorage.getItem(THEME_KEY);
    } catch (e) {
      saved = null;
    }

    if (saved === "light" || saved === "dark") {
      applyTheme(saved);
      return;
    }

    var prefersDark =
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches;
    applyTheme(prefersDark ? "dark" : "light");
  }

  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      applyTheme(next);
      try {
        localStorage.setItem(THEME_KEY, next);
      } catch (e) {
        /* ignore storage errors */
      }
    });
  }

  initTheme();

  // Lead form validation + fake submit
  var form = document.getElementById("lead-form");
  if (form) {
    var email = document.getElementById("email");
    var error = document.getElementById("email-error");
    var status = document.getElementById("form-status");

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var value = (email.value || "").trim();
      var valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);

      if (!valid) {
        email.setAttribute("aria-invalid", "true");
        if (error) error.hidden = false;
        email.focus();
        return;
      }

      email.removeAttribute("aria-invalid");
      if (error) error.hidden = true;
      if (status) {
        status.textContent = "Спасибо! Мы свяжемся с вами по адресу " + value + ".";
      }
      form.reset();
    });

    if (email) {
      email.addEventListener("input", function () {
        if (email.getAttribute("aria-invalid") === "true") {
          email.removeAttribute("aria-invalid");
          if (error) error.hidden = true;
        }
      });
    }
  }
})();
