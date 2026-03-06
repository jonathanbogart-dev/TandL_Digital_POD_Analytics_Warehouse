with source as (

    select * from {{ source('printful', 'orders') }}

),

renamed as (

    select
        -- keys
        id::text                            as order_id,
        external_id::text                   as external_order_id,

        -- timestamps
        to_timestamp(created)::timestamptz  as created_at,
        to_timestamp(updated)::timestamptz  as updated_at,
        _ingested_at::timestamptz           as ingested_at,

        -- attributes
        status::text                        as order_status,

        -- metrics
        total_retail_costs_total::numeric   as order_total_usd

    from source

)

select * from renamed
