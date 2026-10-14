# Running the Warehouse on SQL Server (Local) with Tableau

This walkthrough reproduces an enterprise setup on a laptop:

```
GitHub repo ──► SQL Server (Docker) ──► Tableau Desktop
  CSV files      raw → dw → rpt          live connection + Custom SQL
```

SQL Server runs in a Docker container, the repo's CSVs are loaded with `BULK INSERT`, and Tableau connects with the native SQL Server connector, including a Custom SQL data source written under Tableau's rules (one `SELECT`, no CTEs).

The SQL Server logic was verified against the DuckDB pipeline: the Custom SQL and the reporting view reproduce both CSV marts row for row, to the cent.

**Time:** about 45 minutes the first time. **Cost:** free. Docker Desktop is free for personal use, SQL Server Developer Edition is free, and Tableau Desktop Free Edition is free.

> Use a personal computer for this, not an employer-managed one.

---

## Step 1. Install Docker Desktop

1. Download Docker Desktop for Mac from <https://www.docker.com/products/docker-desktop/>. Pick **Apple Silicon** or **Intel** to match your Mac.
2. Install it, open it, and finish the welcome screens.
3. **Apple Silicon only:** in Docker Desktop, open **Settings → General** and make sure **Use Rosetta for x86_64/amd64 emulation on Apple Silicon** is on. SQL Server is built for Intel chips, and Rosetta lets it run on M-series Macs.

Check it in Terminal:

```bash
docker --version
```

Expected output, with your version number:

```
Docker version 29.x.x, build xxxxxxx
```

## Step 2. Get the repo onto your Mac

