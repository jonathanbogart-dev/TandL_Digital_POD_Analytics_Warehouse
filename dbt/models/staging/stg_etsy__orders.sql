with source as (

    select * from {{ source('etsy', 'receipts') }}

),

renamed as (

    select
        -- keys
        receipt_id::text                            as order_id,
        buyer_user_id::text                         as customer_id,

        -- timestamps
        to_timestamp(creation_tsz)::timestamptz     as created_at,
        _ingested_at::timestamptz                   as ingested_at,

        -- attributes
        status::text                                as order_status,
        currency_code::text                         as currency,

        -- metrics
        grandtotal::numeric                         as order_total_usd

    from source

)

select * from renamed
