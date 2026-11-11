-- Kommun, med län som nyckel mot dim_region. Varje län får en rad för
-- annonser utan kommun, och det finns en rad för annonser helt utan ort.

with named as (

    select municipality_code, mode(municipality) as municipality_name, mode(region_code) as region_code
    from {{ ref('job_ads') }}
    where municipality_code is not null
    group by municipality_code

),

unknown_in_region as (

    select region_key || 'XX' as municipality_key, region_key, region_name
    from {{ ref('dim_region') }}

)

select
    n.municipality_code                               as municipality_key,
    coalesce(n.municipality_name, 'Kommun ' || n.municipality_code) as municipality_name,
    {{ region_key('n.region_code') }}                 as region_key,
    g.municipality_code is not null                   as is_gothenburg_region
from named n
left join {{ ref('gothenburg_region') }} g on g.municipality_code::varchar = n.municipality_code

union all

select municipality_key, region_name || ', kommun saknas', region_key, false
from unknown_in_region
