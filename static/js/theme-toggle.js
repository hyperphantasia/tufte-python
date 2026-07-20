/**
 * Theme switcher for light/dark mode.
 * Author: Brooks for tufte-python (github.com/hyperphantasia/tufte-python)
 * 
 * Behavior:
 * - Detects system color scheme preference
 * - Respects an explicit `data-theme` value on <html>
 * - Falls back to system preference when no explicit theme is set
 * - Persists user choice in localStorage when available
 * - Keeps the theme toggle button state in sync
 *
 * Requirements:
 * - A button with id="theme-switch"
 * - The document root (<html>) may use:
 *   - data-theme="light"
 *   - data-theme="dark"
 *
 * Notes:
 * - If localStorage is unavailable, theme changes still work for the current page load.
 * - System theme changes are followed only when no explicit theme is set.
 */
(function () {
  "use strict";

  function systemPrefersDark() {
    return !!(
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    );
  }

  function explicitTheme() {
    var attr = document.documentElement.getAttribute("data-theme");
    return attr === "light" || attr === "dark" ? attr : null;
  }

  function effectiveTheme() {
    return explicitTheme() || (systemPrefersDark() ? "dark" : "light");
  }

  function setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem("theme", theme);
    } catch (e) {
      /* localStorage unavailable (private browsing etc.) -- theme just
         won't persist across visits, which is fine. */
    }
  }

  function syncSwitch(btn) {
    var isDark = effectiveTheme() === "dark";
    btn.classList.toggle("is-dark", isDark);
    btn.setAttribute("aria-pressed", String(isDark));
  }

  document.addEventListener("DOMContentLoaded", function () {
    var btn = document.getElementById("theme-switch");
    if (!btn) return;

    syncSwitch(btn);

    btn.addEventListener("click", function () {
      setTheme(effectiveTheme() === "dark" ? "light" : "dark");
      syncSwitch(btn);
    });

    // If the user hasn't made an explicit choice yet, keep the switch (and
    // the page) in sync with system theme changes made while it's open.
    if (window.matchMedia) {
      window
        .matchMedia("(prefers-color-scheme: dark)")
        .addEventListener("change", function () {
          if (!explicitTheme()) syncSwitch(btn);
        });
    }
  });
})();
