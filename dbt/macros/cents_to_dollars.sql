{% macro cents_to_dollars(column_name) %}
    ({{ column_name }}::numeric / 100.0)
{% endmacro %}
