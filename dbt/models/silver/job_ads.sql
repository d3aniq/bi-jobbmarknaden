-- En rad per unik annons.
--
-- Här fattas besluten: tider tolkas, yrke och ort plockas ur JSON,
-- 2018–2019 kompletteras med ort och yrke från JobTechs rättade filer,
-- arbetsgivaren klassas och återpublicerade annonser slås ihop.
--
-- Annonstexten tas inte med hit. Ordlistan (ad_term_matches) läser den
-- direkt från bronze för den rad som valts här, så att DuckDB-filen inte
-- behöver bära miljontals annonstexter. Gold innehåller ingen text.

with src as (

    select * from {{ source('bronze', 'job_ads') }}

),

patch as (

    -- Samma annons kan finnas flera gånger i kompletteringen. Ta den med
    -- ort, och bland dem den tidigast publicerade.
    select *
    from {{ source('bronze', 'location_patch') }}
    where original_id is not null
    qualify row_number() over (
        partition by original_id
        order by (municipality_code is null), publication_date, source_file, line_number
    ) = 1

),

parsed as (

    select
        coalesce(src.original_id, src.id)                                   as ad_id,
        src.original_id,
        src.source_file,
        src.line_number,

        try_cast(src.publication_date as timestamp)                          as published_at,
        try_cast(src.last_publication_date as timestamp)                     as last_published_at,
        src.headline,
        src.description_text is not null                                     as has_description,

        -- Yrke: annonsens egen uppgift i första hand, annars kompletteringen
        coalesce(json_extract_string(src.occupation_json, '$[0].concept_id'),
                 json_extract_string(patch.occupation_json, '$[0].concept_id'))            as occupation_concept_id,
        coalesce(json_extract_string(src.occupation_json, '$[0].label'),
                 json_extract_string(patch.occupation_json, '$[0].label'))                 as occupation_label,
        coalesce(json_extract_string(src.occupation_group_json, '$[0].legacy_ams_taxonomy_id'),
                 json_extract_string(patch.occupation_group_json, '$[0].legacy_ams_taxonomy_id')) as ssyk4,
        coalesce(json_extract_string(src.occupation_group_json, '$[0].label'),
                 json_extract_string(patch.occupation_group_json, '$[0].label'))           as ssyk4_label,
        coalesce(json_extract_string(src.occupation_field_json, '$[0].label'),
                 json_extract_string(patch.occupation_field_json, '$[0].label'))           as occupation_field,
        case
            when json_extract_string(src.occupation_group_json, '$[0].legacy_ams_taxonomy_id') is not null then 'annons'
            when json_extract_string(patch.occupation_group_json, '$[0].legacy_ams_taxonomy_id') is not null then 'komplettering'
            else 'saknas'
        end                                                                  as occupation_source,

        -- Ort: annonsen, kompletteringen, eller länet härlett ur kommunkoden
        coalesce(src.municipality_code, patch.municipality_code)            as municipality_code,
        coalesce(src.municipality, patch.municipality)                      as municipality,
        coalesce(src.region_code, patch.region_code,
                 left(coalesce(src.municipality_code, patch.municipality_code), 2)) as region_code,
        case
            when src.municipality_code is not null then 'annons'
            when patch.municipality_code is not null then 'komplettering'
            when src.region_code is not null then 'bara län'
            else 'saknas'
        end                                                                  as location_source,

        json_extract_string(src.employment_type_json, '$[0].label')          as employment_type,
        json_extract_string(src.working_hours_type_json, '$.label')          as working_hours,
        json_extract_string(src.duration_json, '$.label')                    as duration,
        try_cast(json_extract_string(src.scope_of_work_json, '$.min') as integer) as scope_min,
        try_cast(json_extract_string(src.scope_of_work_json, '$.max') as integer) as scope_max,
        try_cast(src.remote_work as boolean)                                 as remote_work,
        try_cast(src.experience_required as boolean)                         as experience_required,
        coalesce(try_cast(src.number_of_vacancies as integer), 1)            as number_of_vacancies,
        src.detected_language,

        -- Arbetsgivare. En enskild näringsidkares organisationsnummer är
        -- personnumret: siffra 3–4 är då en månad (01–12). Juridiska
        -- personer har 20 eller högre där.
        src.employer_organization_number                                    as organization_number,
        case
            when src.employer_organization_number is null then 'okänd'
            when not regexp_full_match(src.employer_organization_number, '[0-9]{10}') then 'okänd'
            when substr(src.employer_organization_number, 3, 1) in ('0', '1') then 'enskild näringsidkare'
            when left(src.employer_organization_number, 1) = '2' then 'offentlig sektor'
            else 'privat sektor'
        end                                                                  as employer_type,
        src.employer_name

    from src
    left join patch
        on patch.original_id = src.original_id
       and src.municipality_code is null

)

select
    *,
    cast(published_at as date) as published_date,
    count(*) over (partition by ad_id) as n_source_rows
from parsed
qualify row_number() over (partition by ad_id order by published_at, source_file, line_number) = 1
