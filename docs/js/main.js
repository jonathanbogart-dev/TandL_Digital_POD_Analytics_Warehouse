/**
 * main.js — Page initialization and DOM wiring.
 *
 * Loads all data (via data.js which handles API → static fallback),
 * then populates the page elements.
 *
 * Add new sections by:
 *   1. Adding data to a JSON file in docs/data/ and/or an API endpoint
 *   2. Adding a fetch call and render function here
 *   3. Adding the HTML section to index.html
 */

// ---- Utility ----

function showStatus(message, type = "info") {
  const bar = document.getElementById("status-bar");
  const msg = document.getElementById("status-message");
  if (!bar || !msg) return;
  msg.textContent = message;
  bar.className = `status-bar ${type}`;
}

function hideStatus() {
  const bar = document.getElementById("status-bar");
  if (bar) bar.className = "status-bar hidden";
}

// ---- KPI Cards ----

function renderKPIs(kpis) {
  const el = (id) => document.getElementById(id);
  const card = (id, card) => {
    const c = card.closest(".kpi-card");
    if (c) c.classList.remove("loading");
  };

  const ordersEl = el("kpi-orders");
  if (ordersEl) {
    ordersEl.textContent = formatNumber(kpis.total_orders ?? 0);
    card("kpi-orders", ordersEl);
  }

  const revenueEl = el("kpi-revenue");
  if (revenueEl) {
    revenueEl.textContent = formatUSD(kpis.total_revenue_usd ?? 0);
    card("kpi-revenue", revenueEl);
  }

  const fulfillmentEl = el("kpi-fulfillment");
  if (fulfillmentEl) {
    fulfillmentEl.textContent = formatPercent(kpis.fulfillment_rate_pct ?? 0);
    card("kpi-fulfillment", fulfillmentEl);
  }

  const productsEl = el("kpi-products");
  if (productsEl) {
    productsEl.textContent = formatNumber(kpis.active_products ?? 0);
    card("kpi-products", productsEl);
  }
}

// ---- Orders Table ----

function renderOrdersTable(orders) {
  const tbody = document.getElementById("orders-tbody");
  if (!tbody) return;

  if (!orders || orders.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="loading-row">No orders found.</td></tr>';
    return;
  }

  const rows = orders.slice(0, CONFIG.ORDERS_DISPLAY_LIMIT).map((order) => `
    <tr>
      <td>${escapeHtml(order.order_id)}</td>
      <td>${escapeHtml(order.order_date)}</td>
      <td>${escapeHtml(order.source)}</td>
      <td>${statusBadge(order.status)}</td>
      <td>${formatUSD(order.total_usd ?? 0)}</td>
    </tr>
  `);

  tbody.innerHTML = rows.join("");
}

// ---- Revenue Chart ----

function renderRevenueChart(revenueRows) {
  const container = document.getElementById("revenue-chart");
  if (!container) return;

  const chartData = (revenueRows || []).map((row) => ({
    label: row.source,
    value: row.revenue_usd,
  }));

  renderBarChart(container, chartData, formatUSD);
}

// ---- Bootstrap ----

async function init() {
  // Set footer year
  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // Load all data in parallel
  const [kpisResult, ordersResult, revenueResult] = await Promise.all([
    getKPIs(),
    getRecentOrders(),
    getRevenueBySource(),
  ]);

  const errors = [kpisResult, ordersResult, revenueResult]
    .filter((r) => !r.ok)
    .map((r) => r.error);

  if (errors.length > 0) {
    showStatus(`Data load warning: ${errors[0]}`, "error");
  } else {
    hideStatus();
  }

  if (kpisResult.ok)   renderKPIs(kpisResult.data);
  if (ordersResult.ok) renderOrdersTable(ordersResult.data);
  if (revenueResult.ok) renderRevenueChart(revenueResult.data);
}

document.addEventListener("DOMContentLoaded", init);
