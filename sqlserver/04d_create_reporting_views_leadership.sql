/*
  04d_create_reporting_views_leadership.sql
  Release 7: the reporting views of case study 7, Who Leads Where. Runs after 03g.

    rpt.vw_org_node              the tree's nodes on the report date: every leader x worker type
    rpt.vw_leader_org            L0 to L2 leaders' organizations, the 13 month-ends to the report date
    rpt.vw_leader_availability   the "At work on" calendar: leader x worker type x day
    rpt.vw_alignment_detail      person x alignment signal on the report date
    rpt.vw_org_entitlement       row-level security for Tableau Cloud
    rpt.vw_org_tree_layout       where every circle and link of the tree sits, for every focus leader

  Thin reads of the dw tables 03g builds, in the DuckDB marts' column names. Checked row for row
  against the DuckDB marts by sqlserver/check_tsql_in_duckdb.py.
  Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

/* The tree's nodes on the report date: every leader x worker type, with the circle, KPI and tooltip fields */
CREATE OR ALTER VIEW rpt.vw_org_node AS
SELECT
    AsOfDate                          AS as_of_date,
    LeaderID                          AS leader_id,
    LeaderName                        AS leader_name,
    JobTitle                          AS job_title,
    Grade                             AS grade,
    LeaderLevel                       AS leader_level,
    IsSelectable                      AS is_selectable,
    ParentLeaderID                    AS parent_leader_id,
    ParentLeaderName                  AS parent_leader_name,
    DepthFromTop                      AS depth_from_top,
    Path                              AS path,
    ChildLeaders                      AS child_leaders,
    DepartmentName                    AS department_name,
    FunctionName                      AS function_name,
    OfficeName                        AS office_name,
    CountryName                       AS country_name,
    Region                            AS region,
    LeadsOrgUnitID                    AS leads_org_unit_id,
    LeadsOrgUnitName                  AS leads_org_unit_name,
    WorkerType                        AS worker_type,
    People                            AS people,
    Directs                           AS directs,
    Indirects                         AS indirects,
    ManagersBelow                     AS managers_below,
    LayersBelow                       AS layers_below,
    Countries                         AS countries,
    MedianSpan                        AS median_span,
    Managers15Plus                    AS managers_15_plus,
    ManagersOneDirect                 AS managers_one_direct,
    GapPeople                         AS gap_people,
    SolidLineGapPeople                AS solid_line_gap_people,
    MatrixGapPeople                   AS matrix_gap_people,
    S1BudgetedElsewhere               AS s1_budgeted_elsewhere,
    S2RoleOtherFunction               AS s2_role_other_function,
    M1CountryLeaderOtherCountry       AS m1_country_leader_other_country,
    M2NotOneCountryMatrix             AS m2_not_one_country_matrix,
    M3MatrixInactiveOrLeaderless      AS m3_matrix_inactive_or_leaderless,
    AssignmentsNamingFormerLeader     AS assignments_naming_former_leader,
    AtWorkToday                       AS at_work_today,
    OffToday                          AS off_today
FROM dw.OrgNode;
GO

/* L0 to L2 leaders' organizations per month-end and worker type, the 13 month-ends to the report date */
CREATE OR ALTER VIEW rpt.vw_leader_org AS
SELECT
    o.MonthEndDate                    AS month_end_date,
    cal.FiscalYear                    AS fiscal_year,
    cal.FiscalQuarterLabel            AS fiscal_quarter_label,
    o.LeaderID                        AS leader_id,
    l.LeaderName                      AS leader_name,
    l.JobTitle                        AS job_title,
    l.LeaderLevel                     AS leader_level,
    l.FunctionName                    AS function_name,
    l.DepartmentName                  AS department_name,
    o.WorkerType                      AS worker_type,
    o.People                          AS people,
    o.Directs                         AS directs,
    o.Indirects                       AS indirects,
    o.ManagersBelow                   AS managers_below,
    o.LayersBelow                     AS layers_below,
    o.Countries                       AS countries,
    o.MedianSpan                      AS median_span,
    o.AverageSpan                     AS average_span,
    o.Managers15Plus                  AS managers_15_plus,
    o.ManagersOneDirect               AS managers_one_direct,
    o.GapPeople                       AS gap_people,
    o.SolidLineGapPeople              AS solid_line_gap_people,
    o.MatrixGapPeople                 AS matrix_gap_people,
    o.S1BudgetedElsewhere             AS s1_budgeted_elsewhere,
    o.S2RoleOtherFunction             AS s2_role_other_function,
    o.M1CountryLeaderOtherCountry     AS m1_country_leader_other_country,
    o.M2NotOneCountryMatrix           AS m2_not_one_country_matrix,
    o.M3MatrixInactiveOrLeaderless    AS m3_matrix_inactive_or_leaderless,
    o.AssignmentsNamingFormerLeader   AS assignments_naming_former_leader,
    CASE WHEN o.People > 0 THEN CAST(o.GapPeople AS FLOAT) / o.People END AS gap_rate
