// Theme toggle functionality
(function() {
    'use strict';

    const THEME_KEY = 'maze-theme';
    const LIGHT = 'light-theme';
    const DARK = 'dark-theme';

    // Get saved theme or system preference
    function getInitialTheme() {
        const saved = localStorage.getItem(THEME_KEY);
        if (saved === 'light' || saved === 'dark') {
            return saved === 'light' ? LIGHT : DARK;
        }
        // No saved preference, use system
        return null;
    }

    // Apply theme
    function applyTheme(theme) {
        document.body.classList.remove(LIGHT, DARK);
        if (theme) {
            document.body.classList.add(theme);
        }
    }

    // Toggle theme
    function toggleTheme() {
        const currentTheme = document.body.classList.contains(DARK) ? DARK :
                           document.body.classList.contains(LIGHT) ? LIGHT : null;

        let newTheme;
        if (currentTheme === DARK) {
            newTheme = LIGHT;
            localStorage.setItem(THEME_KEY, 'light');
        } else {
            newTheme = DARK;
            localStorage.setItem(THEME_KEY, 'dark');
        }

        applyTheme(newTheme);
    }

    // Initialize
    function init() {
        const initialTheme = getInitialTheme();
        if (initialTheme) {
            applyTheme(initialTheme);
        }

        // Add toggle listener
        const toggle = document.querySelector('.theme-toggle');
        if (toggle) {
            toggle.addEventListener('click', toggleTheme);
        }

        // Listen for system theme changes
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', (e) => {
            // Only update if user hasn't set a manual preference
            if (!localStorage.getItem(THEME_KEY)) {
                applyTheme(null); // Remove manual classes, let CSS handle it
            }
        });
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
