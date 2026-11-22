with source as (
    select * from {{ source('olist', 'customers') }}
)

select
    customer_id,                                   -- one per order
    customer_unique_id,                            -- the real person
    lpad(customer_zip_code_prefix, 5, '0')   as customer_zip_code_prefix,
    customer_city,
    upper(customer_state)                    as customer_state
from source
