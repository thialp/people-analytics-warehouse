/*
  custom_sql_seat_corridors.sql
  Tableau Custom SQL for Dashboard #3, Workforce Planning (SQL Server, database ArcadiaHR).
  Seat corridors: one row per fiscal quarter x from office x to office, 821 rows.

  Reads the reporting view rpt.vw_seat_corridors (built by sqlserver/04_create_reporting_views.sql
  from the seat layer in 03b). The columns are listed so the data source documents itself and
  keeps the warehouse names (data dictionary: docs/warehouse/data_dictionary.md); the view has
  the same columns as the DuckDB mart, so a workbook can switch with Replace Data Source.

  Grain: one row per QUARTER x FROM OFFICE x TO OFFICE, for backfills refilled in ANOTHER
  office only (same-office refills are not in this table): where the seat sat when its prior
  incumbent left vs where it was refilled. location_change separates moves inside a country
  from moves across a border. Sum seats over quarters and offices freely (FY26: 467 seats =
  410 within a country + 57 across a border).

  Checked row for row against the DuckDB mart by sqlserver/check_tsql_in_duckdb.py.
  Tableau rules: one SELECT, no CTEs, no ORDER BY, block comments only.
  Arcadia Systems is fictional and all data is synthetic.
*/
SELECT
    v.fiscal_year,
    v.fiscal_quarter_label,
    v.location_change,
    v.from_location_id,
    v.from_office_name,
    v.from_city,
    v.from_country_code,
    v.from_country_name,
    v.from_latitude,
    v.from_longitude,
    v.from_pay_zone,
    v.to_location_id,
    v.to_office_name,
    v.to_city,
    v.to_country_code,
    v.to_country_name,
    v.to_latitude,
    v.to_longitude,
    v.to_pay_zone,
    v.seats,
    v.seats_levelled_down,
    v.seats_levelled_up,
    v.seats_relocated_for_backfill,
    v.pay_change_usd_constant,
    v.location_effect_usd_constant
FROM rpt.vw_seat_corridors AS v
