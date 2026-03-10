/**
 * datasets.js — DatasetLoader module
 *
 * Provides access to the backend dataset registry and individual dataset
 * records.  When CONFIG.API_BASE_URL is set, data comes from the API.
 * All functions are async and resolve to the expected shapes.
 *
 * Usage
 * -----
 *   const meta  = await DatasetLoader.getRegistry();   // array of DatasetMeta
 *   const rows  = await DatasetLoader.getRecords("my_dataset");
 *   await DatasetLoader.uploadFile("my_dataset", fileObject, "replace");
 *   await DatasetLoader.deleteDataset("my_dataset");
 *
 * Depends on: config.js (must be loaded first)
 */

const DatasetLoader = (() => {
  /** Cached registry — null means not yet fetched. */
  let _registry = null;

  function _apiUrl(path) {
    return CONFIG.API_BASE_URL + path;
  }

  function _timeout() {
    return AbortSignal.timeout
      ? AbortSignal.timeout(CONFIG.API_TIMEOUT_MS)
      : undefined;
  }

  // ── Registry ──────────────────────────────────────────────────────────────

  /**
   * Fetch the list of all stored datasets from the API.
   * Returns [] when the API is not configured or the request fails.
   *
   * @returns {Promise<Array<{name, source_filename, row_count, rows_in_upload, created_at, updated_at}>>}
   */
  async function getRegistry() {
    if (!CONFIG.API_BASE_URL) return [];
    if (_registry !== null) return _registry;
    try {
      const r = await fetch(_apiUrl("/datasets"), {
        signal: _timeout(),
      });
      if (!r.ok) throw new Error("HTTP " + r.status);
      _registry = await r.json();
      return _registry;
    } catch (err) {
      console.warn("[DatasetLoader] Could not fetch registry:", err.message);
      return [];
    }
  }

  /** Invalidate the cached registry (call after upload or delete). */
  function invalidateRegistry() {
    _registry = null;
  }

  // ── Records ────────────────────────────────────────────────────────────────

  /**
   * Fetch all records for a named dataset.
   *
   * @param {string} name  Dataset slug (lowercase, underscores).
   * @returns {Promise<Array<Object>>}
   * @throws {Error} When the API is unconfigured or the request fails.
   */
  async function getRecords(name) {
    if (!CONFIG.API_BASE_URL) {
      throw new Error("No API configured. Set CONFIG.API_BASE_URL.");
    }
    const r = await fetch(_apiUrl("/datasets/" + name), {
      signal: _timeout(),
    });
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  }

  // ── Upload ─────────────────────────────────────────────────────────────────

  /**
   * Upload a .js dataset file to the backend.
   *
   * @param {string}  name  Dataset slug.
   * @param {File}    file  A File object whose name ends in ".js".
   * @param {"replace"|"append"} mode
   * @returns {Promise<{name, mode, rows_in_upload, total_rows}>}
   * @throws {Error} On network failure or server error (4xx / 5xx).
   */
  async function uploadFile(name, file, mode = "replace") {
    if (!CONFIG.API_BASE_URL) {
      throw new Error("No API configured. Set CONFIG.API_BASE_URL.");
    }
    const form = new FormData();
    form.append("file", file);

    const r = await fetch(
      _apiUrl("/datasets/" + name + "?mode=" + mode),
      { method: "POST", body: form, signal: _timeout() }
    );

    if (!r.ok) {
      const body = await r.json().catch(() => ({}));
      throw new Error(body.detail || "Upload failed (HTTP " + r.status + ")");
    }

    invalidateRegistry();
    return r.json();
  }

  // ── Delete ─────────────────────────────────────────────────────────────────

  /**
   * Delete a named dataset from the backend store.
   *
   * @param {string} name  Dataset slug.
   * @returns {Promise<void>}
   * @throws {Error} On network failure or server error.
   */
  async function deleteDataset(name) {
    if (!CONFIG.API_BASE_URL) {
      throw new Error("No API configured. Set CONFIG.API_BASE_URL.");
    }
    const r = await fetch(_apiUrl("/datasets/" + name), {
      method: "DELETE",
      signal: _timeout(),
    });
    if (!r.ok && r.status !== 204) {
      const body = await r.json().catch(() => ({}));
      throw new Error(body.detail || "Delete failed (HTTP " + r.status + ")");
    }
    invalidateRegistry();
  }

  // ── Schema inference ───────────────────────────────────────────────────────

  const _DATE_RE = /^\d{4}-\d{2}-\d{2}/;

  /**
   * Infer dimensions and metrics from a sample record.
   *
   * Rules:
   *   - Keys whose values are numbers → metrics (defaultAgg: sum for
   *     integers, avg for floats).
   *   - Keys whose values match YYYY-MM-DD → date dimensions.
   *   - Everything else → string dimensions.
   *
   * @param {Object} sample  A single record from the dataset.
   * @returns {{ dimensions: Array, metrics: Array }}
   */
  function inferSchema(sample) {
    const dimensions = [];
    const metrics    = [];

    for (const [key, val] of Object.entries(sample)) {
      const label = key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());

      if (typeof val === "number") {
        const isFloat = !Number.isInteger(val);
        metrics.push({
          key,
          label,
          typeTag:    "number",
          defaultAgg: isFloat ? "avg" : "sum",
        });
      } else if (typeof val === "string" && _DATE_RE.test(val)) {
        dimensions.push({ key, label, typeTag: "date" });
      } else {
        dimensions.push({ key, label, typeTag: "string" });
      }
    }

    return { dimensions, metrics };
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  return {
    getRegistry,
    invalidateRegistry,
    getRecords,
    uploadFile,
    deleteDataset,
    inferSchema,
  };
})();
