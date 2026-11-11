-- Län. Namnen tas från annonserna. Västra Götaland, Stockholm och Skåne
-- särredovisas, resten är "Övriga Sverige".

with named as (

    select region_code, mode(region) as region_name
    from {{ source('bronze', 'job_ads') }}
    where region_code is not null and region is not null
    group by region_code

),

codes as (

    select distinct region_code from {{ ref('job_ads') }} where region_code is not null
    union
    select distinct region_code from {{ ref('employment') }} where region_code <> '00'

)

select
    c.region_code                                    as region_key,
    coalesce(n.region_name,
             case c.region_code when '99' then 'Okänt län (SCB)' else 'Län ' || c.region_code end) as region_name,
    case c.region_code
        when '14' then 'Västra Götaland'
        when '01' then 'Stockholm'
        when '12' then 'Skåne'
        when '90' then 'Ospecificerad'
        when '99' then 'Ospecificerad'
        else 'Övriga Sverige'
    end                                              as region_group,
    c.region_code = '14'                             as is_vastra_gotaland
from codes c
left join named n using (region_code)

union all

select 'XX', 'Län saknas', 'Okänd', false
