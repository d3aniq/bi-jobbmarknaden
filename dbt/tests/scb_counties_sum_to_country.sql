-- Summan av länen ska vara exakt riket, för varje tabell, år och yrke.
-- SCB har ett eget "län" för okänd arbetsplats (99), så summan ska gå
-- jämnt upp. En avvikelse betyder att en cell tappats eller tolkats fel.

with r as (
    select
        source_table, year, ssyk4,
        sum(employed) filter (where region_code <> '00') as sum_counties,
        max(employed) filter (where region_code = '00')  as country
    from {{ ref('employment') }}
    group by all
)

select * from r
where sum_counties is distinct from country
