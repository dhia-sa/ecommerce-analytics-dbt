-- Monthly acquisition cohorts: share of customers who order again N months after their first order
with orders as (
    select
        customer_unique_id,
        cast(date_trunc('month', order_date) as date) as order_month
    from {{ ref('fct_orders') }}
    where is_valid_order
      and order_date between cast('{{ var("analysis_start_date") }}' as date)
                         and cast('{{ var("analysis_end_date") }}' as date)
),

first_orders as (
    select customer_unique_id, min(order_month) as cohort_month
    from orders
    group by 1
),

activity as (
    select distinct
        first_orders.cohort_month,
        orders.customer_unique_id,
        date_diff('month', first_orders.cohort_month, orders.order_month) as months_since_first
    from orders
    inner join first_orders using (customer_unique_id)
),

cohort_size as (
    select cohort_month, count(*) as cohort_customers
    from first_orders
    group by 1
)

select
    activity.cohort_month,
    activity.months_since_first,
    cohort_size.cohort_customers,
    count(distinct activity.customer_unique_id)                           as active_customers,
    count(distinct activity.customer_unique_id) / cohort_size.cohort_customers as retention_rate
from activity
inner join cohort_size using (cohort_month)
group by 1, 2, 3
