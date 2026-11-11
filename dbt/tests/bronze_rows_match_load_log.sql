-- Bronze ska innehålla exakt de rader som inläsningen räknade i varje fil,
-- och ingen rad får ha misslyckats. Returnerar filer där något inte stämmer.

with logged as (
    select 'annonser' as part, source_file, cast(lines as bigint) as lines,
           cast(parsed as bigint) as parsed, cast(failed as bigint) as failed
    from {{ source('bronze', 'job_ads_load_log') }}
    union all
    select 'komplettering', source_file, cast(lines as bigint), cast(parsed as bigint), cast(failed as bigint)
    from {{ source('bronze', 'location_patch_load_log') }}
),

loaded as (
    select 'annonser' as part, source_file, count(*) as rows_in_bronze
    from {{ source('bronze', 'job_ads') }} group by all
    union all
    select 'komplettering', source_file, count(*)
    from {{ source('bronze', 'location_patch') }} group by all
)

select l.*, b.rows_in_bronze
from logged l
full outer join loaded b using (part, source_file)
where b.rows_in_bronze is null
   or l.lines is null
   or l.failed > 0
   or l.lines <> l.parsed
   or l.parsed <> b.rows_in_bronze
