-- Aggregeringen till fact_ad_volume får inte tappa eller dubbla annonser,
-- och antalet dataannonser ska stämma med fact_job_ad.

with v as (
    select sum(n_ads) as n_ads, sum(n_data_ads) as n_data_ads from {{ ref('fact_ad_volume') }}
),
s as (
    select count(*) as n_ads from {{ ref('job_ads') }} where published_date is not null
),
f as (
    select count(*) as n_data_ads from {{ ref('fact_job_ad') }}
)

select v.n_ads, s.n_ads as silver_ads, v.n_data_ads, f.n_data_ads as fact_data_ads
from v, s, f
where v.n_ads <> s.n_ads or v.n_data_ads <> f.n_data_ads
