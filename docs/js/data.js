/**
 * data.js — Helpers for loading static JSON data files.
 *
 * These functions fetch pre-built JSON files from docs/data/.
 * They are the fallback when the live API is unavailable or unconfigured.
 *
 * Uses the same { ok, data, error } response shape as api.js.
 */

/**
 * Loads a static JSON file from the data directory.
 *
 * @param {string} filename - Filename from CONFIG.STATIC_FILES (e.g. "kpis.json").
 * @returns {Promise<{ ok: boolean, data: any|null, error: string|null }>}
 */
async function loadStaticJSON(filename) {
  const url = `${CONFIG.DATA_BASE_PATH}/${filename}`;
  try {
    const response = await fetch(url);
    if (!response.ok) {
      return {
        ok: false,
        data: null,
        error: `Failed to load ${url}: ${response.status} ${response.statusText}`,
      };
    }
    const data = await response.json();
    return { ok: true, data, error: null };
  } catch (err) {
    return { ok: false, data: null, error: `Error loading ${url}: ${err.message}` };
  }
}

/**
 * Resolves data using the API first, then falling back to static JSON.
 *
 * @param {Function} apiFn - An api.js function to call first.
 * @param {string} staticFile - Key from CONFIG.STATIC_FILES to fall back to.
 * @returns {Promise<{ ok: boolean, data: any|null, error: string|null, source: "api"|"static"|"error" }>}
 */
async function resolveData(apiFn, staticFile) {
  // Try live API if configured
  if (CONFIG.API_BASE_URL) {
    const result = await apiFn();
    if (result.ok) {
      return { ...result, source: "api" };
    }
    console.warn(`API call failed (${result.error}), falling back to static data.`);
  }

  // Fall back to static JSON
  const filename = CONFIG.STATIC_FILES[staticFile];
  if (!filename) {
    return { ok: false, data: null, error: `No static file configured for: ${staticFile}`, source: "error" };
  }

  const result = await loadStaticJSON(filename);
  return { ...result, source: result.ok ? "static" : "error" };
}

// Convenience wrappers with fallback built in

/**
 * Get KPI data (API → static fallback).
 */
async function getKPIs() {
  return resolveData(apiGetKPIs, "kpis");
}

/**
 * Get recent orders (API → static fallback).
 */
async function getRecentOrders() {
  return resolveData(apiGetRecentOrders, "orders");
}

/**
 * Get revenue by source (API → static fallback).
 */
async function getRevenueBySource() {
  return resolveData(apiGetRevenueBySource, "revenue");
}
