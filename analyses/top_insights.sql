-- Ad-hoc queries used for the README insights. Compile with `dbt compile -s top_insights`
-- or paste into the DuckDB CLI: duckdb ecommerce.duckdb

-- 1. Review score: late vs on-time deliveries
select
    is_late_delivery,
    count(*)            as orders,
    avg(review_score)   as avg_review_score
from {{ ref('fct_orders') }}
where is_late_delivery is not null
group by 1
