-- En rad per annons: vad den handlar om enligt två av de tre källorna.
--
--   Ordlistan:  vilka termer annonsen nämner (ad_term_matches)
--   Yrkesvalet: om arbetsgivarens yrke är ett datayrke (occupation_rules)
--
-- En annons är en dataannons om den nämner en BI-kärnterm (kategorier med
-- is_core_bi i term_category) eller om yrket är ett datayrke. Bara SQL,
-- Python, Excel eller ett moln räcker inte: då skulle varje
-- utvecklar- och kontorsannons räknas. Dataannonser kommer med i
-- fact_job_ad. Alla annonser kommer med i fact_ad_volume.

with term_flags as (

    select
        m.ad_id,
        count(*)                                        as n_terms,
        bool_or(c.is_core_bi)                           as mentions_core_bi,
        bool_or(m.term_id = 'power_bi')                 as mentions_power_bi
    from {{ ref('ad_term_matches') }} m
    join {{ ref('term_dictionary') }} t using (term_id)
    join {{ ref('term_category') }} c using (category)
    group by m.ad_id

),

occupation_family as (

    select
        a.ad_id,
        r.data_role_family
    from {{ ref('job_ads') }} a
    join {{ ref('occupation_rules') }} r
      on regexp_matches(lower(a.occupation_label), r.pattern)
    qualify row_number() over (partition by a.ad_id order by r.rule_order) = 1

)

select
    a.ad_id,
    coalesce(t.n_terms, 0)                      as n_terms,
    coalesce(t.mentions_core_bi, false)         as mentions_core_bi,
    coalesce(t.mentions_power_bi, false)        as mentions_power_bi,
    o.data_role_family,
    o.data_role_family is not null              as is_data_occupation,
    (coalesce(t.mentions_core_bi, false) or o.data_role_family is not null) as is_data_ad
from {{ ref('job_ads') }} a
left join term_flags t using (ad_id)
left join occupation_family o using (ad_id)
