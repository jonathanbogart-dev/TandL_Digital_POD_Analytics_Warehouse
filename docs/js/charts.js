/**
 * charts.js — Simple pure-CSS/HTML bar chart renderer.
 *
 * No external charting library required. Charts are built from divs
 * and CSS so they work anywhere without CDN dependencies.
 *
 * To swap in Chart.js or another library, replace the render functions
 * here without touching main.js.
 */

/**
 * Renders a horizontal bar chart into a container element.
 *
 * @param {HTMLElement} container - The element to render into.
 * @param {Array<{ label: string, value: number }>} rows - Data rows.
 * @param {(value: number) => string} [formatValue] - Formats the displayed value.
 */
function renderBarChart(container, rows, formatValue = (v) => String(v)) {
  container.innerHTML = "";

  if (!rows || rows.length === 0) {
    container.innerHTML = '<p style="color: var(--color-text-muted); font-style: italic;">No data available.</p>';
    return;
  }

  const maxValue = Math.max(...rows.map((r) => r.value), 1);

  rows.forEach((row) => {
    const pct = Math.round((row.value / maxValue) * 100);
    const isNarrow = pct < 20;
    const formatted = formatValue(row.value);

    const rowEl = document.createElement("div");
    rowEl.className = "bar-row";
    rowEl.innerHTML = `
      <span class="bar-label">${escapeHtml(row.label)}</span>
      <div class="bar-track">
        <div class="bar-fill${isNarrow ? " narrow" : ""}" style="width: ${pct}%">
          ${isNarrow ? "" : `<span class="bar-amount">${escapeHtml(formatted)}</span>`}
        </div>
      </div>
      ${isNarrow ? `<span class="bar-amount-outside">${escapeHtml(formatted)}</span>` : ""}
    `;
    container.appendChild(rowEl);
  });
}

/**
 * Returns a CSS badge element string for an order status.
 *
 * @param {string} status
 * @returns {string} HTML string
 */
function statusBadge(status) {
  const normalized = (status || "").toLowerCase();
  const classMap = {
    fulfilled: "badge-fulfilled",
    shipped:   "badge-fulfilled",
    complete:  "badge-fulfilled",
    pending:   "badge-pending",
    processing: "badge-pending",
    cancelled: "badge-cancelled",
    canceled:  "badge-cancelled",
    refunded:  "badge-cancelled",
  };
  const cls = classMap[normalized] || "badge-default";
  return `<span class="badge ${cls}">${escapeHtml(status)}</span>`;
}

/**
 * Escapes a string for safe HTML insertion.
 *
 * @param {any} value
 * @returns {string}
 */
function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/**
 * Formats a number as USD currency.
 *
 * @param {number} value
 * @returns {string}
 */
function formatUSD(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Formats a number with comma separators.
 *
 * @param {number} value
 * @returns {string}
 */
function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(value);
}

/**
 * Formats a decimal as a percentage string.
 *
 * @param {number} value - e.g. 0.943 or 94.3
 * @param {boolean} [isDecimal] - true if value is 0–1 range, false if 0–100
 * @returns {string}
 */
function formatPercent(value, isDecimal = false) {
  const pct = isDecimal ? value * 100 : value;
  return `${pct.toFixed(1)}%`;
}
