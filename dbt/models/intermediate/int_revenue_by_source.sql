/*
  int_revenue_by_source — aggregates gross revenue per source per day.
  Used by fct_revenue and the /revenue/by-source API endpoint.
*/

with orders as (

    select * from {{ ref('int_orders_combined') }}

),

charges as (

    select * from {{ ref('stg_stripe__charges') }}
    where charge_status = 'succeeded'

),

refunds as (

    select * from {{ ref('stg_stripe__refunds') }}

),

net_stripe as (

    select
        date_trunc('day', c.created_at)::date   as revenue_date,
        'stripe'                                 as source,
        sum(c.amount_usd)                        as gross_revenue_usd,
        sum(coalesce(r.refund_amount_usd, 0))    as refunds_usd,
        sum(c.amount_usd)
          - sum(coalesce(r.refund_amount_usd, 0)) as net_revenue_usd

    from charges c
    left join refunds r on r.charge_id = c.charge_id
    group by 1, 2

),

order_revenue as (

    select
        date_trunc('day', created_at)::date     as revenue_date,
        source,
        sum(order_total_usd)                    as gross_revenue_usd,
        0::numeric                              as refunds_usd,
        sum(order_total_usd)                    as net_revenue_usd

    from orders
    group by 1, 2

),

combined as (

    select * from net_stripe
    union all
    select * from order_revenue

)

select * from combined
