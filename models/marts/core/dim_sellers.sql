with sellers as (
    select * from {{ ref('stg_olist__sellers') }}
),

items as (
    select * from {{ ref('stg_olist__order_items') }}
),

orders as (
    select * from {{ ref('stg_olist__orders') }}
),

seller_activity as (
    select
        items.seller_id,
        min(orders.purchased_at)        as first_sale_at,
        max(orders.purchased_at)        as last_sale_at,
        count(distinct items.order_id)  as lifetime_orders,
        count(distinct items.product_id) as distinct_products_sold
    from items
    inner join orders on items.order_id = orders.order_id
    group by 1
)

select
    sellers.seller_id,
    sellers.seller_city,
    sellers.seller_state,
    sellers.seller_zip_code_prefix,
    seller_activity.first_sale_at,
    seller_activity.last_sale_at,
    coalesce(seller_activity.lifetime_orders, 0)        as lifetime_orders,
    coalesce(seller_activity.distinct_products_sold, 0) as distinct_products_sold
from sellers
left join seller_activity using (seller_id)
