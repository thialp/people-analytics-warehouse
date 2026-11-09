/*
  18_validate_leadership_scope.sql
  Release 7 (case study 7, Who Leads Where): runs the page's Tableau Custom SQL inside SQL Server
  exactly as Tableau would (included unchanged with sqlcmd's :r) and checks it against the numbers
  the DuckDB warehouse writes on the report date (Jun 30, 2026). Run it after build_all.sql:

    sqlcmd -S localhost -U sa -P "<password>" -C -i /repo/sqlserver/18_validate_leadership_scope.sql

  Every expected value comes from the DuckDB marts (python pipeline/run_pipeline.py, release 7).
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

DECLARE @started DATETIME2 = SYSDATETIME();
DROP TABLE IF EXISTS #w7;
SELECT *
INTO #w7
FROM (
:r /repo/tableau/custom_sql_who_leads_where.sql
) AS s;
DECLARE @n INT = (SELECT COUNT(*) FROM #w7);
PRINT CONCAT('Who Leads Where Custom SQL returned ', @n, ' rows in ',
             DATEDIFF(SECOND, @started, SYSDATETIME()), ' seconds');
GO

PRINT '1. Rows by type';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'all rows' AS check_name, (SELECT COUNT(*) FROM #w7) AS actual, 580222 AS expected
    UNION ALL SELECT 'Node rows (leader x worker type)',     (SELECT COUNT(*) FROM #w7 WHERE row_type = 'Node'), 10518
    UNION ALL SELECT 'Tree rows (circles and link points)',  (SELECT COUNT(*) FROM #w7 WHERE row_type = 'Tree'), 255219
    UNION ALL SELECT 'Tree rows, the company tree (Dynamic)', (SELECT COUNT(*) FROM #w7 WHERE row_type = 'Tree' AND tree_mode = 'Dynamic'), 63091
    UNION ALL SELECT 'Day rows (31 days)',                   (SELECT COUNT(*) FROM #w7 WHERE row_type = 'Day'), 300359
    UNION ALL SELECT 'Signal rows (person x signal x leader above)', (SELECT COUNT(*) FROM #w7 WHERE row_type = 'Signal'), 14119
    UNION ALL SELECT 'R1 rows (assignment x leader above)',  (SELECT COUNT(*) FROM #w7 WHERE row_type = 'R1'), 7
    UNION ALL SELECT 'leaders in the picker (L0 9, L1 20, L2 189)',
                     (SELECT COUNT(*) FROM #w7 WHERE row_type = 'Node' AND worker_type = 'All' AND is_selectable = 1), 218
    UNION ALL SELECT 'rows without the report date label', (SELECT COUNT(*) FROM #w7 WHERE report_as_of_label IS NULL), 0
) AS c;
GO

PRINT '2. Ties to the published dashboards';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'employees on the report date (Dashboards #1 to #3)' AS check_name,
                     (SELECT COUNT(*) FROM dw.PersonMonthEnd AS p JOIN fc.report_calendar AS rc ON p.MonthEndDate = rc.report_as_of_date
                      WHERE p.WorkerType = 'Employee' AND p.IsExecutiveOfficer = 0) AS actual, 30005 AS expected
    UNION ALL SELECT 'contingent workers on the report date (Dashboards #1 and #4)',
                     (SELECT COUNT(*) FROM dw.PersonMonthEnd AS p JOIN fc.report_calendar AS rc ON p.MonthEndDate = rc.report_as_of_date
                      WHERE p.WorkerType = 'Contingent'), 11941
    UNION ALL SELECT 'CEO organization, all (12 contingent workers have no manager on file)',
                     (SELECT people FROM #w7 WHERE row_type = 'Node' AND leader_level = 'L0' AND parent_leader_id IS NULL AND worker_type = 'All'), 41934
    UNION ALL SELECT 'CEO organization, employees',
                     (SELECT people FROM #w7 WHERE row_type = 'Node' AND leader_level = 'L0' AND parent_leader_id IS NULL AND worker_type = 'Employees'), 30005
    UNION ALL SELECT 'CEO organization, contingent',
                     (SELECT people FROM #w7 WHERE row_type = 'Node' AND leader_level = 'L0' AND parent_leader_id IS NULL AND worker_type = 'Contingent'), 11929
    UNION ALL SELECT 'CEO organization at work on the report date',
                     (SELECT at_work_today FROM #w7 WHERE row_type = 'Node' AND leader_level = 'L0' AND parent_leader_id IS NULL AND worker_type = 'All'), 37972
) AS c;
GO

PRINT '3. Alignment gaps on the report date (people)';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'people with at least one gap (4.9%)' AS check_name,
                     (SELECT gap_people FROM #w7 WHERE row_type = 'Node' AND leader_id = (SELECT leader_id FROM #w7 WHERE row_type = 'Node' AND parent_leader_id IS NULL AND leader_level = 'L0' AND worker_type = 'All') AND worker_type = 'All') AS actual, 2057 AS expected
    UNION ALL SELECT 'S1 Budgeted in another org',
                     (SELECT COUNT(DISTINCT person_id) FROM #w7 WHERE row_type = 'Signal' AND leader_id = (SELECT leader_id FROM #w7 WHERE row_type = 'Node' AND parent_leader_id IS NULL AND leader_level = 'L0' AND worker_type = 'All') AND signal_code = 'S1'), 258
    UNION ALL SELECT 'S2 Role from another function',
                     (SELECT COUNT(DISTINCT person_id) FROM #w7 WHERE row_type = 'Signal' AND leader_id = (SELECT leader_id FROM #w7 WHERE row_type = 'Node' AND parent_leader_id IS NULL AND leader_level = 'L0' AND worker_type = 'All') AND signal_code = 'S2'), 958
    UNION ALL SELECT 'M1 Country leader for another country',
                     (SELECT COUNT(DISTINCT person_id) FROM #w7 WHERE row_type = 'Signal' AND leader_id = (SELECT leader_id FROM #w7 WHERE row_type = 'Node' AND parent_leader_id IS NULL AND leader_level = 'L0' AND worker_type = 'All') AND signal_code = 'M1'), 42
    UNION ALL SELECT 'M2 In two country matrices, or none',
                     (SELECT COUNT(DISTINCT person_id) FROM #w7 WHERE row_type = 'Signal' AND leader_id = (SELECT leader_id FROM #w7 WHERE row_type = 'Node' AND parent_leader_id IS NULL AND leader_level = 'L0' AND worker_type = 'All') AND signal_code = 'M2'), 19
    UNION ALL SELECT 'M3 Matrix inactive or without a leader',
                     (SELECT COUNT(DISTINCT person_id) FROM #w7 WHERE row_type = 'Signal' AND leader_id = (SELECT leader_id FROM #w7 WHERE row_type = 'Node' AND parent_leader_id IS NULL AND leader_level = 'L0' AND worker_type = 'All') AND signal_code = 'M3'), 817
    UNION ALL SELECT 'R1 role assignments still naming a former leader',
                     (SELECT COUNT(DISTINCT person_id) FROM #w7 WHERE row_type = 'R1' AND leader_id = (SELECT leader_id FROM #w7 WHERE row_type = 'Node' AND parent_leader_id IS NULL AND leader_level = 'L0' AND worker_type = 'All')), 2
    UNION ALL SELECT 'leaders whose Signal people differ from their gap count (must be 0)',
                     (SELECT COUNT(*) FROM (
                          SELECT n.leader_id, n.worker_type
                          FROM #w7 AS n
                          LEFT JOIN #w7 AS s ON s.row_type = 'Signal' AND s.leader_id = n.leader_id
                                            AND (n.worker_type = 'All' OR s.worker_type = n.worker_type)
                          WHERE n.row_type = 'Node'
                          GROUP BY n.leader_id, n.worker_type, n.gap_people
                          HAVING n.gap_people <> COUNT(DISTINCT s.person_id)) AS x), 0
) AS c;
GO

PRINT '4. The headline leader: Isaac Holland, L1, Software Engineering';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'people (all)' AS check_name,
                     (SELECT people FROM #w7 WHERE row_type = 'Node' AND leader_name = 'Isaac Holland' AND leader_level = 'L1' AND worker_type = 'All') AS actual,
                     13248 AS expected
    UNION ALL SELECT 'employees',
                     (SELECT people FROM #w7 WHERE row_type = 'Node' AND leader_name = 'Isaac Holland' AND leader_level = 'L1' AND worker_type = 'Employees'), 8101
    UNION ALL SELECT 'contingent workers',
                     (SELECT people FROM #w7 WHERE row_type = 'Node' AND leader_name = 'Isaac Holland' AND leader_level = 'L1' AND worker_type = 'Contingent'), 5147
    UNION ALL SELECT 'directs',
                     (SELECT directs FROM #w7 WHERE row_type = 'Node' AND leader_name = 'Isaac Holland' AND leader_level = 'L1' AND worker_type = 'All'), 12
    UNION ALL SELECT 'countries',
                     (SELECT countries FROM #w7 WHERE row_type = 'Node' AND leader_name = 'Isaac Holland' AND leader_level = 'L1' AND worker_type = 'All'), 22
    UNION ALL SELECT 'layers below',
                     (SELECT layers_below FROM #w7 WHERE row_type = 'Node' AND leader_name = 'Isaac Holland' AND leader_level = 'L1' AND worker_type = 'All'), 6
    UNION ALL SELECT 'alignment gaps (6.5%)',
                     (SELECT gap_people FROM #w7 WHERE row_type = 'Node' AND leader_name = 'Isaac Holland' AND leader_level = 'L1' AND worker_type = 'All'), 866
    UNION ALL SELECT 'at work on the report date',
                     (SELECT at_work_today FROM #w7 WHERE row_type = 'Node' AND leader_name = 'Isaac Holland' AND leader_level = 'L1' AND worker_type = 'All'), 12004
) AS c;
GO

PRINT '5. Structure (each must be 0)';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'reporting chains longer than the 12 levels the closure builds' AS check_name,
                     (SELECT COUNT(*) FROM dw.OrgClosure AS c
                      JOIN dw.PersonMonthEnd AS p ON p.MonthEndDate = c.MonthEndDate AND p.PersonID = c.AncestorID
                      WHERE c.Depth = 12 AND p.ManagerWorkerID IS NOT NULL) AS actual, 0 AS expected
    UNION ALL SELECT 'leaders not in the company tree exactly once',
                     (SELECT COUNT(*) FROM #w7 AS n WHERE n.row_type = 'Node' AND n.worker_type = 'All'
                      AND (SELECT COUNT(*) FROM #w7 AS t WHERE t.row_type = 'Tree' AND t.tree_mode = 'Dynamic'
                           AND t.mark_type = 'Node' AND t.node_id = n.leader_id) <> 1), 0
    UNION ALL SELECT 'leaders who cannot be the static tree''s focus',
                     (SELECT COUNT(*) FROM #w7 AS n WHERE n.row_type = 'Node' AND n.worker_type = 'All'
                      AND NOT EXISTS (SELECT 1 FROM #w7 AS t WHERE t.row_type = 'Tree' AND t.tree_mode = 'Static'
                                      AND t.focus_leader_id = n.leader_id AND t.tier = 0)), 0
    UNION ALL SELECT 'links without 17 points',
                     (SELECT COUNT(*) FROM (SELECT tree_mode, focus_leader_id, node_id FROM #w7
                                            WHERE row_type = 'Tree' AND mark_type = 'Link'
                                            GROUP BY tree_mode, focus_leader_id, node_id HAVING COUNT(*) <> 17) AS x), 0
    UNION ALL SELECT 'static circles off the canvas (x outside 0 to 1)',
                     (SELECT COUNT(*) FROM #w7 WHERE row_type = 'Tree' AND tree_mode = 'Static' AND (x < 0 OR x > 1)), 0
    UNION ALL SELECT 'weekdays where at work + off <> people',
                     (SELECT COUNT(*) FROM #w7 WHERE row_type = 'Day' AND is_weekend = 0 AND at_work + [off] <> people), 0
) AS c;
GO
