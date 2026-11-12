-- depends_on: {{ ref('term_dictionary') }}
-- En rad per annons och term som annonsen nämner.
--
-- Ordlistan (seeds/term_dictionary.csv) har tre delar per term:
--   pattern          det som ska hittas, som helt ord (reguljärt uttryck)
--   exclude_pattern  finns det här någonstans i annonsen räknas inte träffen
--   require_pattern  måste också finnas i annonsen för att träffen ska räknas
-- Alla mönster körs mot rubrik och beskrivning i gemener.
--
-- Prestanda: om mönstret läses från en kolumn kompilerar DuckDB om det
-- reguljära uttrycket för varje rad. Mot 8,7 miljoner annonser tog det
-- över en timme. Här läser dbt ordlistan när modellen körs och skriver
-- in varje terms mönster som en konstant, en fråga per term. Samma
-- träffar, cirka 50 gånger snabbare (uppmätt på 100 000 annonser).
--
-- Varje term prövas först utan ordgräns (billigt), och bara där det
-- träffar med ordgräns (dyrare).

{% set b = "[^a-z0-9åäöéü_]" %}

{% if execute %}
    {% set terms = run_query(
        "select term_id, pattern, exclude_pattern, require_pattern from "
        ~ ref('term_dictionary') ~ " order by term_id"
    ).rows %}
{% else %}
    {% set terms = [] %}
{% endif %}


with texts as (

    -- Texten för den rad som silver valde för varje annons
    select
        a.ad_id,
        lower(coalesce(b.headline, '') || ' ' || coalesce(b.description_text, '')) as search_text,
        lower(coalesce(b.headline, ''))                                           as headline_text
    from {{ ref('job_ads') }} a
    join {{ source('bronze', 'job_ads') }} b using (source_file, line_number)

),

candidates as (

    -- Annonser som kan träffa minst en term, med ett samlat mönster
    select *
    from texts
    where regexp_matches(
        search_text,
        {{ sql_string("(^|" ~ b ~ ")(" ~ (terms | map(attribute=1) | join("|")) ~ ")(" ~ b ~ "|$)") }}
    )

)

{% for t in terms %}
{% set rx = "(^|" ~ b ~ ")(" ~ t[1] ~ ")(" ~ b ~ "|$)" %}
select
    ad_id,
    '{{ t[0] }}' as term_id,
    regexp_matches(headline_text, {{ sql_string(rx) }}) as in_headline
from candidates
where regexp_matches(search_text, {{ sql_string(t[1]) }})
  and regexp_matches(search_text, {{ sql_string(rx) }})
  {% if t[2] %}and not regexp_matches(search_text, {{ sql_string(t[2]) }}){% endif %}
  {% if t[3] %}and regexp_matches(search_text, {{ sql_string(t[3]) }}){% endif %}
{% if not loop.last %}union all{% endif %}
{% endfor %}

{% if terms | length == 0 %}
select null::varchar as ad_id, null::varchar as term_id, null::boolean as in_headline where false
{% endif %}
