-- En rad per annons och term som annonsen nämner.
--
-- Ordlistan (seeds/term_dictionary.csv) har tre delar per term:
--   pattern          det som ska hittas, som helt ord
--   exclude_pattern  finns det här någonstans i annonsen räknas inte träffen
--   require_pattern  måste också finnas i annonsen för att träffen ska räknas
-- Alla mönster körs mot rubrik och beskrivning i gemener.
--
-- Först filtreras annonserna med ett samlat mönster, så att de dyra
-- jämförelserna bara görs för de få procent som kan träffa alls.

{% set b = "[^a-z0-9åäöéü_]" %}

with terms as (

    select
        term_id,
        '(^|{{ b }})(' || pattern || ')({{ b }}|$)' as rx,
        exclude_pattern,
        require_pattern
    from {{ ref('term_dictionary') }}

),

any_term as (

    select '(^|{{ b }})(' || string_agg(pattern, '|') || ')({{ b }}|$)' as rx
    from {{ ref('term_dictionary') }}

),

texts as (

    -- Texten för den rad som silver valde för varje annons
    select
        a.ad_id,
        lower(coalesce(b.headline, '') || ' ' || coalesce(b.description_text, '')) as search_text,
        lower(coalesce(b.headline, ''))                                           as headline_text
    from {{ ref('job_ads') }} a
    join {{ source('bronze', 'job_ads') }} b using (source_file, line_number)

),

candidates as (

    select t.*
    from texts t, any_term
    where regexp_matches(t.search_text, any_term.rx)

)

select
    c.ad_id,
    t.term_id,
    regexp_matches(c.headline_text, t.rx) as in_headline
from candidates c
join terms t
  on regexp_matches(c.search_text, t.rx)
where (t.exclude_pattern is null or not regexp_matches(c.search_text, t.exclude_pattern))
  and (t.require_pattern is null or regexp_matches(c.search_text, t.require_pattern))
