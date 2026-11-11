-- DBT är också dialektisk beteendeterapi. Efter undantagen i ordlistan
-- får ingen dbt-träff finnas i en annons inom hälso- och sjukvård eller
-- socialt arbete. Annars räknas terapi som datateknik.

select a.ad_id, a.occupation_label, a.ssyk4, a.occupation_field
from {{ ref('ad_term_matches') }} m
join {{ ref('job_ads') }} a using (ad_id)
where m.term_id = 'dbt'
  and (
        a.occupation_field in ('Hälso- och sjukvård', 'Socialt arbete')
     or a.ssyk4 like '22%'      -- hälso- och sjukvårdsyrken
     or a.ssyk4 like '2634%'    -- psykologer och psykoterapeuter
     or a.ssyk4 like '3412%'    -- behandlingsassistenter och socialpedagoger
  )
