(() => {
    "use strict";

    const STORAGE_KEY = "yokai-pokedex:favorites:v1";
    const favoriteButtons = Array.from(document.querySelectorAll("[data-favorite-button]"));
    if (!favoriteButtons.length) return;

    const readFavorites = () => {
        try {
            const stored = window.localStorage.getItem(STORAGE_KEY);
            const parsed = stored ? JSON.parse(stored) : [];
            return new Set(Array.isArray(parsed) ? parsed.filter((slug) => typeof slug === "string") : []);
        } catch (_) {
            return new Set();
        }
    };

    let favorites = readFavorites();
    const persistFavorites = () => {
        try {
            window.localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(favorites)));
        } catch (_) {
            // Keep favorites in memory for this page view if browser storage is unavailable.
        }
    };

    const favoritesPage = document.querySelector("[data-favorites-page]");
    const emptyMessage = document.querySelector("[data-favorites-empty]");

    const renderFavorites = () => {
        favoriteButtons.forEach((button) => {
            const active = favorites.has(button.dataset.yokaiSlug);
            const icon = button.querySelector("[aria-hidden='true']");
            button.classList.toggle("is-favorite", active);
            button.setAttribute("aria-pressed", String(active));
            button.setAttribute("aria-label", active ? "Quitar de favoritos" : "Añadir a favoritos");
            button.title = active ? "Quitar de favoritos" : "Añadir a favoritos";
            if (icon) icon.textContent = active ? "★" : "☆";
        });

        if (favoritesPage) {
            const cards = Array.from(favoritesPage.querySelectorAll(".yokai-card"));
            let visibleCount = 0;
            cards.forEach((card) => {
                const active = favorites.has(card.dataset.yokaiSlug);
                card.hidden = !active;
                if (active) visibleCount += 1;
            });
            favoritesPage.classList.add("favorites-ready");
            if (emptyMessage) emptyMessage.hidden = visibleCount > 0;
        }
    };

    favoriteButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const slug = button.dataset.yokaiSlug;
            if (favorites.has(slug)) favorites.delete(slug);
            else favorites.add(slug);
            persistFavorites();
            renderFavorites();
        });
    });

    renderFavorites();
})();
