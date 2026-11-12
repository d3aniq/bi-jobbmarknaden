{# Textkonstant i SQL med enkla citattecken skyddade. #}
{% macro sql_string(s) -%}
    '{{ s | replace("'", "''") }}'
{%- endmacro %}
