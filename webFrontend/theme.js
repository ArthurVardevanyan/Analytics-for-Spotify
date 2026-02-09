/**
 * Theme Management for Analytics for Spotify
 * Supports: auto-detection, manual toggle, and localStorage persistence
 */

const ThemeManager = {
  // Theme constants
  THEMES: {
    LIGHT: "light",
    DARK: "dark",
    AUTO: "auto",
  },

  STORAGE_KEY: "theme-preference",

  /**
   * Initialize theme on page load
   */
  init() {
    // Get saved preference or default to auto
    const savedTheme =
      localStorage.getItem(this.STORAGE_KEY) || this.THEMES.AUTO;
    this.setTheme(savedTheme);

    // Listen for system theme changes when in auto mode
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    mediaQuery.addEventListener("change", (e) => {
      if (this.getCurrentPreference() === this.THEMES.AUTO) {
        this.applyTheme(e.matches ? this.THEMES.DARK : this.THEMES.LIGHT);
      }
    });

    // Update toggle button state
    this.updateToggleButton();
  },

  /**
   * Get current theme preference from localStorage
   */
  getCurrentPreference() {
    return localStorage.getItem(this.STORAGE_KEY) || this.THEMES.AUTO;
  },

  /**
   * Get actual active theme (resolves 'auto' to light/dark)
   */
  getActiveTheme() {
    const preference = this.getCurrentPreference();
    if (preference === this.THEMES.AUTO) {
      return window.matchMedia("(prefers-color-scheme: dark)").matches
        ? this.THEMES.DARK
        : this.THEMES.LIGHT;
    }
    return preference;
  },

  /**
   * Set theme and save preference
   */
  setTheme(theme) {
    localStorage.setItem(this.STORAGE_KEY, theme);

    // If auto, detect system preference
    if (theme === this.THEMES.AUTO) {
      const systemPrefersDark = window.matchMedia(
        "(prefers-color-scheme: dark)",
      ).matches;
      this.applyTheme(systemPrefersDark ? this.THEMES.DARK : this.THEMES.LIGHT);
    } else {
      this.applyTheme(theme);
    }

    this.updateToggleButton();
  },

  /**
   * Apply theme to document
   */
  applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);

    // Update Chart.js default colors if Chart is loaded
    if (typeof Chart !== "undefined") {
      this.updateChartDefaults(theme);
    }
  },

  /**
   * Update Chart.js default colors for theme
   */
  updateChartDefaults(theme) {
    const isDark = theme === this.THEMES.DARK;

    Chart.defaults.color = isDark ? "#e0e0e0" : "#666";
    Chart.defaults.borderColor = isDark ? "#444" : "#ddd";

    // Update all existing charts
    Object.values(Chart.instances).forEach((chart) => {
      if (chart.options.scales) {
        Object.keys(chart.options.scales).forEach((scaleId) => {
          const scale = chart.options.scales[scaleId];
          if (scale.ticks) {
            scale.ticks.color = isDark ? "#e0e0e0" : "#666";
          }
          if (scale.grid) {
            scale.grid.color = isDark ? "#444" : "#ddd";
          }
        });
      }
      chart.update("none"); // Update without animation
    });
  },

  /**
   * Toggle between light/dark/auto themes
   */
  toggleTheme() {
    const current = this.getCurrentPreference();
    let next;

    switch (current) {
      case this.THEMES.LIGHT:
        next = this.THEMES.DARK;
        break;
      case this.THEMES.DARK:
        next = this.THEMES.AUTO;
        break;
      case this.THEMES.AUTO:
      default:
        next = this.THEMES.LIGHT;
        break;
    }

    this.setTheme(next);
  },

  /**
   * Update theme toggle button text and icon
   */
  updateToggleButton() {
    const button = document.getElementById("theme-toggle");
    if (!button) return;

    const preference = this.getCurrentPreference();
    const active = this.getActiveTheme();

    // Update button text and icon
    const icons = {
      [this.THEMES.LIGHT]: "☀",
      [this.THEMES.DARK]: "☾",
      [this.THEMES.AUTO]: "◐",
    };

    const labels = {
      [this.THEMES.LIGHT]: "Light",
      [this.THEMES.DARK]: "Dark",
      [this.THEMES.AUTO]: "Auto",
    };

    button.innerHTML = `${icons[preference]} ${labels[preference]}`;
    button.setAttribute("data-theme", preference);
    button.setAttribute("data-active", active);
    button.title = `Current: ${labels[preference]}${preference === this.THEMES.AUTO ? ` (${active})` : ""}`;
  },
};

// Initialize theme when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => ThemeManager.init());
} else {
  ThemeManager.init();
}
