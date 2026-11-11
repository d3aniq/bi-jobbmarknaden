-- Arbetsgivare som har publicerat dataannonser. Bara juridiska personer:
-- enskilda näringsidkare har personnumret som organisationsnummer och
-- tas aldrig med.

select
    a.organization_number                             as employer_key,
    mode(a.employer_name)                             as employer_name,
    mode(a.employer_type)                             as employer_type
from {{ ref('job_ads') }} a
join {{ ref('fact_job_ad') }} f using (ad_id)
where f.employer_key is not null
group by a.organization_number
