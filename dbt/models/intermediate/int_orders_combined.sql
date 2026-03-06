/*
  int_orders_combined — union of orders from all POD sources with a
  consistent schema and a `source` tag for attribution.

  This model is ephemeral (no table written) and is consumed by fct_orders.
*/

with printful_orders as (

    select
        'printful-' || order_id  as order_key,
        order_id,
        'printful'               as source,
        created_at,
        ingested_at,
        order_status,
        order_total_usd,
        null::text               as customer_email,
        null::text               as fulfillment_status
    from {{ ref('stg_printful__orders') }}

),

printify_orders as (

    select
        'printify-' || order_id  as order_key,
        order_id,
        'printify'               as source,
        created_at,
        ingested_at,
        order_status,
        order_total_usd,
        null::text               as customer_email,
        null::text               as fulfillment_status
    from {{ ref('stg_printify__orders') }}

),

etsy_orders as (

    select
        'etsy-' || order_id      as order_key,
        order_id,
        'etsy'                   as source,
        created_at,
        ingested_at,
        order_status,
        order_total_usd,
        null::text               as customer_email,
        null::text               as fulfillment_status
    from {{ ref('stg_etsy__orders') }}

),

shopify_orders as (

    select
        'shopify-' || order_id   as order_key,
        order_id,
        'shopify'                as source,
        created_at,
        ingested_at,
        financial_status         as order_status,
        order_total_usd,
        customer_email,
        fulfillment_status
    from {{ ref('stg_shopify__orders') }}

),

combined as (

    select * from printful_orders
    union all
    select * from printify_orders
    union all
    select * from etsy_orders
    union all
    select * from shopify_orders

)

select * from combined
