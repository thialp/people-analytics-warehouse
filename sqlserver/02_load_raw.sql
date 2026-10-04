/*
  02_load_raw.sql
  Lands every CSV from data/raw/ into the raw schema as text, the way an
  enterprise landing zone receives files. Types are applied later in 03.

  The repository folder is mounted into the container at /repo (see the setup
  guide), so SQL Server reads the files directly with BULK INSERT.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

DROP TABLE IF EXISTS raw.dim_worker;
CREATE TABLE raw.dim_worker (
    [worker_id]            NVARCHAR(400) NULL,
    [original_hire_date]   NVARCHAR(400) NULL,
    [termination_date]     NVARCHAR(400) NULL,
    [termination_type]     NVARCHAR(400) NULL,
    [worker_type]          NVARCHAR(400) NULL,
    [is_executive_officer] NVARCHAR(400) NULL
);
BULK INSERT raw.dim_worker
FROM '/repo/data/raw/dim_worker.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', ROWTERMINATOR = '0x0a', TABLOCK);
DECLARE @n_dim_worker INT = (SELECT COUNT(*) FROM raw.dim_worker);
PRINT CONCAT('raw.dim_worker', REPLICATE(' ', 22), @n_dim_worker, ' rows');
GO

DROP TABLE IF EXISTS raw.fact_job_history;
CREATE TABLE raw.fact_job_history (
    [job_record_id]        NVARCHAR(400) NULL,
    [worker_id]            NVARCHAR(400) NULL,
    [effective_start_date] NVARCHAR(400) NULL,
    [effective_end_date]   NVARCHAR(400) NULL,
    [action_reason]        NVARCHAR(400) NULL,
    [position_id]          NVARCHAR(400) NULL,
    [department_id]        NVARCHAR(400) NULL,
    [location_id]          NVARCHAR(400) NULL,
    [job_profile_id]       NVARCHAR(400) NULL,
    [grade]                NVARCHAR(400) NULL,
    [fte]                  NVARCHAR(400) NULL
);
BULK INSERT raw.fact_job_history
FROM '/repo/data/raw/fact_job_history.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', ROWTERMINATOR = '0x0a', TABLOCK);
DECLARE @n_fact_job_history INT = (SELECT COUNT(*) FROM raw.fact_job_history);
PRINT CONCAT('raw.fact_job_history', REPLICATE(' ', 16), @n_fact_job_history, ' rows');
GO

DROP TABLE IF EXISTS raw.fact_compensation_history;
CREATE TABLE raw.fact_compensation_history (
    [comp_record_id]           NVARCHAR(400) NULL,
    [worker_id]                NVARCHAR(400) NULL,
    [effective_start_date]     NVARCHAR(400) NULL,
    [effective_end_date]       NVARCHAR(400) NULL,
    [action_reason]            NVARCHAR(400) NULL,
    [transaction_type]         NVARCHAR(400) NULL,
    [currency_code]            NVARCHAR(400) NULL,
    [base_salary_annual_local] NVARCHAR(400) NULL
);
BULK INSERT raw.fact_compensation_history
FROM '/repo/data/raw/fact_compensation_history.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', ROWTERMINATOR = '0x0a', TABLOCK);
DECLARE @n_fact_compensation_history INT = (SELECT COUNT(*) FROM raw.fact_compensation_history);
PRINT CONCAT('raw.fact_compensation_history', REPLICATE(' ', 7), @n_fact_compensation_history, ' rows');
GO

DROP TABLE IF EXISTS raw.dim_department;
CREATE TABLE raw.dim_department (
    [department_id]       NVARCHAR(400) NULL,
    [department_name]     NVARCHAR(400) NULL,
    [sub_function]        NVARCHAR(400) NULL,
    [function]            NVARCHAR(400) NULL,
    [cost_center]         NVARCHAR(400) NULL,
    [effective_from_date] NVARCHAR(400) NULL
);
BULK INSERT raw.dim_department
FROM '/repo/data/raw/dim_department.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', ROWTERMINATOR = '0x0a', TABLOCK);
DECLARE @n_dim_department INT = (SELECT COUNT(*) FROM raw.dim_department);
PRINT CONCAT('raw.dim_department', REPLICATE(' ', 18), @n_dim_department, ' rows');
GO

DROP TABLE IF EXISTS raw.dim_location;
CREATE TABLE raw.dim_location (
    [location_id]   NVARCHAR(400) NULL,
    [city]          NVARCHAR(400) NULL,
    [country_code]  NVARCHAR(400) NULL,
    [country_name]  NVARCHAR(400) NULL,
    [region]        NVARCHAR(400) NULL,
    [currency_code] NVARCHAR(400) NULL,
    [site_type]     NVARCHAR(400) NULL
);
BULK INSERT raw.dim_location
FROM '/repo/data/raw/dim_location.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', ROWTERMINATOR = '0x0a', TABLOCK);
DECLARE @n_dim_location INT = (SELECT COUNT(*) FROM raw.dim_location);
PRINT CONCAT('raw.dim_location', REPLICATE(' ', 20), @n_dim_location, ' rows');
GO

DROP TABLE IF EXISTS raw.dim_job_profile;
CREATE TABLE raw.dim_job_profile (
    [job_profile_id]  NVARCHAR(400) NULL,
    [job_family_code] NVARCHAR(400) NULL,
    [job_family]      NVARCHAR(400) NULL,
    [job_title]       NVARCHAR(400) NULL,
    [grade]           NVARCHAR(400) NULL,
    [grade_level]     NVARCHAR(400) NULL,
    [career_track]    NVARCHAR(400) NULL
);
BULK INSERT raw.dim_job_profile
FROM '/repo/data/raw/dim_job_profile.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', ROWTERMINATOR = '0x0a', TABLOCK);
DECLARE @n_dim_job_profile INT = (SELECT COUNT(*) FROM raw.dim_job_profile);
PRINT CONCAT('raw.dim_job_profile', REPLICATE(' ', 17), @n_dim_job_profile, ' rows');
GO

DROP TABLE IF EXISTS raw.ref_fx_rate_monthly;
CREATE TABLE raw.ref_fx_rate_monthly (
    [currency_code] NVARCHAR(400) NULL,
    [rate_date]     NVARCHAR(400) NULL,
    [usd_per_local] NVARCHAR(400) NULL
);
BULK INSERT raw.ref_fx_rate_monthly
FROM '/repo/data/raw/ref_fx_rate_monthly.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', ROWTERMINATOR = '0x0a', TABLOCK);
DECLARE @n_ref_fx_rate_monthly INT = (SELECT COUNT(*) FROM raw.ref_fx_rate_monthly);
PRINT CONCAT('raw.ref_fx_rate_monthly', REPLICATE(' ', 13), @n_ref_fx_rate_monthly, ' rows');
GO

DROP TABLE IF EXISTS raw.ref_fx_rate_constant;
CREATE TABLE raw.ref_fx_rate_constant (
    [rate_set]      NVARCHAR(400) NULL,
    [currency_code] NVARCHAR(400) NULL,
    [usd_per_local] NVARCHAR(400) NULL
);
BULK INSERT raw.ref_fx_rate_constant
FROM '/repo/data/raw/ref_fx_rate_constant.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', ROWTERMINATOR = '0x0a', TABLOCK);
DECLARE @n_ref_fx_rate_constant INT = (SELECT COUNT(*) FROM raw.ref_fx_rate_constant);
PRINT CONCAT('raw.ref_fx_rate_constant', REPLICATE(' ', 12), @n_ref_fx_rate_constant, ' rows');
GO

DROP TABLE IF EXISTS raw.ref_fringe_rate;
CREATE TABLE raw.ref_fringe_rate (
    [country_code] NVARCHAR(400) NULL,
    [fiscal_year]  NVARCHAR(400) NULL,
    [fringe_rate]  NVARCHAR(400) NULL
);
BULK INSERT raw.ref_fringe_rate
FROM '/repo/data/raw/ref_fringe_rate.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', ROWTERMINATOR = '0x0a', TABLOCK);
DECLARE @n_ref_fringe_rate INT = (SELECT COUNT(*) FROM raw.ref_fringe_rate);
PRINT CONCAT('raw.ref_fringe_rate', REPLICATE(' ', 17), @n_ref_fringe_rate, ' rows');
GO

DROP TABLE IF EXISTS raw.ref_salary_range;
CREATE TABLE raw.ref_salary_range (
    [fiscal_year]   NVARCHAR(400) NULL,
    [grade]         NVARCHAR(400) NULL,
    [country_code]  NVARCHAR(400) NULL,
    [currency_code] NVARCHAR(400) NULL,
    [range_min]     NVARCHAR(400) NULL,
    [range_mid]     NVARCHAR(400) NULL,
    [range_max]     NVARCHAR(400) NULL
);
BULK INSERT raw.ref_salary_range
FROM '/repo/data/raw/ref_salary_range.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', ROWTERMINATOR = '0x0a', TABLOCK);
DECLARE @n_ref_salary_range INT = (SELECT COUNT(*) FROM raw.ref_salary_range);
PRINT CONCAT('raw.ref_salary_range', REPLICATE(' ', 16), @n_ref_salary_range, ' rows');
GO
