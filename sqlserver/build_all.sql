/*
  build_all.sql
  Runs the whole SQL Server build in order. Run it with sqlcmd, which
  understands the :r (include file) commands below:

    sqlcmd -S localhost -U sa -P "<password>" -C -i /repo/sqlserver/build_all.sql

  See docs/setup/sql_server_local_setup.md for the full walkthrough.
*/
:on error exit
:r /repo/sqlserver/01_create_database.sql
:r /repo/sqlserver/02_load_raw.sql
:r /repo/sqlserver/03_build_dw.sql
:r /repo/sqlserver/03b_build_dw_workforce_planning.sql
:r /repo/sqlserver/03c_build_dw_contingent.sql
:r /repo/sqlserver/04_create_reporting_views.sql
:r /repo/sqlserver/04b_create_reporting_views_contingent.sql
:r /repo/sqlserver/05_validate.sql
:r /repo/sqlserver/08_validate_workforce_planning.sql
:r /repo/sqlserver/12_validate_contingent_workforce.sql
