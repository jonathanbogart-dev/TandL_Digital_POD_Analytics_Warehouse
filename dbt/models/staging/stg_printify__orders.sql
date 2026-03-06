with source as (

    select * from {{ source('printify', 'orders') }}

),

renamed as (

    select
        -- keys
        id::text                                    as order_id,
        shop_id::text                               as shop_id,

        -- timestamps
        created_at::timestamptz                     as created_at,
        _ingested_at::timestamptz                   as ingested_at,

        -- attributes
        status::text                                as order_status,

        -- metrics
        -- Printify stores price in cents; convert to dollars
        (total_price::numeric / 100.0)              as order_total_usd

    from source

)

select * from renamed
