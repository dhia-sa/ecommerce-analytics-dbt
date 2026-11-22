-- Grain: one row per item in an order
with items as (
    select * from {{ ref('int_order_items_enriched') }}
),

orders as (
    select * from {{ ref('stg_olist__orders') }}
),

customers as (
    select * from {{ ref('stg_olist__customers') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['items.order_id', 'items.order_item_id']) }} as order_item_key,
    items.order_id,
    items.order_item_id,
    items.product_id,
    items.seller_id,
    customers.customer_unique_id,
    cast(orders.purchased_at as date)                as order_date,
    orders.order_status,
    items.product_category,
    items.seller_state,
    customers.customer_state,
    items.seller_state = customers.customer_state    as is_same_state_shipment,
    items.price,
    items.freight_value,
    items.item_total
from items
inner join orders    on items.order_id = orders.order_id
inner join customers on orders.customer_id = customers.customer_id
