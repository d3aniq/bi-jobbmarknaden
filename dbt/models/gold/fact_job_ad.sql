-- Fakta: en rad per unik dataannons (se ad_classification för definitionen).
-- Ingen text och inga personuppgifter. Arbetsgivaren finns bara med som
-- nyckel när det är en juridisk person.

select
    a.ad_id,
    a.published_date,
    {{ municipality_key('a.municipality_code', 'a.region_code') }} as municipality_key,
    {{ ssyk4_key('a.ssyk4') }}                                    as ssyk4_key,
    coalesce(a.occupation_concept_id, 'okänd')                    as occupation_key,
    case when a.employer_type in ('privat sektor', 'offentlig sektor')
         then a.organization_number end                           as employer_key,
    a.employer_type,
    a.number_of_vacancies,
    a.remote_work,
    a.experience_required,
    coalesce(a.employment_type, 'Uppgift saknas')                 as employment_type,
    coalesce(a.working_hours, 'Uppgift saknas')                   as working_hours,
    a.scope_min,
    a.scope_max,
    c.n_terms,
    c.mentions_core_bi,
    c.mentions_power_bi,
    c.is_data_occupation,
    coalesce(c.data_role_family, 'Inget datayrke')                as data_role_family,
    a.location_source,
    a.occupation_source
from {{ ref('job_ads') }} a
join {{ ref('ad_classification') }} c using (ad_id)
where c.is_data_ad
