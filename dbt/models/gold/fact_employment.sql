-- Fakta: anställda per år, län och yrkesgrupp (SCB). Bara den föredragna
-- serien per år (se silver.employment), och bara län, inte riket.
-- Kopplas till annonserna via år, län och SSYK 4 i DAX.

select
    year,
    region_code   as region_key,
    ssyk4         as ssyk4_key,
    employed,
    method,
    source_table
from {{ ref('employment') }}
where is_preferred
  and region_code <> '00'
  and employed is not null
