with source as (

    select * from {{ source('stripe', 'refunds') }}

),

renamed as (

    select
        -- keys
        id::text                                    as refund_id,
        charge_id::text                             as charge_id,

        -- timestamps
        to_timestamp(created)::timestamptz          as created_at,
        _ingested_at::timestamptz                   as ingested_at,

        -- attributes
        status::text                                as refund_status,

        -- metrics
        (amount::numeric / 100.0)                   as refund_amount_usd

    from source

)

select * from renamed
