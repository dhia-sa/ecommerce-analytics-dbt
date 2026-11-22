-- RFM segmentation per customer, measured as of the end of the analysis window
with orders as (
    select * from {{ ref('fct_orders') }}
    where is_valid_order
      and order_date between cast('{{ var("analysis_start_date") }}' as date)
                         and cast('{{ var("analysis_end_date") }}' as date)
),

rfm_base as (
    select
        customer_unique_id,
        date_diff(
            'day',
            max(order_date),
            cast('{{ var("analysis_end_date") }}' as date)
        )                         as recency_days,
        count(distinct order_id)  as frequency,
        sum(order_value)          as monetary
    from orders
    group by 1
),

scored as (
    select
        *,
        ntile(5) over (order by recency_days desc)  as r_score,  -- 5 = most recent
        -- most customers buy only once, so frequency is scored on fixed buckets instead of ntile
        case
            when frequency >= 4 then 5
            when frequency = 3  then 4
            when frequency = 2  then 3
            else 1
        end                                          as f_score,
        ntile(5) over (order by monetary)            as m_score  -- 5 = highest spend
    from rfm_base
)

select
    *,
    r_score::varchar || f_score::varchar || m_score::varchar  as rfm_code,
    case
        when r_score >= 4 and f_score >= 3                    then 'Champions'
        when f_score >= 3                                     then 'Loyal'
        when r_score >= 4 and m_score >= 4                    then 'Big Spenders - Recent'
        when r_score >= 4                                     then 'New / Promising'
        when r_score = 3                                      then 'Needs Attention'
        when r_score <= 2 and m_score >= 4                    then 'At Risk - High Value'
        else                                                       'Hibernating'
    end                                                       as rfm_segment
from scored
