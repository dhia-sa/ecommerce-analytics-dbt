-- One row per seller: revenue, volume, delivery and review performance
with items as (
    select * from {{ ref('fct_order_items') }}
    where order_status not in ('canceled', 'unavailable')
      and order_date between cast('{{ var("analysis_start_date") }}' as date)
                         and cast('{{ var("analysis_end_date") }}' as date)
),

orders as (
    select order_id, is_late_delivery, delivery_days, review_score
    from {{ ref('fct_orders') }}
),

sellers as (
    select * from {{ ref('dim_sellers') }}
),

seller_orders as (
    select distinct items.seller_id, orders.*
    from items
    inner join orders on items.order_id = orders.order_id
),

item_stats as (
    select
        seller_id,
        count(distinct order_id)           as orders,
        count(*)                           as items_sold,
        count(distinct product_category)   as categories,
        sum(price)                         as gmv,
        mode(product_category)             as top_category
    from items
    group by 1
),

order_stats as (
    select
        seller_id,
        avg(delivery_days)                                   as avg_delivery_days,
        avg(case when is_late_delivery then 1.0 else 0.0 end) filter (where is_late_delivery is not null) as late_rate,
        avg(review_score)                                    as avg_review_score
    from seller_orders
    group by 1
)

select
    sellers.seller_id,
    sellers.seller_city,
    sellers.seller_state,
    item_stats.orders,
    item_stats.items_sold,
    item_stats.categories,
    item_stats.top_category,
    item_stats.gmv,
    order_stats.avg_delivery_days,
    order_stats.late_rate,
    order_stats.avg_review_score,
    rank() over (order by item_stats.gmv desc)  as gmv_rank,
    case
        when item_stats.gmv >= 50000 then 'Top'
        when item_stats.gmv >= 10000 then 'Mid'
        else 'Long tail'
    end                                         as seller_tier
from item_stats
inner join sellers     using (seller_id)
left join order_stats  using (seller_id)
