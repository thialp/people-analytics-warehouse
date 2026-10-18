/*
  13_check_tie_out_population.sql
  The "73 of the 72 who joined" check (Dashboard #2 guide, section 8 item 9), for
  FY26 (Jun 30, 2025 -> Jun 30, 2026), Department Accounting & Controllership (D-502).
  Reads only the dw tables, so it runs on any release 3 build. From the Mac:

    docker exec arcadia-sql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -W \
        -i /repo/sqlserver/13_check_tie_out_population.sql

  (a) joined        first month-end in the snapshot, department on that month-end (Dashboard #1)   72
  (b) still here    absent Jun 30, 2025, present Jun 30, 2026, department on Jun 30, 2026 (Hires bar) 73
  (c) in one only   4 joined A&C and left; 5 joined another department and moved in                 9 rows
  (d) the fix       of (b): joined A&C 68, joined elsewhere and moved in 5
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

PRINT '(a) Joined Accounting & Controllership in FY26, as Dashboard #1 counts it (expected 72)';
SELECT COUNT(DISTINCT cur.WorkerID) AS joined_at_hire_dept
FROM dw.MonthEndCalendar AS cal
JOIN dw.WorkerMonthEndSnapshot AS cur ON cur.MonthEndDate = cal.MonthEndDate
LEFT JOIN dw.WorkerMonthEndSnapshot AS pri
  ON pri.MonthEndDate = cal.PriorMonthEndDate AND pri.WorkerID = cur.WorkerID
WHERE cal.MonthEndDate > '2025-06-30' AND cal.MonthEndDate <= '2026-06-30'
  AND pri.WorkerID IS NULL AND cur.DepartmentID = 'D-502' AND cur.IsExecutiveOfficer = 0;
GO

PRINT '(b) Hires still here in Accounting & Controllership, as the Hires bar counts them (expected 73)';
SELECT COUNT(DISTINCT c.WorkerID) AS still_here_at_close_dept
FROM dw.WorkerMonthEndSnapshot AS c
LEFT JOIN dw.WorkerMonthEndSnapshot AS o ON o.MonthEndDate = '2025-06-30' AND o.WorkerID = c.WorkerID
WHERE c.MonthEndDate = '2026-06-30' AND o.WorkerID IS NULL
  AND c.DepartmentID = 'D-502' AND c.IsExecutiveOfficer = 0;
GO

PRINT '(c) Workers in only one of (a) and (b) (expected 9 rows: 4 gone, 5 moved in)';
SELECT COALESCE(a.WorkerID, b.WorkerID)                   AS worker_id,
       CASE WHEN a.WorkerID IS NOT NULL THEN 1 ELSE 0 END AS in_a,
       CASE WHEN b.WorkerID IS NOT NULL THEN 1 ELSE 0 END AS in_b,
       COALESCE(a.joined_month, j.joined_month)           AS joined_month,
       COALESCE(a.joined_dept,  j.joined_dept)            AS joined_dept,
       cl.DepartmentID                                    AS close_dept,
       CASE WHEN b.WorkerID IS NULL AND cl.WorkerID IS NULL    THEN 'joined A&C, gone by Jun 30, 2026'
            WHEN b.WorkerID IS NULL                            THEN 'joined A&C, moved to another department'
            WHEN a.WorkerID IS NULL AND j.WorkerID IS NOT NULL THEN 'joined another department, moved into A&C'
            ELSE 'in A&C at close, no join event in FY26' END AS reason
FROM (SELECT cur.WorkerID, cal.MonthEndDate AS joined_month, cur.DepartmentID AS joined_dept
      FROM dw.MonthEndCalendar AS cal
      JOIN dw.WorkerMonthEndSnapshot AS cur ON cur.MonthEndDate = cal.MonthEndDate
      LEFT JOIN dw.WorkerMonthEndSnapshot AS pri ON pri.MonthEndDate = cal.PriorMonthEndDate AND pri.WorkerID = cur.WorkerID
      WHERE cal.MonthEndDate > '2025-06-30' AND cal.MonthEndDate <= '2026-06-30'
        AND pri.WorkerID IS NULL AND cur.DepartmentID = 'D-502' AND cur.IsExecutiveOfficer = 0) AS a
FULL OUTER JOIN
     (SELECT c.WorkerID FROM dw.WorkerMonthEndSnapshot AS c
      LEFT JOIN dw.WorkerMonthEndSnapshot AS o ON o.MonthEndDate = '2025-06-30' AND o.WorkerID = c.WorkerID
      WHERE c.MonthEndDate = '2026-06-30' AND o.WorkerID IS NULL
        AND c.DepartmentID = 'D-502' AND c.IsExecutiveOfficer = 0) AS b ON b.WorkerID = a.WorkerID
LEFT JOIN
     (SELECT cur.WorkerID, cal.MonthEndDate AS joined_month, cur.DepartmentID AS joined_dept
      FROM dw.MonthEndCalendar AS cal
      JOIN dw.WorkerMonthEndSnapshot AS cur ON cur.MonthEndDate = cal.MonthEndDate
      LEFT JOIN dw.WorkerMonthEndSnapshot AS pri ON pri.MonthEndDate = cal.PriorMonthEndDate AND pri.WorkerID = cur.WorkerID
      WHERE cal.MonthEndDate > '2025-06-30' AND cal.MonthEndDate <= '2026-06-30' AND pri.WorkerID IS NULL) AS j
  ON j.WorkerID = b.WorkerID AND a.WorkerID IS NULL
LEFT JOIN dw.WorkerMonthEndSnapshot AS cl
  ON cl.MonthEndDate = '2026-06-30' AND cl.WorkerID = COALESCE(a.WorkerID, b.WorkerID)
WHERE a.WorkerID IS NULL OR b.WorkerID IS NULL
ORDER BY reason, worker_id;
GO

PRINT '(d) The fix: the Hires bar split by the department each hire joined (expected 68, 5, 73)';
SELECT SUM(CASE WHEN h.DepartmentID =  'D-502' THEN 1 ELSE 0 END) AS joined_here_still_here,
       SUM(CASE WHEN h.DepartmentID <> 'D-502' THEN 1 ELSE 0 END) AS joined_elsewhere_moved_in,
       COUNT(*)                                                   AS hires_bar
FROM dw.WorkerMonthEndSnapshot AS c
JOIN dw.DimWorker AS w ON w.WorkerID = c.WorkerID
LEFT JOIN dw.WorkerMonthEndSnapshot AS o ON o.MonthEndDate = '2025-06-30' AND o.WorkerID = c.WorkerID
JOIN dw.WorkerMonthEndSnapshot AS h ON h.MonthEndDate = EOMONTH(w.OriginalHireDate) AND h.WorkerID = c.WorkerID
WHERE c.MonthEndDate = '2026-06-30' AND o.WorkerID IS NULL
  AND c.DepartmentID = 'D-502' AND c.IsExecutiveOfficer = 0;
GO

PRINT 'Summary';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT '(a) joined A&C' AS check_name,
                     (SELECT COUNT(DISTINCT cur.WorkerID)
                      FROM dw.MonthEndCalendar AS cal
                      JOIN dw.WorkerMonthEndSnapshot AS cur ON cur.MonthEndDate = cal.MonthEndDate
                      LEFT JOIN dw.WorkerMonthEndSnapshot AS pri
                        ON pri.MonthEndDate = cal.PriorMonthEndDate AND pri.WorkerID = cur.WorkerID
                      WHERE cal.MonthEndDate > '2025-06-30' AND cal.MonthEndDate <= '2026-06-30'
                        AND pri.WorkerID IS NULL AND cur.DepartmentID = 'D-502' AND cur.IsExecutiveOfficer = 0) AS actual,
                     72 AS expected
    UNION ALL SELECT '(b) still here in A&C',
                     (SELECT COUNT(DISTINCT c.WorkerID)
                      FROM dw.WorkerMonthEndSnapshot AS c
                      LEFT JOIN dw.WorkerMonthEndSnapshot AS o ON o.MonthEndDate = '2025-06-30' AND o.WorkerID = c.WorkerID
                      WHERE c.MonthEndDate = '2026-06-30' AND o.WorkerID IS NULL
                        AND c.DepartmentID = 'D-502' AND c.IsExecutiveOfficer = 0),
                     73
    UNION ALL SELECT '(d) joined A&C and still here',
                     (SELECT COUNT(*)
                      FROM dw.WorkerMonthEndSnapshot AS c
                      JOIN dw.DimWorker AS w ON w.WorkerID = c.WorkerID
                      LEFT JOIN dw.WorkerMonthEndSnapshot AS o ON o.MonthEndDate = '2025-06-30' AND o.WorkerID = c.WorkerID
                      JOIN dw.WorkerMonthEndSnapshot AS h ON h.MonthEndDate = EOMONTH(w.OriginalHireDate) AND h.WorkerID = c.WorkerID
                      WHERE c.MonthEndDate = '2026-06-30' AND o.WorkerID IS NULL AND h.DepartmentID = 'D-502'
                        AND c.DepartmentID = 'D-502' AND c.IsExecutiveOfficer = 0),
                     68
) AS s;
GO
