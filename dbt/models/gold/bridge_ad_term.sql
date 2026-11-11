-- Brygga: dataannons × term. Löser många-till-många mellan annonser och
-- termer utan dubbelriktad filtrering i hela modellen.

select
    m.ad_id,
    m.term_id,
    m.in_headline
from {{ ref('ad_term_matches') }} m
join {{ ref('fact_job_ad') }} f using (ad_id)
