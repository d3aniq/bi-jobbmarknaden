-- Ort och yrke ska finnas för minst 90 % av annonserna varje år, efter
-- kompletteringen för 2018–2019. Utan kompletteringen saknar de två åren
-- ort och yrke helt, och det här testet är det som fångar det.
--
-- Gränsen är 10 % och inte 5 %: 2020 saknar kommun i cirka 7 % av
-- annonserna, och JobTech har inte rättat det året. Det redovisas i
-- rapporten i stället för att döljas av en lägre tröskel.

select
    year(published_date) as year,
    count(*) as n,
    round(100.0 * count(*) filter (where location_source = 'saknas') / count(*), 1) as pct_no_location,
    round(100.0 * count(*) filter (where occupation_source = 'saknas') / count(*), 1) as pct_no_occupation
from {{ ref('job_ads') }}
group by 1
having count(*) filter (where location_source = 'saknas') > 0.10 * count(*)
    or count(*) filter (where occupation_source = 'saknas') > 0.10 * count(*)
