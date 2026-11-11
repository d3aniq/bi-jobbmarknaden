-- Yrkesbenämning (det arbetsgivaren valde), bara för dataannonserna.

select
    f.occupation_key,
    mode(a.occupation_label)                              as occupation_label,
    mode(a.ssyk4)                                         as ssyk4,
    mode(f.data_role_family)                              as data_role_family
from {{ ref('fact_job_ad') }} f
join {{ ref('job_ads') }} a using (ad_id)
group by f.occupation_key
