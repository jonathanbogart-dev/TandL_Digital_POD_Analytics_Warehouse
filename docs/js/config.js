/**
 * config.js — Central configuration for API endpoints and feature flags.
 *
 * Edit this file to point to your actual API endpoints and toggle features.
 * This is loaded first so all other scripts can reference CONFIG.
 *
 * ⚠️  SECURITY: This file is public — it is served as-is to every browser.
 *     NEVER put API keys, tokens, passwords, or any secret here.
 *     If the API requires authentication, implement it server-side and have
 *     your backend proxy requests; the front end should only hold the base URL.
 */

const CONFIG = {
  /**
   * Base URL for your backend REST API.
   * Set to an empty string ("") to disable live API calls and use static
   * data only (useful for GitHub Pages deployment without a backend).
   *
   * Local dev (FastAPI running via `make api-dev` or `docker compose up`):
   *   "http://localhost:8000/api"
   *
   * Production:
   *   "https://api.yourdomain.com/api"
   */
  API_BASE_URL: "",  // ← set to "http://localhost:8000/api" for local dev

  /**
   * Path prefix for static JSON data files (relative to this page).
   * Files in docs/data/ are served at this path on GitHub Pages.
   */
  DATA_BASE_PATH: "data",

  /**
   * Request timeout in milliseconds for API calls.
   */
  API_TIMEOUT_MS: 10000,

  /**
   * Static JSON files to load. Keys are logical names used in data.js;
   * values are filenames inside DATA_BASE_PATH/.
   */
  STATIC_FILES: {
    kpis:    "kpis.json",
    orders:  "orders.json",
    revenue: "revenue.json",
  },

  /**
   * REST API endpoint paths (appended to API_BASE_URL).
   * Only used when API_BASE_URL is non-empty.
   */
  API_ENDPOINTS: {
    kpis:       "/kpis",
    orders:     "/orders/recent",
    revenue:    "/revenue/by-source",
    // Dataset management (Explore page + dynamic dashboards)
    datasets:   "/datasets",          // GET → registry; POST /{name} → upload
  },

  /**
   * Maximum number of recent orders to display.
   */
  ORDERS_DISPLAY_LIMIT: 25,
};

// Freeze to prevent accidental mutation
Object.freeze(CONFIG);
