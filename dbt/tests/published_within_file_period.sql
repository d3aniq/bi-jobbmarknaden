-- En annons kan inte vara publicerad efter den period som filen täcker.
-- (Filerna innehåller däremot annonser publicerade före perioden, de
-- som fortfarande var aktiva.) Filerna slutar ibland exakt vid midnatt
-- efter sista dagen, så en dag tolereras.

with periods as (
    select
        ad_id,
        published_at,
        source_file,
        regexp_extract(source_file, '^([0-9]{4})(-Q([1-4]))?', 1)::integer as y,
        nullif(regexp_extract(source_file, '^([0-9]{4})(-Q([1-4]))?', 3), '')::integer as q
    from {{ ref('job_ads') }}
)

select *
from periods
where published_at >= case
        when q is null then make_date(y + 1, 1, 1)
        else make_date(y, 1, 1) + to_months(3 * q)
      end + interval 1 day
