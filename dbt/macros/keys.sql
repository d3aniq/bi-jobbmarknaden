{# Nycklar som delas mellan faktatabellerna. Annonser utan kommun får en
   "okänd kommun"-rad i sitt län, och annonser utan län en helt okänd rad,
   så att inga annonser faller bort i en relation. #}

{% macro municipality_key(municipality_code, region_code) -%}
    coalesce({{ municipality_code }}, coalesce({{ region_code }}, 'XX') || 'XX')
{%- endmacro %}

{% macro region_key(region_code) -%}
    coalesce({{ region_code }}, 'XX')
{%- endmacro %}

{% macro ssyk4_key(ssyk4) -%}
    coalesce({{ ssyk4 }}, 'XXXX')
{%- endmacro %}
