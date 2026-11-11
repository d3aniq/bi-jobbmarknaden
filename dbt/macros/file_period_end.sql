{# Första dagen efter den period som en JobTech-fil täcker, plus en dags
   marginal (filerna slutar ibland exakt vid midnatt).
   "2024_beta1_jsonl.zip" -> 2025-01-02, "2026-Q2_beta1_jsonl.zip" -> 2026-07-02 #}
{% macro file_period_end(source_file) -%}
    (case
        when regexp_matches({{ source_file }}, '^[0-9]{4}-Q[1-4]')
            then make_date(left({{ source_file }}, 4)::integer, 1, 1)
                 + to_months(3 * substr({{ source_file }}, 7, 1)::integer)
        else make_date(left({{ source_file }}, 4)::integer + 1, 1, 1)
     end + interval 1 day)
{%- endmacro %}
