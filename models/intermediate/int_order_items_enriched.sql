-- Order items joined with product category (in English) and seller location
with items as (
    select * from {{ ref('stg_olist__order_items') }}
),

products as (
    select * from {{ ref('stg_olist__products') }}
),

translation as (
    select * from {{ ref('stg_olist__category_translation') }}
),

sellers as (
    select * from {{ ref('stg_olist__sellers') }}
)

select
    items.order_id,
    items.order_item_id,
    items.product_id,
    items.seller_id,
    items.shipping_limit_at,
    items.price,
    items.freight_value,
    items.price + items.freight_value                         as item_total,
    coalesce(
        translation.product_category_name_english,
        products.product_category_name,
        'unknown'
    )                                                         as product_category,
    sellers.seller_city,
    sellers.seller_state
from items
left join products    on items.product_id = products.product_id
left join translation on products.product_category_name = translation.product_category_name
left join sellers     on items.seller_id = sellers.seller_id
