-- Inget i gold får likna en personuppgift: personnummer, e-postadress
-- eller telefonnummer. Kontrollen körs mot varje textkolumn som kan bära
-- fritext från källan. Returnerar de rader som bryter mot regeln.

with texts as (
    select 'dim_employer.employer_name' as col, employer_name as val from {{ ref('dim_employer') }}
    union all
    select 'dim_employer.employer_key', employer_key from {{ ref('dim_employer') }}
    union all
    select 'dim_occupation.occupation_label', occupation_label from {{ ref('dim_occupation') }}
    union all
    select 'dim_municipality.municipality_name', municipality_name from {{ ref('dim_municipality') }}
    union all
    select 'fact_job_ad.employer_key', employer_key from {{ ref('fact_job_ad') }}
)

select col, val
from texts
where val is not null
  and (
        regexp_matches(val, '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')        -- e-post
     or regexp_matches(val, '(^|[^0-9])(19|20)?[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[-+]?[0-9]{4}([^0-9]|$)')  -- personnummer
     or regexp_matches(val, '(^|[^0-9])(\+46|0)[1-9][0-9]{0,2}[- ]?[0-9]{2,3}[ ]?[0-9]{2}[ ]?[0-9]{2}([^0-9]|$)')      -- telefon
  )
  -- organisationsnummer för juridiska personer ser ut som personnummer
  -- men har 20 eller högre på plats 3–4
  and not (col like '%employer_key' and substr(val, 3, 1) not in ('0', '1'))
