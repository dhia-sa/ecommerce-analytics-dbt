-- A few orders have more than one review. Keep the most recently answered one,
-- so downstream models get exactly one review per order.
with reviews as (
    select * from {{ ref('stg_olist__order_reviews') }}
)

select *
from reviews
qualify row_number() over (
    partition by order_id
    order by review_answered_at desc, review_created_at desc, review_id
) = 1
