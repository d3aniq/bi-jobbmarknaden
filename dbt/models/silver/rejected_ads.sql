-- Annonser som inte går vidare till job_ads, med orsak. Hellre en synlig
-- lista än att raderna försvinner tyst eller hamnar år 2099 i rapporten.

with chosen as (

    select
        coalesce(original_id, id) as ad_id,
        source_file,
        line_number,
        try_cast(publication_date as timestamp) as published_at
    from {{ source('bronze', 'job_ads') }}
    qualify row_number() over (
        partition by coalesce(original_id, id)
        order by try_cast(publication_date as timestamp), source_file, line_number
    ) = 1

)

select
    ad_id,
    source_file,
    line_number,
    published_at,
    case
        when published_at is null then 'publiceringsdatum saknas eller går inte att tolka'
        else 'publicerad efter filens period'
    end as reason
from chosen
where published_at is null
   or published_at >= {{ file_period_end('source_file') }}
