with source as (

    select * from {{ source('shopify', 'orders') }}

),

renamed as (

    select
        -- keys
        id::text                            as order_id,
        name::text                          as order_name,

        -- timestamps
        created_at::timestamptz             as created_at,
        _ingested_at::timestamptz           as ingested_at,

        -- attributes
        email::text                         as customer_email,
        financial_status::text              as financial_status,
        fulfillment_status::text            as fulfillment_status,
        currency::text                      as currency,

        -- metrics
        total_price::numeric                as order_total_usd

    from source

)

select * from renamed
