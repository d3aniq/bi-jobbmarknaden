-- En annons kan inte vara publicerad efter den period som filen täcker.
-- (Filerna innehåller däremot annonser publicerade före perioden, de som
-- fortfarande var aktiva.) Sådana rader ska ha hamnat i rejected_ads.

select ad_id, published_at, source_file
from {{ ref('job_ads') }}
where published_at >= {{ file_period_end('source_file') }}
