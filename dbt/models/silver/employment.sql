-- Anställda per år, län och yrke (SSYK 4) från SCB:s yrkesregister.
--
-- PxWeb-svaret har en rad per cell: key = [region, yrke, år], values = [antal].
-- Kön är utelämnat i frågan och därmed summerat av SCB.
--
-- Två metodbyten finns kvar med flit:
--   YREG60 och YREG60N räknar 16–64 år (RAMS). YREG60BAS räknar alla åldrar (BAS).
--   2020 och 2021 finns i både YREG60N och YREG60BAS.
-- is_preferred väljer en serie per år: RAMS till och med 2019, BAS från 2020.

with raw as (

    select
        regexp_extract(filename, '(YREG[0-9A-Z]+)\.json$', 1) as source_table,
        unnest(data) as cell
    from {{ source('bronze', 'scb_employment') }}

),

cells as (

    select
        source_table,
        cell.key[1]                  as region_code,
        cell.key[2]                  as ssyk4,
        cast(cell.key[3] as integer) as year,
        cell.values[1]               as raw_value
    from raw

)

select
    source_table,
    case when source_table = 'YREG60BAS' then 'BAS, alla åldrar' else 'RAMS, 16–64 år' end as method,
    year,
    region_code,
    ssyk4,
    -- SCB markerar sekretess och saknade värden med punkter och streck
    try_cast(raw_value as integer) as employed,
    raw_value,
    case
        when source_table = 'YREG60BAS' then true
        when year <= 2019 then true
        else false
    end as is_preferred
from cells
