# Release 7 on SQL Server: run guide (Who Leads Where)

Rebuild the `ArcadiaHR` database on your Mac with the release 7 tables (org design, time off and the Canopy tree), check them, and connect Tableau to the page's one Custom SQL. About 20 minutes, most of it waiting. Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.

What was already checked before this run: the same T-SQL, translated to DuckDB with `sqlglot`, built every table, every reporting view and the Custom SQL matched the DuckDB marts row for row, and every check in `18_validate_leadership_scope.sql` passed (`python sqlserver/check_tsql_in_duckdb.py`). This run is the final check on SQL Server itself.

## Step 1. Get the release

In Terminal, in the folder SQL Server sees as `/repo` (Step 2 of the [setup guide](../../setup/sql_server_local_setup.md)):

```bash
cd ~/GitHub/people-analytics-warehouse
git checkout main
git pull
git status
```

Expected: `Fast-forward` with a list of files (or `Already up to date.`), then `On branch main` and `nothing to commit, working tree clean`. The container reads this folder directly, so SQL Server now sees the release 7 CSVs and scripts.

## Step 2. Start SQL Server and load the password

```bash
docker start arcadia-sql
docker ps --filter name=arcadia-sql --format '{{.Names}}  {{.Status}}'
export MSSQL_SA_PASSWORD="$(docker exec arcadia-sql printenv MSSQL_SA_PASSWORD)"
echo ${#MSSQL_SA_PASSWORD}
```

Expected: `arcadia-sql`, then `arcadia-sql  Up …`, then a number that is not `0`. (If Docker Desktop is closed, open it first and wait for the whale icon to stop animating.)

## Step 3. Rebuild the warehouse

```bash
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -i /repo/sqlserver/build_all.sql
```

15 to 25 minutes under emulation. `build_all` now also runs 03g (release 7 tables), 04d (release 7 views) and 18 (release 7 checks). Look for these lines among the raw loads:

```
raw.bw_time_off                     72949 rows
raw.gen_org_drift_truth             999 rows
raw.ks_leave_of_absence             1771 rows
raw.ks_matrix_membership            70311 rows
raw.ks_matrix_org                   37 rows
raw.ks_role_assignment              115 rows
raw.ks_time_off_request             363620 rows
raw.ref_job_family_home             14 rows
raw.ref_public_holiday              276 rows
```

then, after the release 6 tables:

```
dw.PersonMonthEnd                 523466
dw.OrgClosure                     3845721
dw.OrgTreeLayout                  321670
dw.LeaderAvailability             300359
```

and at the end:

```
Who Leads Where Custom SQL returned 646673 rows in N seconds
1. Rows by type
2. Ties to the published dashboards
3. Alignment gaps on the report date (people)
4. The headline leader: Isaac Holland, L1, Software Engineering
5. Structure (each must be 0)
```

with every row of every table **PASS**. Section 2 is the one that matters most: 30,005 employees and 11,941 contingent workers, the same numbers Dashboards #1 to #4 show.

No `Msg` lines anywhere. If one appears, copy the whole message and the few lines above it and send it over.

To rerun only the release 7 checks later (2 to 3 minutes):

```bash
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -i /repo/sqlserver/18_validate_leadership_scope.sql
```

## Step 4. Connect Tableau to the Custom SQL

1. Open Tableau Desktop. **Connect > To a Server > Microsoft SQL Server**: server `localhost`, database `ArcadiaHR`, authentication **Use a specific username and password**, user `sa`, the password from Step 2. Tick **Trust Server Certificate** if Tableau offers it (the setting in `tableau/sqlserver_trust_local_certificate.tdc` does the same).
2. Drag **New Custom SQL** to the canvas. Open `tableau/custom_sql_who_leads_where.sql` in a text editor, copy the whole file, paste it, **OK**.
3. Rename the data source **Who Leads Where**.
4. Switch the connection to **Extract** and save the extract next to the workbook.

You should see 646,673 rows and these row types (`row_type`):

| row_type | Rows | What it feeds |
|---|---:|---|
| Node | 10,518 | the rail picker, headline, five KPIs, breadcrumb and tooltips (leader × All / Employees / Contingent) |
| Tree | 321,670 | the Canopy tree: circles (`mark_type` Node) and link curves (`mark_type` Link, 17 points each), for every leader as the focus, Dynamic and Static |
| Day | 300,359 | the "At work on" calendar: leader × worker type × the report date and the 30 days after it |
| Signal | 14,119 | the Org design alignment panel: each person with a gap, once under every leader above them |
| R1 | 7 | role assignments still naming a former leader |

Quick checks in a blank sheet, with `row_type = Node`, `worker_type = All`:

| Leader | People | At work today | Alignment gaps |
|---|---:|---:|---:|
| The CEO (leader_level L0, no parent) | 41,934 | 37,972 | 2,057 |
| Isaac Holland, L1, Software Engineering | 13,248 | 12,004 | 866 |

Three leaders are named Isaac Holland (the names are synthetic); the L1 is the one in the headline.
