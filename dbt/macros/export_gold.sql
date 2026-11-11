{# Skriver alla gold-tabeller till Parquet, en fil per tabell, för Power BI.

     dbt run-operation export_gold --args "{path: ../powerbi/data}"

   Gold innehåller ingen annonstext och inga personuppgifter, och
   filerna är små nog att checka in. Då kan vem som helst öppna
   rapporten utan att köra pipelinen. #}

{% macro export_gold(path) %}
    {% set tables = run_query("select table_name from information_schema.tables where table_schema = 'gold' order by 1") %}
    {% for row in tables.rows %}
        {% set t = row[0] %}
        {% do run_query("copy gold." ~ t ~ " to '" ~ path ~ "/" ~ t ~ ".parquet' (format parquet, compression zstd)") %}
        {{ log("exporterad: " ~ t, info=true) }}
    {% endfor %}
{% endmacro %}
