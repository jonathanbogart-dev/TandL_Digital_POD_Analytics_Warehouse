/*
  fct_revenue — daily net revenue by source, backing the
  /revenue/by-source API endpoint and the dashboard revenue widget.

  Grain: one row per (revenue_date, source).
*/

with revenue as (

    select * from {{ ref('int_revenue_by_source') }}

)

select
    -- keys / dimensions
    revenue_date,
    source,

    -- time dimensions
    date_trunc('week',  revenue_date::timestamp)::date  as revenue_week,
    date_trunc('month', revenue_date::timestamp)::date  as revenue_month,

    -- metrics
    gross_revenue_usd,
    refunds_usd,
    net_revenue_usd

from revenue
