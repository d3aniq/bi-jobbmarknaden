-- Yrkesgrupp (SSYK 2012, 4 siffror). Delad av alla tre faktatabellerna.
-- Benämningen tas från annonserna (vanligaste stavningen). Koder som bara
-- finns hos SCB får koden som benämning.

with from_ads as (

    select ssyk4, mode(ssyk4_label) as ssyk4_label
    from {{ ref('job_ads') }}
    where ssyk4 is not null
    group by ssyk4

),

codes as (

    select ssyk4 from from_ads
    union
    select distinct ssyk4 from {{ ref('employment') }}

)

select
    c.ssyk4                                          as ssyk4_key,
    c.ssyk4,
    coalesce(a.ssyk4_label, 'SSYK ' || c.ssyk4)      as ssyk4_label,
    left(c.ssyk4, 3)                                 as ssyk3,
    left(c.ssyk4, 1)                                 as ssyk1,
    g.ssyk1_label
from codes c
left join from_ads a using (ssyk4)
left join {{ ref('ssyk_major_group') }} g on g.ssyk1::varchar = left(c.ssyk4, 1)

union all

select 'XXXX', null, 'Yrke saknas', null, null, 'Yrke saknas'
