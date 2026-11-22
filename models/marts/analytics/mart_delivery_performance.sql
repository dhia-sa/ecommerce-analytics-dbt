-- Delivery speed, lateness and its effect on review score, by customer state and month
with orders as (
    select * from {{ ref('fct_orders') }}
    where order_status = 'delivered'
      and delivered_at is not null
      and order_date between cast('{{ var("analysis_start_date") }}' as date)
                         and cast('{{ var("analysis_end_date") }}' as date)
)

select
    cast(date_trunc('month', order_date) as date)                   as order_month,
    customer_state,
    count(*)                                                        as delivered_orders,
    avg(delivery_days)                                              as avg_delivery_days,
    median(delivery_days)                                           as median_delivery_days,
    avg(days_vs_estimate)                                           as avg_days_vs_estimate,
    count(*) filter (where is_late_delivery)                        as late_orders,
    count(*) filter (where is_late_delivery) / count(*)             as late_rate,
    avg(review_score) filter (where not is_late_delivery)           as avg_review_on_time,
    avg(review_score) filter (where is_late_delivery)               as avg_review_late
from orders
group by 1, 2
