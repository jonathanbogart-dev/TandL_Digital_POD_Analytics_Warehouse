# Data Dictionary

Documents all analytics-ready models in the marts layer plus key staging models.

---

## Mart Models

### `fct_orders`

**Description:** All POD orders unified across Printful, Printify, Etsy, and Shopify.

**Grain:** One row per order. Primary key: `order_key`.

| Column | Type | Description |
|---|---|---|
| `order_key` | text | Globally unique surrogate key (`<source>-<order_id>`) |
| `order_id` | text | Order ID from the originating source system |
| `source` | text | Source system: `printful`, `printify`, `etsy`, `shopify` |
| `order_date` | date | Calendar date the order was placed |
| `order_week` | date | ISO week start date |
| `order_month` | date | Month start date |
| `created_at` | timestamptz | Full timestamp the order was created |
| `ingested_at` | timestamptz | Timestamp the row was loaded into the warehouse |
| `order_status` | text | Latest known status (source-specific; see `pod_order_statuses` seed) |
| `customer_email` | text | Customer email — Shopify only; null for other sources |
| `fulfillment_status` | text | Fulfillment status — Shopify only |
| `order_total_usd` | numeric | Gross order total in USD |

**Known nulls:**
- `customer_email` and `fulfillment_status` are null for Printful, Printify, and Etsy orders (not exposed by those APIs at the order level)

---

### `fct_revenue`

**Description:** Daily net revenue by source, combining order totals and Stripe charge/refund data.

**Grain:** One row per `(revenue_date, source)`.

| Column | Type | Description |
|---|---|---|
| `revenue_date` | date | Calendar date for this revenue record |
| `source` | text | Revenue source: `printful`, `printify`, `etsy`, `shopify`, `stripe` |
| `revenue_week` | date | ISO week start date |
| `revenue_month` | date | Month start date |
| `gross_revenue_usd` | numeric | Total revenue before refunds |
| `refunds_usd` | numeric | Total refunds issued (Stripe only; 0 for order-based sources) |
| `net_revenue_usd` | numeric | Net revenue after refunds |

**Note:** Stripe revenue is based on `succeeded` charges minus refunds. Order-based sources (Printful, etc.) use `order_total_usd` as gross revenue with no refund data currently modelled at the order level.

---

## Staging Models

### `stg_printful__orders`

| Column | Type | Source Column |
|---|---|---|
| `order_id` | text | `id` |
| `external_order_id` | text | `external_id` |
| `created_at` | timestamptz | `created` (unix → timestamp) |
| `updated_at` | timestamptz | `updated` (unix → timestamp) |
| `ingested_at` | timestamptz | `_ingested_at` |
| `order_status` | text | `status` |
| `order_total_usd` | numeric | `total_retail_costs_total` |

### `stg_printify__orders`

| Column | Type | Source Column |
|---|---|---|
| `order_id` | text | `id` |
| `shop_id` | text | `shop_id` |
| `created_at` | timestamptz | `created_at` |
| `ingested_at` | timestamptz | `_ingested_at` |
| `order_status` | text | `status` |
| `order_total_usd` | numeric | `total_price / 100` (cents → dollars) |

### `stg_etsy__orders`

| Column | Type | Source Column |
|---|---|---|
| `order_id` | text | `receipt_id` |
| `customer_id` | text | `buyer_user_id` |
| `created_at` | timestamptz | `creation_tsz` (unix → timestamp) |
| `ingested_at` | timestamptz | `_ingested_at` |
| `order_status` | text | `status` |
| `currency` | text | `currency_code` |
| `order_total_usd` | numeric | `grandtotal` |

### `stg_shopify__orders`

| Column | Type | Source Column |
|---|---|---|
| `order_id` | text | `id` |
| `order_name` | text | `name` |
| `created_at` | timestamptz | `created_at` |
| `ingested_at` | timestamptz | `_ingested_at` |
| `customer_email` | text | `email` |
| `financial_status` | text | `financial_status` |
| `fulfillment_status` | text | `fulfillment_status` |
| `currency` | text | `currency` |
| `order_total_usd` | numeric | `total_price` |

### `stg_stripe__charges`

| Column | Type | Source Column |
|---|---|---|
| `charge_id` | text | `id` |
| `created_at` | timestamptz | `created` (unix → timestamp) |
| `ingested_at` | timestamptz | `_ingested_at` |
| `charge_status` | text | `status` |
| `currency` | text | `currency` |
| `description` | text | `description` |
| `amount_usd` | numeric | `amount / 100` (cents → dollars) |

### `stg_stripe__refunds`

| Column | Type | Source Column |
|---|---|---|
| `refund_id` | text | `id` |
| `charge_id` | text | `charge_id` |
| `created_at` | timestamptz | `created` (unix → timestamp) |
| `ingested_at` | timestamptz | `_ingested_at` |
| `refund_status` | text | `status` |
| `refund_amount_usd` | numeric | `amount / 100` (cents → dollars) |

---

## Seed Tables

### `pod_order_statuses`

Maps raw source-specific order status strings to a normalized status and a boolean `is_fulfilled`.

| Column | Type | Description |
|---|---|---|
| `source` | text | Source system |
| `raw_status` | text | Status string as returned by the source API |
| `normalized_status` | text | Canonical status: `pending`, `processing`, `on_hold`, `partial`, `fulfilled`, `returned`, `cancelled` |
| `is_fulfilled` | boolean | True if the order has been shipped/completed |
