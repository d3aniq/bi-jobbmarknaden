-- Ordlistan mot JobTechs berikning, per term och år, för alla annonser.
-- Visar hur ofta de två källorna är överens om att en annons nämner en
-- term, och hur ofta bara den ena hittar den.

with d as (
    select ad_id, term_id from {{ ref('ad_term_matches') }}
    where term_id in (select term_id from {{ ref('enrichment_mapping') }})
),

e as (
    select ad_id, term_id from {{ ref('enrichment_term_matches') }}
),

both_sources as (
    select
        coalesce(d.ad_id, e.ad_id)     as ad_id,
        coalesce(d.term_id, e.term_id) as term_id,
        d.ad_id is not null            as in_dictionary,
        e.ad_id is not null            as in_enrichment
    from d
    full outer join e using (ad_id, term_id)
)

select
    b.term_id,
    year(a.published_date)                                           as year,
    count(*) filter (where in_dictionary and in_enrichment)          as n_both,
    count(*) filter (where in_dictionary and not in_enrichment)      as n_dictionary_only,
    count(*) filter (where in_enrichment and not in_dictionary)      as n_enrichment_only
from both_sources b
join {{ ref('job_ads') }} a using (ad_id)
group by all
