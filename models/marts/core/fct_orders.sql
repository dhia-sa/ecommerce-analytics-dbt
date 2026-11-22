-- Grain: one row per order
with orders as (
    select * from {{ ref('stg_olist__orders') }}
),

customers as (
    select * from {{ ref('stg_olist__customers') }}
),

items as (
    select
        order_id,
        count(*)                          as item_count,
        count(distinct seller_id)         as seller_count,
        sum(price)                        as items_value,
        sum(freight_value)                as freight_value
    from {{ ref('stg_olist__order_items') }}
    group by 1
),

payments as (
    select * from {{ ref('int_order_payments_pivoted') }}
),

reviews as (
    select * from {{ ref('int_order_reviews_deduplicated') }}
)

select
    orders.order_id,
    orders.customer_id,
    customers.customer_unique_id,
    customers.customer_state,
    orders.order_status,
    orders.order_status not in ('canceled', 'unavailable')        as is_valid_order,

    -- dates
    orders.purchased_at,
    cast(orders.purchased_at as date)                             as order_date,
    orders.approved_at,
    orders.delivered_to_carrier_at,
    orders.delivered_at,
    orders.estimated_delivery_at,

    -- order value
    coalesce(items.item_count, 0)                                 as item_count,
    coalesce(items.seller_count, 0)                               as seller_count,
    coalesce(items.items_value, 0)                                as items_value,
    coalesce(items.freight_value, 0)                              as freight_value,
    coalesce(items.items_value, 0) + coalesce(items.freight_value, 0) as order_value,

    -- payment
    payments.total_payment,
    payments.main_payment_type,
    payments.max_installments,

    -- delivery
    date_diff('day', orders.purchased_at, orders.delivered_at)   as delivery_days,
    date_diff('day', cast(orders.estimated_delivery_at as date), cast(orders.delivered_at as date)) as days_vs_estimate,  -- negative = early
    case
        when orders.delivered_at is null then null
        -- estimated date has no time part, so compare calendar days
        else cast(orders.delivered_at as date) > cast(orders.estimated_delivery_at as date)
    end                                                           as is_late_delivery,

    -- review
    reviews.review_score,
    reviews.review_comment_message is not null                    as has_review_comment

from orders
left join customers on orders.customer_id = customers.customer_id
left join items     on orders.order_id = items.order_id
left join payments  on orders.order_id = payments.order_id
left join reviews   on orders.order_id = reviews.order_id
