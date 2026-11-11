-- Datumdimension från första till sista publiceringsdag.

with bounds as (

    select
        date_trunc('year', min(published_date))::date as first_day,
        (date_trunc('year', max(published_date)) + interval 1 year - interval 1 day)::date as last_day
    from {{ ref('job_ads') }}

),

days as (

    select unnest(generate_series(first_day, last_day, interval 1 day))::date as date
    from bounds

)

select
    date,
    year(date)                                         as year,
    quarter(date)                                      as quarter,
    year(date) || '-K' || quarter(date)                as year_quarter,
    year(date) * 10 + quarter(date)                    as year_quarter_sort,
    month(date)                                        as month,
    date_trunc('month', date)::date                    as month_start,
    strftime(date, '%Y-%m')                            as year_month,
    isodow(date)                                       as weekday_number,
    weekofyear(date)                                   as iso_week,
    isodow(date) >= 6                                  as is_weekend
from days
