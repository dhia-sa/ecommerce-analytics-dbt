-- Monthly GMV, orders, AOV and customers by product category
with items as (
    select * from {{ ref('fct_order_items') }}
    where order_status not in ('canceled', 'unavailable')
      and order_date between cast('{{ var("analysis_start_date") }}' as date)
                         and cast('{{ var("analysis_end_date") }}' as date)
)

select
    cast(date_trunc('month', order_date) as date)  as order_month,
    product_category,
    count(distinct order_id)                       as orders,
    count(*)                                       as items_sold,
    count(distinct customer_unique_id)             as customers,
    sum(price)                                     as gmv,
    sum(freight_value)                             as freight_revenue,
    sum(item_total)                                as total_revenue,
    sum(price) / count(distinct order_id)          as avg_order_value
from items
group by 1, 2
