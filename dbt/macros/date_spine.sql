{% macro date_spine(start_date, end_date) %}
/*
  Generates a contiguous series of dates between start_date and end_date.
  Usage: {{ date_spine('2024-01-01', '2024-12-31') }}
*/
select
    (generate_series(
        {{ start_date }}::date,
        {{ end_date }}::date,
        '1 day'::interval
    ))::date as date_day
{% endmacro %}
