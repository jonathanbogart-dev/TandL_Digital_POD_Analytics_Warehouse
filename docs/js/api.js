/**
 * api.js — Helpers for fetching data from a REST API.
 *
 * Functions here wrap fetch() with timeout, error handling, and a consistent
 * response shape: { ok: boolean, data: any|null, error: string|null }.
 *
 * All functions are no-ops (return null) if CONFIG.API_BASE_URL is empty,
 * allowing the app to fall back to static JSON seamlessly.
 */

/**
 * Fetches a URL with a timeout.
 *
 * @param {string} url
 * @param {number} timeoutMs
 * @returns {Promise<Response>}
 */
async function fetchWithTimeout(url, timeoutMs = CONFIG.API_TIMEOUT_MS) {
  const controller = new AbortController();
  const timerId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { signal: controller.signal });
    return response;
  } finally {
    clearTimeout(timerId);
  }
}

/**
 * Makes a GET request to an API endpoint.
 *
 * @param {string} path - Endpoint path (e.g. "/orders/recent").
 * @param {Object} [params] - Optional query parameters.
 * @returns {Promise<{ ok: boolean, data: any|null, error: string|null }>}
 */
async function apiGet(path, params = {}) {
  if (!CONFIG.API_BASE_URL) {
    return { ok: false, data: null, error: "API_BASE_URL not configured" };
  }

  // Reject plain-HTTP origins in production to prevent credential interception.
  // Allow localhost HTTP for local development only.
  const base = CONFIG.API_BASE_URL;
  const isLocalhost = /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?/.test(base);
  if (base.startsWith("http://") && !isLocalhost) {
    console.error("Security: API_BASE_URL must use HTTPS in production.");
    return { ok: false, data: null, error: "API_BASE_URL must use HTTPS" };
  }

  const url = new URL(base + path);
  Object.entries(params).forEach(([key, val]) => {
    if (val !== undefined && val !== null) {
      url.searchParams.set(key, val);
    }
  });

  try {
    const response = await fetchWithTimeout(url.toString());

    if (!response.ok) {
      const text = await response.text().catch(() => "");
      return {
        ok: false,
        data: null,
        error: `API error ${response.status}: ${text || response.statusText}`,
      };
    }

    const data = await response.json();
    return { ok: true, data, error: null };
  } catch (err) {
    if (err.name === "AbortError") {
      return { ok: false, data: null, error: "Request timed out" };
    }
    return { ok: false, data: null, error: err.message };
  }
}

/**
 * Fetch KPI summary data from the API.
 *
 * Expected response shape:
 * {
 *   total_orders: number,
 *   total_revenue_usd: number,
 *   fulfillment_rate_pct: number,
 *   active_products: number
 * }
 *
 * @returns {Promise<{ ok: boolean, data: Object|null, error: string|null }>}
 */
async function apiGetKPIs() {
  return apiGet(CONFIG.API_ENDPOINTS.kpis);
}

/**
 * Fetch recent orders from the API.
 *
 * Expected response shape: Array of order objects:
 * [{ order_id, order_date, source, status, total_usd }, ...]
 *
 * @param {number} [limit]
 * @returns {Promise<{ ok: boolean, data: Array|null, error: string|null }>}
 */
async function apiGetRecentOrders(limit = CONFIG.ORDERS_DISPLAY_LIMIT) {
  return apiGet(CONFIG.API_ENDPOINTS.orders, { limit });
}

/**
 * Fetch revenue by source from the API.
 *
 * Expected response shape:
 * [{ source: string, revenue_usd: number }, ...]
 *
 * @returns {Promise<{ ok: boolean, data: Array|null, error: string|null }>}
 */
async function apiGetRevenueBySource() {
  return apiGet(CONFIG.API_ENDPOINTS.revenue);
}
