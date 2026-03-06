with source as (

    select * from {{ source('stripe', 'charges') }}

),

renamed as (

    select
        -- keys
        id::text                                    as charge_id,

        -- timestamps
        to_timestamp(created)::timestamptz          as created_at,
        _ingested_at::timestamptz                   as ingested_at,

        -- attributes
        status::text                                as charge_status,
        currency::text                              as currency,
        description::text                           as description,

        -- metrics
        -- Stripe stores amounts in cents
        (amount::numeric / 100.0)                   as amount_usd

    from source

)

select * from renamed
