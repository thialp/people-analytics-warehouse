/*
  04c_create_reporting_views_reconciliation.sql
  Release 4: the reporting views of Dashboard #4, Contingent Workforce Reconciliation. Runs after 03d.

    rpt.vw_cw_gap_close        every gap at every month-end close, with its flag, risk, place,
                               cause, group (Bridgeway's billed cost center) and Helix ticket
    rpt.vw_cw_gap_rate_close   the gap rate's numerator and denominator per close x cost center
    rpt.vw_itsm_ticket_close   Helix tickets open at each close, placed for the ticket card

  Thin reads of the dw tables 03d builds, in the DuckDB marts' column names, so a workbook built on
  the data/marts CSV files can switch to SQL Server with Data > Replace Data Source. Checked row for row
  against the DuckDB marts by sqlserver/check_tsql_in_duckdb.py.
  Arcadia Systems, Keystone HR, Bridgeway VMS and Helix Service Desk are fictional; all data is synthetic.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

/* Dashboard #4: every gap at every month-end close (Jun 2021 to Jun 2026), with its flag, risk, place, cause, group and ticket */
CREATE OR ALTER VIEW rpt.vw_cw_gap_close AS
SELECT
    MonthEndDate                 AS month_end_date,
    CloseLabel                   AS close_label,
    IsLatestClose                AS is_latest_close,
    GapID                        AS gap_id,
    ContractorKey                AS contractor_key,
    BwWorkerID                   AS bw_worker_id,
    PersonID                     AS person_id,
    ContractorName               AS contractor_name,
    CwType                       AS cw_type,
    SupplierName                 AS supplier_name,
    FlagCode                     AS flag_code,
    FlagName                     AS flag_name,
    FlagLabel                    AS flag_label,
    FlagCount                    AS flag_count,
    FlagRank                     AS flag_rank,
    FlagCountPriorClose          AS flag_count_prior_close,
    FlagRankPriorClose           AS flag_rank_prior_close,
    FlagCountYearAgo             AS flag_count_year_ago,
    FlagRankYearAgo              AS flag_rank_year_ago,
    Risk                         AS risk,
    RiskOrder                    AS risk_order,
    Place                        AS place,
    PlaceOrder                   AS place_order,
    PlaceLabel                   AS place_label,
    CauseCode                    AS cause_code,
    CauseName                    AS cause_name,
    RootCauseCode                AS root_cause_code,
    TimingClass                  AS timing_class,
    IsCounted                    AS is_counted,
    SinceDate                    AS since_date,
    DaysOpen                     AS days_open,
    OpenBand                     AS open_band,
    IsOver90Days                 AS is_over_90_days,
    DaysSinceEnd                 AS days_since_end,
    WasOpenPriorClose            AS was_open_prior_close,
    FixedDayAfterClose           AS fixed_day_after_close,
    Items                        AS items,
    ServiceOrderID               AS service_order_id,
    FeedEventID                  AS feed_event_id,
    PositionID                   AS position_id,
    CostCenterID                 AS cost_center_id,
    DepartmentID                 AS department_id,
    DepartmentName               AS department_name,
    FunctionName                 AS function_name,
    CountryCode                  AS country_code,
    CountryName                  AS country_name,
    KeystoneShows                AS keystone_shows,
    BridgewayHas                 AS bridgeway_has,
    Evidence                     AS evidence,
    NextStep                     AS next_step,
    TicketNumber                 AS ticket_number,
    TicketTitle                  AS ticket_title,
    TicketState                  AS ticket_state,
    TicketStatus                 AS ticket_status,
    HasTicket                    AS has_ticket
FROM dw.CwGapClose;
GO

/* Dashboard #4: the gap rate per close x cost center, against the 3% target */
CREATE OR ALTER VIEW rpt.vw_cw_gap_rate_close AS
SELECT
    MonthEndDate                 AS month_end_date,
    CloseLabel                   AS close_label,
    IsLatestClose                AS is_latest_close,
    CostCenterID                 AS cost_center_id,
    DepartmentID                 AS department_id,
    DepartmentName               AS department_name,
    FunctionName                 AS function_name,
    CountryCode                  AS country_code,
    CountryName                  AS country_name,
    ContractorsWorking           AS contractors_working,
    ContractorsWorkingKeystone   AS contractors_working_keystone,
    WorkingBridgewayOnly         AS working_bridgeway_only,
    WorkingKeystoneOnly          AS working_keystone_only,
    ContractorsWithGap           AS contractors_with_gap,
    ContractorsWithAnyGap        AS contractors_with_any_gap,
    Gaps                         AS gaps,
    GapsCounted                  AS gaps_counted,
    GapsClearOnOwn               AS gaps_clear_on_own,
    GapsNoTicket                 AS gaps_no_ticket,
    GapsOver90Days               AS gaps_over_90_days,
    GapsOpenPriorClose           AS gaps_open_prior_close,
    GapsFixedDayAfter            AS gaps_fixed_day_after,
    GapRateTarget                AS gap_rate_target,
    LoadNote                     AS load_note
FROM dw.CwGapRateClose;
GO

/* Dashboard #4: Helix tickets open at each close, with their dot on the ticket card */
CREATE OR ALTER VIEW rpt.vw_itsm_ticket_close AS
SELECT
    MonthEndDate                 AS month_end_date,
    CloseLabel                   AS close_label,
    IsLatestClose                AS is_latest_close,
    TicketNumber                 AS ticket_number,
    Title                        AS title,
    State                        AS state,
    CategoryCode                 AS category_code,
    CategoryName                 AS category_name,
    FlagCode                     AS flag_code,
    Risk                         AS risk,
    Priority                     AS priority,
    Place                        AS place,
    PlaceOrder                   AS place_order,
    PlaceLabel                   AS place_label,
    CurrentGroup                 AS current_group,
    OpenedAt                     AS opened_at,
    AgeDays                      AS age_days,
    AgeBand                      AS age_band,
    AgeBandOrder                 AS age_band_order,
    TimesReopened                AS times_reopened,
    TimesReassigned              AS times_reassigned,
    LinkTier                     AS link_tier,
    ContractorKey                AS contractor_key,
    LinkedGapID                  AS linked_gap_id,
    CostCenterID                 AS cost_center_id,
    DepartmentID                 AS department_id,
    DepartmentName               AS department_name,
    FunctionName                 AS function_name,
    CountryCode                  AS country_code,
    CountryName                  AS country_name,
    DotSeq                       AS dot_seq,
    DotX                         AS dot_x,
    DotY                         AS dot_y
FROM dw.ItsmTicketClose;
GO
