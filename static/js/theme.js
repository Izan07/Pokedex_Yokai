(() => {
    "use strict";

    const STORAGE_KEY = "yokai-pokedex:theme:v1";
    const root = document.documentElement;
    let savedTheme = null;

    try {
        const stored = window.localStorage.getItem(STORAGE_KEY);
        if (stored === "light" || stored === "dark") savedTheme = stored;
    } catch (_) {
        // Storage is optional; the operating-system preference still applies.
    }

    let systemPrefersDark = false;
    try {
        systemPrefersDark = typeof window.matchMedia === "function"
            && window.matchMedia("(prefers-color-scheme: dark)").matches;
    } catch (_) {
        systemPrefersDark = false;
    }
    let currentTheme = savedTheme || (systemPrefersDark ? "dark" : "light");

    const updateButton = () => {
        const button = document.getElementById("theme-toggle");
        const icon = document.getElementById("theme-icon");
        if (!button || !icon) return;
        const nextTheme = currentTheme === "dark" ? "light" : "dark";
        const label = `Cambiar a modo ${nextTheme === "dark" ? "oscuro" : "claro"}`;
        icon.textContent = currentTheme === "dark" ? "☀" : "☾";
        button.setAttribute("aria-label", label);
        button.title = label;
    };

    const applyTheme = () => {
        root.dataset.theme = currentTheme;
        updateButton();
    };

    applyTheme();

    const attachToggle = () => {
        const button = document.getElementById("theme-toggle");
        if (!button) return;
        updateButton();
        button.addEventListener("click", () => {
            currentTheme = currentTheme === "dark" ? "light" : "dark";
            applyTheme();
            try {
                window.localStorage.setItem(STORAGE_KEY, currentTheme);
            } catch (_) {
                // Theme still changes for the current page if storage is unavailable.
            }
        });
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", attachToggle, { once: true });
    } else {
        attachToggle();
    }
})();
