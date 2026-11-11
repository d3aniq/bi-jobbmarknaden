{# Använd schemanamnet som det står (silver, gold) i stället för dbt:s
   standard target_schema + "_" + schema. #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name if custom_schema_name is not none else target.schema }}
{%- endmacro %}
