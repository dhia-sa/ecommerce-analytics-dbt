with products as (
    select * from {{ ref('stg_olist__products') }}
),

translation as (
    select * from {{ ref('stg_olist__category_translation') }}
)

select
    products.product_id,
    coalesce(
        translation.product_category_name_english,
        products.product_category_name,
        'unknown'
    )                                        as product_category,
    products.product_category_name           as product_category_portuguese,
    products.product_photos_qty,
    products.product_weight_g,
    products.product_length_cm,
    products.product_height_cm,
    products.product_width_cm,
    products.product_length_cm
        * products.product_height_cm
        * products.product_width_cm          as product_volume_cm3
from products
left join translation
    on products.product_category_name = translation.product_category_name
