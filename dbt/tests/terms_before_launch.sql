-- Ett verktyg kan inte efterfrågas innan det fanns. Träffar före
-- lanseringsåret är nästan alltid ett fel i ordlistan: fel ord med rätt
-- namn. Mer än 2 % av en terms träffar före lansering stoppar bygget.

with hits as (
    select
        m.term_id,
        t.launched_year,
        count(*) as n,
        count(*) filter (where year(a.published_date) < t.launched_year) as n_before
    from {{ ref('ad_term_matches') }} m
    join {{ ref('job_ads') }} a using (ad_id)
    join {{ ref('term_dictionary') }} t using (term_id)
    group by all
)

select *, round(100.0 * n_before / n, 1) as pct_before
from hits
where n_before > 0
  and n_before > 0.02 * n