FROM dw.LeaderOrg AS o
JOIN dw.OrgLeader AS l ON l.MonthEndDate = o.MonthEndDate AND l.LeaderID = o.LeaderID
JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate = o.MonthEndDate
WHERE l.LeaderLevel IN ('L0', 'L1', 'L2');
GO

/* The "At work on" calendar: per leader, worker type and day, the report date and the 30 days after it */
CREATE OR ALTER VIEW rpt.vw_leader_availability AS
SELECT
    LeaderID             AS leader_id,
    WorkerType           AS worker_type,
    Day                  AS day,
    DayOffset            AS day_offset,
    IsWeekend            AS is_weekend,
    People               AS people,
    AtWork               AS at_work,
    Off                  AS off,
    OffTimeOff           AS off_time_off,
    OffLeave             AS off_leave,
    OffPublicHoliday     AS off_public_holiday,
    LeftTeam             AS left_team
FROM dw.LeaderAvailability;
GO

/* Person x alignment signal on the report date, with the L0, L1 and L2 above each person */
CREATE OR ALTER VIEW rpt.vw_alignment_detail AS
SELECT
    AsOfDate                  AS as_of_date,
    PersonID                  AS person_id,
    PersonName                AS person_name,
    WorkerType                AS worker_type,
    JobTitle                  AS job_title,
    DepartmentName            AS department_name,
    FunctionName              AS function_name,
    OfficeName                AS office_name,
    CountryCode               AS country_code,
    Region                    AS region,
    ManagerWorkerID           AS manager_worker_id,
    ManagerName               AS manager_name,
    ManagerDepartmentName     AS manager_department_name,
    ManagerSource             AS manager_source,
    SignalCode                AS signal_code,
    SignalName                AS signal_name,
    SignalLine                AS signal_line,
    SignalDetail              AS signal_detail,
    L0LeaderID                AS l0_leader_id,
    L1LeaderID                AS l1_leader_id,
    L2LeaderID                AS l2_leader_id
FROM dw.AlignmentDetail;
GO

/* Row-level security for Tableau Cloud: each leader x the people they may see */
CREATE OR ALTER VIEW rpt.vw_org_entitlement AS
SELECT
    ViewerLeaderID        AS viewer_leader_id,
    ViewerEmail           AS viewer_email,
    ViewerLeaderLevel     AS viewer_leader_level,
    PersonID              AS person_id,
    Depth                 AS depth
FROM dw.OrgEntitlement;
GO

/* Where every circle and link of the Canopy tree sits, for every leader as the focus (dynamic and static) */
CREATE OR ALTER VIEW rpt.vw_org_tree_layout AS
SELECT
    TreeMode          AS tree_mode,
    FocusLeaderID     AS focus_leader_id,
    MarkType          AS mark_type,
    Tier              AS tier,
    NodeID            AS node_id,
    ParentNodeID      AS parent_node_id,
    Tier1NodeID       AS tier1_node_id,
    Slot              AS slot,
    Slots             AS slots,
    PointIndex        AS point_index,
    X                 AS x,
    Y                 AS y
FROM dw.OrgTreeLayout;
GO
