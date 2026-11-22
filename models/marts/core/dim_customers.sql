-- One row per real customer (customer_unique_id).
-- Olist issues a new customer_id for every order, so customer_unique_id is the person.
with customers as (
    select * from {{ ref('stg_olist__customers') }}
),

orders as (
    select * from {{ ref('stg_olist__orders') }}
),

customer_orders as (
    select
        customers.customer_unique_id,
        customers.customer_city,
        customers.customer_state,
        customers.customer_zip_code_prefix,
        orders.purchased_at
    from customers
    inner join orders on customers.customer_id = orders.customer_id
),

latest_location as (
    -- location from the customer's most recent order
    select *
    from customer_orders
    qualify row_number() over (
        partition by customer_unique_id order by purchased_at desc
    ) = 1
),

order_stats as (
    select
        customer_unique_id,
        min(purchased_at)  as first_order_at,
        max(purchased_at)  as last_order_at,
        count(*)           as lifetime_orders
    from customer_orders
    group by 1
)

select
    latest_location.customer_unique_id,
    latest_location.customer_city,
    latest_location.customer_state,
    latest_location.customer_zip_code_prefix,
    order_stats.first_order_at,
    order_stats.last_order_at,
    order_stats.lifetime_orders,
    order_stats.lifetime_orders > 1  as is_repeat_customer
from latest_location
inner join order_stats using (customer_unique_id)
