-- Den tredje källan: JobTechs egen automatiska tolkning av annonstexten
-- (keywords.enriched.skill). Etiketterna mappas till ordlistans termer
-- med seeds/enrichment_mapping.csv, så att de två går att jämföra.
--
-- Bara den rad som silver valde för varje annons används (samma fil och
-- radnummer), så att återpublicerade annonser inte räknas två gånger.

with chosen as (

    select ad_id, source_file, line_number
    from {{ ref('job_ads') }}

),

skills as (

    select
        c.ad_id,
        unnest(json_extract_string(b.keywords_json, '$.enriched.skill[*]')) as enrichment_label
    from {{ source('bronze', 'job_ads') }} b
    join chosen c using (source_file, line_number)

)

select distinct
    s.ad_id,
    m.term_id
from skills s
join {{ ref('enrichment_mapping') }} m using (enrichment_label)
