with date_spine as (
    {{ dbt_utils.date_spine(
        datepart = "day",
        start_date = "cast('2016-01-01' as date)",
        end_date = "cast('2019-01-01' as date)"
    ) }}
)

select
    cast(date_day as date)                          as date_day,
    year(date_day)                                  as year,
    quarter(date_day)                               as quarter,
    month(date_day)                                 as month,
    strftime(date_day, '%B')                        as month_name,
    cast(date_trunc('month', date_day) as date)     as month_start,
    weekofyear(date_day)                            as week_of_year,
    isodow(date_day)                                as day_of_week,      -- 1 = Monday
    strftime(date_day, '%A')                        as day_name,
    isodow(date_day) in (6, 7)                      as is_weekend
from date_spine
