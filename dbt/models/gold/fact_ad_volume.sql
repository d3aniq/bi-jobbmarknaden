-- Fakta: alla annonser, aggregerade per månad, kommun, yrkesgrupp,
-- arbetsgivartyp och källsystem. Nämnaren för andelar ("hur stor del av
-- alla annonser"), utan att modellen behöver bära miljontals rader.

select
    date_trunc('month', a.published_date)::date                         as month_start,
    {{ municipality_key('a.municipality_code', 'a.region_code') }}       as municipality_key,
    {{ ssyk4_key('a.ssyk4') }}                                           as ssyk4_key,
    a.employer_type,
    a.source_system,
    count(*)                                                             as n_ads,
    sum(a.number_of_vacancies)::bigint                                   as n_vacancies,
    count(*) filter (where c.is_data_ad)                                 as n_data_ads,
    count(*) filter (where c.mentions_core_bi)                           as n_core_bi_ads,
    count(*) filter (where c.mentions_power_bi)                          as n_power_bi_ads,
    count(*) filter (where a.remote_work)                                as n_remote_ads
from {{ ref('job_ads') }} a
join {{ ref('ad_classification') }} c using (ad_id)
where a.published_date is not null
group by all
