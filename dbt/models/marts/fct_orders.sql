/*
  fct_orders — final analytics-ready fact table for all POD orders.

  Grain: one row per order (source + order_id composite key).
  Primary key: order_key (surrogate, globally unique across sources).
*/

with orders as (

    select * from {{ ref('int_orders_combined') }}

)

select
    -- keys
    order_key,
    order_id,
    source,

    -- dates
    date_trunc('day', created_at)::date   as order_date,
    date_trunc('week', created_at)::date  as order_week,
    date_trunc('month', created_at)::date as order_month,
    created_at,
    ingested_at,

    -- attributes
    order_status,
    customer_email,
    fulfillment_status,

    -- metrics
    coalesce(order_total_usd, 0)          as order_total_usd

from orders
