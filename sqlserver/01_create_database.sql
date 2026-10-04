/*
  01_create_database.sql
  Creates the ArcadiaHR database and its schemas.

    raw  - CSV files landed as text, exactly as received
    dw   - typed, cleaned warehouse tables (dimensions, facts, reference data, snapshots)
    rpt  - reporting views for Tableau
*/
SET NOCOUNT ON;

IF DB_ID('ArcadiaHR') IS NULL
BEGIN
    CREATE DATABASE ArcadiaHR;
    PRINT 'Created database ArcadiaHR';
END
ELSE
    PRINT 'Database ArcadiaHR already exists';
GO

USE ArcadiaHR;
GO

IF SCHEMA_ID('raw') IS NULL EXEC('CREATE SCHEMA raw');
IF SCHEMA_ID('dw')  IS NULL EXEC('CREATE SCHEMA dw');
IF SCHEMA_ID('rpt') IS NULL EXEC('CREATE SCHEMA rpt');
PRINT 'Schemas ready: raw, dw, rpt';
GO
