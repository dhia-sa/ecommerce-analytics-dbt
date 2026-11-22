-- By definition every customer is active in their first month, so month 0 retention must be 100%
select *
from {{ ref('mart_cohort_retention') }}
where months_since_first = 0
  and retention_rate <> 1