If you already cloned it with GitHub Desktop, skip this step. Otherwise (keep it in `~/GitHub`, outside the folders iCloud syncs; see the note in [`docker_compose_guide.md`](docker_compose_guide.md#2-get-the-repo)):

```bash
mkdir -p ~/GitHub
cd ~/GitHub
git clone https://github.com/thialp/people-analytics-warehouse.git
ls people-analytics-warehouse
```

Expected output:

```
README.md  data  docs  generator  pipeline  requirements.txt  sql  sqlserver  tableau  tests
```

## Step 3. Start SQL Server

> **Shortcut:** Steps 3–4 can be replaced by a single `docker compose up -d`, which starts SQL Server, waits until it's healthy and builds the warehouse. See [`docker_compose_guide.md`](docker_compose_guide.md).

Pick a password for the `sa` (admin) account. It needs at least 8 characters with upper case, lower case, a number and a symbol. Avoid `!`, because zsh treats it specially. This example uses `Arcadia#Local2026`:

```bash
export MSSQL_SA_PASSWORD='Arcadia#Local2026'

docker run -d --name arcadia-sql \
  --platform linux/amd64 \
  -e "ACCEPT_EULA=Y" \
  -e "MSSQL_PID=Developer" \
  -e "MSSQL_SA_PASSWORD=$MSSQL_SA_PASSWORD" \
  -p 1433:1433 \
  -v ~/GitHub/people-analytics-warehouse:/repo:ro \
  mcr.microsoft.com/mssql/server:2022-latest
```

What the flags do:

- `-p 1433:1433` exposes SQL Server's standard port to your Mac, so Tableau can reach it.
- `-v ...:/repo:ro` shares the repo folder with the container, read-only, at `/repo`. This is how `BULK INSERT` reads the CSVs.
- `--platform linux/amd64` runs the Intel build, through Rosetta on Apple Silicon.

The first run downloads about 1.5 GB. When it finishes, Docker prints a long container ID. Then watch the startup log:

```bash
docker logs -f arcadia-sql
```

Wait for this line (30–90 seconds under emulation), then press `Ctrl+C` to stop following the log:

```
SQL Server is now ready for client connections.
```

## Step 4. Build the warehouse

```bash
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -i /repo/sqlserver/build_all.sql
```

`-C` tells `sqlcmd` to trust the container's self-signed certificate. `build_all.sql` runs these scripts in order:

| Script | What it does |
|---|---|
| `01_create_database.sql` | Creates the `ArcadiaHR` database and the `raw`, `dw` and `rpt` schemas |
| `02_load_raw.sql` | Lands each CSV as text with `BULK INSERT` |
| `03_build_dw.sql` | Types and cleans the data, resolves pay corrections, values pay at its posting-date FX rate, builds the fiscal calendar, the indexed worker month-end snapshot, the pay ledger behind the compensation walk and the reporting chain |
| `03b_build_dw_workforce_planning.sql` | The seat layer: cost centers, positions (SCD2), seat assignments, requisitions, the workforce plan, candidates, the seat month-end snapshot, seat fills with the pay walk, vacancy chains, plan vs actual |
| `03c_build_dw_contingent.sql` | Release 3, the contingent workforce: Bridgeway VMS (workers, service orders and revisions, timesheets), Keystone HR's contingent records, the feed log; the contingent month-end snapshot, conversions to employee, contingent movement, the plan's contingent actuals; for case study 6 the supplier spellings, identity resolution, the two systems side by side and the discrepancy rules |
| `04_create_reporting_views.sql` | Creates `rpt.vw_workforce_cost_snapshot`, `rpt.vw_org_leader_summary`, `rpt.vw_fringe_rate`, and for Workforce Planning `rpt.vw_position_fill`, `rpt.vw_vacancy_pool`, `rpt.vw_plan_vs_actual`, `rpt.vw_seat_corridors` |
| `04b_create_reporting_views_contingent.sql` | Creates `rpt.vw_cw_spend`, `rpt.vw_workforce_cost_growth_mix` and, for case study 6, `rpt.vw_cw_discrepancy_detail`, `rpt.vw_cw_reconciliation`, `rpt.vw_cw_engagement_cap`, `rpt.vw_cw_detection_score` |
| `05_validate.sql` | Checks row counts, reporting lines, control totals and that the pay ledger explains every worker's change in cost |
| `08_validate_workforce_planning.sql` | Checks the seat layer: row counts, one incumbent per seat, filled seats = headcount, the seat pay walk, FY26 fills, the vacancy pool and plan vs actual |
| `12_validate_contingent_workforce.sql` | Checks the contingent workforce: every raw row landed, the population and spend, identity resolution, the discrepancies open on 30 Jun 2026 and the detection score, and that the cost bridge Custom SQL closes and the growth mix effects add up |

Expected output, abbreviated (5–10 minutes under emulation):

```
Created database ArcadiaHR
Schemas ready: raw, dw, rpt
raw.dim_candidate                   188982 rows
raw.dim_cost_center                 630 rows
...
raw.dim_worker                      46980 rows
raw.fact_job_history                98028 rows
raw.fact_compensation_history       186191 rows
...
TableName                       RowsLoaded
dw.DimWorker                         46980
dw.FactJobHistory                    98028
dw.FactCompensationHistory          185063
dw.FactPerformanceReview            154151
dw.FactBonusPayout                  154151
dw.MonthEndCalendar                     61
dw.WorkerMonthEndSnapshot          1639687
dw.WorkerPayLedger                 1639687
dw.WorkerReportingChain            1048170
TableName                       RowsLoaded
dw.DimCostCenter                       630
dw.DimPosition                      101297
dw.FactPositionAssignment            54094
dw.FactRequisition                   31323
dw.FactWorkforcePlan                 28800
dw.DimCandidate                     188982
dw.FactCandidateStageEvent          531691
dw.PositionMonthEndSnapshot        1701742
dw.SeatFill                          30575
dw.SeatVacancyChain                  30575
dw.PlanVsActual                      29415
TableName                       RowsLoaded
dw.BwContingentWorker                43484
dw.BwServiceOrderRevision           160499
dw.BwTimesheetMonth                 632504
dw.KsContingentWorker               141791
dw.FeedBridgewayKeystoneEvent       106357
dw.CwMonthEndSnapshot               598752
dw.CwConversion                       1174
dw.CwMovement                       616469
dw.CwIdentityResolution              43552
dw.CwReconciliationSnapshot         599228
dw.CwDiscrepancy                     28586
Created views rpt.vw_workforce_cost_snapshot, rpt.vw_org_leader_summary, rpt.vw_fringe_rate,
              rpt.vw_position_fill, rpt.vw_vacancy_pool, rpt.vw_plan_vs_actual, rpt.vw_seat_corridors
1. Row counts
check_name                          actual   expected  result
dw.DimWorker rows                    46980      46980  PASS
...
3. Everyone except the CEO reports to an employed manager (expected 0)
workers_without_a_valid_manager
0
4. Control totals (executive officers excluded)
month_end_date  headcount  fte       loaded_usd_nominal  loaded_usd_constant
2022-06-30      25052      25052.00  2482526955.64       2519944448.45
2026-06-30      30005      30005.00  3410482749.84       3410482749.84
5. The pay ledger explains every change in every worker's cost (expected 0)
worker_months_not_explained
0
1. Row counts                 (08: twelve rows, all PASS)
2. Seat integrity (every check expects 0)
seats with two incumbents at once                               0  PASS
month-ends where filled seats differ from headcount             0  PASS
...
3. FY26 seat fills (fiscal_year = 2026)        (twelve rows, all PASS)
4. Vacancy pool at 30 Jun 2026                 (four rows, all PASS)
5. FY26 plan vs actual, company                (compare with the expected values in the script)
Workforce cost bridge Custom SQL returned 29123 rows in <n> seconds
1. Every raw row landed in dw                  (12: nine rows, all PASS)
2. Population and spend                        (seven rows, all PASS)
3. Who is who: identity resolution             (ten rows, all PASS)
4. The discrepancies, open on 30 Jun 2026 ...  (nineteen rows, all PASS)
5. Cost: the bridge closes ...                 (six rows, all PASS)
```

Every row with a `result` column should say `PASS`, the single-number checks in 05 should show `0`, and the control totals should match (SQL Server may show a cent different from DuckDB: each group is rounded to the cent before the total is added up).

**No SQL Server at hand?** `python sqlserver/check_tsql_in_duckdb.py` translates the same T-SQL to DuckDB with sqlglot, runs it on the same CSVs and compares every view and Custom SQL with the pipeline's marts, row for row (about 15 minutes on a 2-core machine). It is how releases 2 and 3 were checked before they ran on SQL Server.

### Optional: validate the compensation walk

The compensation walk is Tableau Custom SQL, not a view, so the build doesn't run it. This script runs the exact Tableau file inside SQL Server (`:r` includes it unchanged), prints how long it took, and checks the result:

```bash
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -i /repo/sqlserver/06_validate_compensation_walk.sql
```

Expected, abbreviated:

```
Custom SQL returned 115544 rows in <n> seconds
1. Shape
rows          115544   115544  PASS
date pairs        88       88  PASS
views              6        6  PASS
2. Groups whose walk does not close: Opening + steps <> Closing (expected 0)
0
3. Company, FY23 (30 Jun 2022 to 30 Jun 2023)
Opening   25052   2482526955.47   2519944448.29
Closing   26932   2761818121.64   2771129945.16
4. FY26 company walk, loaded cost at constant FX ...
```

The seconds it prints are about what a Tableau extract refresh of this data source will take. Field reference and rules: [`compensation_walk.md`](../projects/compensation-walk/compensation_walk.md).

**If `sqlcmd` isn't found,** older images keep it at `/opt/mssql-tools/bin/sqlcmd`. Use that path and drop the `-C`.

### Optional: validate the office moves

The office-moves query is a second Custom SQL, read by the map on the Compensation Walk dashboard. This script runs it and the compensation walk exactly as Tableau would, prints how long each took, and ties the moves to the walk's transfers:

```bash
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -i /repo/sqlserver/07_validate_office_moves.sql
```

Expected: section 1 and 2 rows say `PASS` (89,611 rows; FY26 has 725 people who changed office, 600 within one country and 125 across a border), and sections 3 and 4 show `0`.

### Optional: validate the region walk and career moves

Two more Custom SQL queries for the same dashboard ([field reference](../projects/compensation-walk/region_walk_and_career_moves.md)). This script runs both with the walk and checks that they tie to it:

```bash
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -i /repo/sqlserver/09_validate_region_walk_and_career_moves.sql
```

Expected: every row with a `result` column says `PASS` (26,520 and 34,532 rows; FY26 1,850 promotions, 16 into Director and above).

## Step 5. Install the SQL Server driver for Tableau

Tableau on a Mac needs Microsoft's ODBC driver to talk to SQL Server. The simplest install is with [Homebrew](https://brew.sh), the standard Mac package manager.

> **Intel Mac?** Homebrew no longer supports Intel Macs (the installer stops with *"only supported on Apple Silicon processors"*). Use the JDBC route instead, which needs no Homebrew and was tested end to end on an Intel MacBook Pro:
>
> 1. Download the **.tar.gz** from [Microsoft JDBC Driver for SQL Server](https://learn.microsoft.com/en-us/sql/connect/jdbc/download-microsoft-jdbc-driver-for-sql-server) and unzip it.
> 2. Copy the jar into Tableau's driver folder:
>    ```bash
>    mkdir -p ~/Library/Tableau/Drivers
>    cp ~/Downloads/sqljdbc_*/enu/jars/mssql-jdbc-*.jre11.jar ~/Library/Tableau/Drivers/
>    ```
> 3. Restart Tableau and connect with **To a Server → More… → Other Databases (JDBC)**:
>    - **URL:** `jdbc:sqlserver://localhost:1433;databaseName=ArcadiaHR;encrypt=true;trustServerCertificate=true`
>    - **Dialect:** SQL-92
>    - **Username / Password:** `sa` and your password
>
> Then skip Step 6 and continue at Step 7. On Intel, drop `--platform linux/amd64` from Step 3: SQL Server runs natively.
>
> If Docker Desktop is closed, the container stops too. `docker update --restart unless-stopped arcadia-sql` makes it start again with Docker.

**5a. Install Homebrew (skip if `brew --version` already works)**

If you see `zsh: command not found: brew`, Homebrew isn't installed yet:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

It asks for your Mac password (nothing shows as you type) and to press Enter. It may also install Apple's Command Line Tools, which takes 5–10 minutes. It finishes with `==> Installation successful!` and a `==> Next steps:` block. Run the lines it prints there, normally:

```bash
echo >> ~/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Then check:

```bash
brew --version
```

Expected: `Homebrew 4.x.x` or newer.

**5b. Install the driver**

```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql18
```

This also installs `unixodbc`, which the driver needs. Confirm the driver is registered:

```bash
odbcinst -q -d
```

Expected:

```
[ODBC Driver 18 for SQL Server]
```

If Tableau later says a driver is missing, its connection dialog links to the official driver download page.

## Step 6. Connect Tableau to SQL Server

In Tableau Desktop:

1. **Connect → To a Server → Microsoft SQL Server.**
2. Fill in the dialog:
   - **Server:** `localhost, 1433`
   - **Database:** `ArcadiaHR`
   - **Authentication:** *Use a specific username and password*
   - **Username:** `sa`
   - **Password:** the password from Step 3
   - **Require SSL:** leave unchecked
3. Click **Sign In**.

You should land on the Data Source page with `ArcadiaHR` selected and the `dw`, `raw` and `rpt` schemas listed.

**If you get an SSL or certificate error,** copy [`tableau/sqlserver_trust_local_certificate.tdc`](../../tableau/sqlserver_trust_local_certificate.tdc) into `~/Documents/My Tableau Repository/Datasources/`, quit and reopen Tableau, and sign in again. The file tells the driver to trust the container's self-signed certificate.

## Step 7. Create the Custom SQL data source

1. On the Data Source page, double-click **New Custom SQL** in the left panel.
2. Paste the full contents of [`tableau/custom_sql_workforce_cost_bridge.sql`](../../tableau/custom_sql_workforce_cost_bridge.sql).
3. Click **Preview Results** to check it runs, then **OK**.
4. Rename the data source (top left) to **Workforce Cost Bridge (SQL Server)**.
5. Set the connection to **Extract** (top right), then go to a sheet. Tableau saves the extract.

Expected: 20 columns and 13,835 rows. The extract takes about a minute under emulation.

Why it's written this way: Tableau wraps Custom SQL in a subquery, so CTEs, `ORDER BY` and trailing `--` comments all break it. The query uses derived tables and `CROSS APPLY` instead. Comments at the top of the file explain each layer.

Why Extract: the query aggregates about 1.35 million worker-months on every refresh. An extract runs it once and makes the dashboard fast, which is the usual production pattern for heavy Custom SQL.

## Step 8. Add the snapshot as a second data source

1. **Data → New Data Source → Microsoft SQL Server**, with the same connection details.
2. Pick schema **rpt** and drag **vw_workforce_cost_snapshot** onto the canvas.
3. Rename it **Workforce Cost Snapshot (SQL Server)** and set it to **Extract**.

Expected: 24 columns and 233,866 rows.

Keep the two data sources separate. They have different grains, and joining them would duplicate dollars.

## Step 9. Build the first visualization: FY26 cost bridge waterfall

Use the **Workforce Cost Bridge** data source.

1. Drag **Fiscal Year** to Filters and keep only **2026**. Drag **Worker Type** to Filters and keep only **Employee** (release 3: the bridge also explains the contingent workforce's bill run-rate, as worker type **Contingent**).
2. Create a calculated field **Bridge Amount**:

   ```
   IF [Driver] = "Opening Run-Rate" THEN
       IIF([Fiscal Period] = "FY26 P01", [Loaded Usd Nominal], 0)
   ELSEIF [Driver] = "Closing Run-Rate" THEN
       0
   ELSE
       [Loaded Usd Nominal]
   END
   ```

   For a full fiscal year, the opening comes from the first month and every driver sums across all 12 months. The closing becomes the grand total in step 6.
3. Drag **Driver** to Columns. Right-click it, choose **Sort → Field → Driver Order (Sum) → Ascending**, then filter out **Closing Run-Rate**.
4. Drag **Bridge Amount** to Rows. Right-click it, choose **Quick Table Calculation → Running Total**, and change the mark type to **Gantt Bar**.
5. Create **Bar Size** = `-SUM([Bridge Amount])` and drag it to **Size**.
6. Turn on **Analysis → Totals → Show Row Grand Totals**, which adds the closing bar.
7. Create **Increase** = `SUM([Bridge Amount]) > 0` and drag it to **Color**.

**Check your numbers:**

| Driver | Expected (USD) |
|---|---:|
| Opening Run-Rate | 3,171,717,783 |
| Hires | +524,006,326 |
| Terminations | −408,961,394 |
| Transfers In / Out | +157,393,285 / −157,393,285 |
| Promotions | +24,784,185 |
| Demotions | −879,216 |
| Tenure & Market Adjustments | +116,038,891 |
| International Mobility | −787,039 |
| Conversions (contingent workers hired as employees) | +19,677,620 |
| Fringe Rate Changes | +9,537,549 |
| FX Rate Changes | −44,651,955 |
| **Grand Total (Closing)** | **3,410,482,750** |

(Warehouse release 3. There is no FTE Changes driver: every employee is 1.0 FTE. Hires + Conversions = 543,683,946, the Hires line before conversions were split out of it.)

With **Worker Type = Contingent** instead: Opening 1,073,453,800; Contingent Starts +872,484,118; Contingent Ends −674,446,779; Transfers In / Out +38,877,944 / −38,877,944; Contingent Rate Changes +6,550,467; Conversions −32,702,296; FX Rate Changes −7,713,108; Closing **1,237,626,203**. The two conversion lines net to −13,024,675: what swapping 270 contractors for employees saved in FY26, at run-rate.

If these match, your SQL Server, Custom SQL and Tableau calculation all agree with the published data.

## Step 10. Getting it onto Tableau Public

Tableau Desktop **Free Edition** can't publish to Tableau Public. Publishing needs the separate **Tableau Public** app, which only reads files. Because the SQL Server outputs use **the same column names** as the CSVs in `data/marts/`, switching sources is quick:

1. In your workbook, **Data → New Data Source → Text file** and pick `data/marts/mart_workforce_cost_bridge.csv`.
2. Right-click the SQL Server data source and choose **Replace Data Source…** → the CSV. Every field maps automatically because the names match.
3. Repeat for the snapshot with `mart_workforce_cost_snapshot.csv`.
4. Save as a packaged workbook (`.twbx`), open it in Tableau Public, and publish.

Keep the SQL Server version of the workbook too. Screenshots of the connection dialog, the Custom SQL editor and the extract make good evidence in the repo and in interviews.

## Everyday commands

```bash
docker stop arcadia-sql     # stop SQL Server (data is kept)
docker start arcadia-sql    # start it again
docker rm -f arcadia-sql    # delete the container (rebuild with Steps 3–4)
```

After pulling new data from GitHub, rerun Step 4. The scripts drop and recreate their tables, so they're safe to run repeatedly. Then refresh the extracts in Tableau.
