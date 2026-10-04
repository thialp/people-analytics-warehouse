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

If you already cloned it with GitHub Desktop, skip this step. Otherwise:

```bash
mkdir -p ~/Documents/GitHub
cd ~/Documents/GitHub
git clone https://github.com/thialp/people-analytics-warehouse.git
ls people-analytics-warehouse
```

Expected output:

```
README.md  data  docs  generator  pipeline  requirements.txt  sql  sqlserver  tableau  tests
```

## Step 3. Start SQL Server

Pick a password for the `sa` (admin) account. It needs at least 8 characters with upper case, lower case, a number and a symbol. Avoid `!`, because zsh treats it specially. This example uses `Arcadia#Local2026`:

```bash
export MSSQL_SA_PASSWORD='Arcadia#Local2026'

docker run -d --name arcadia-sql \
  --platform linux/amd64 \
  -e "ACCEPT_EULA=Y" \
  -e "MSSQL_PID=Developer" \
  -e "MSSQL_SA_PASSWORD=$MSSQL_SA_PASSWORD" \
  -p 1433:1433 \
  -v ~/Documents/GitHub/people-analytics-warehouse:/repo:ro \
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

`-C` tells `sqlcmd` to trust the container's self-signed certificate. `build_all.sql` runs scripts 01 to 05 in order:

| Script | What it does |
|---|---|
| `01_create_database.sql` | Creates the `ArcadiaHR` database and the `raw`, `dw` and `rpt` schemas |
| `02_load_raw.sql` | Lands each CSV as text with `BULK INSERT` |
| `03_build_dw.sql` | Types and cleans the data, resolves pay corrections, builds the fiscal calendar and the indexed worker month-end snapshot |
| `04_create_reporting_views.sql` | Creates `rpt.vw_workforce_cost_snapshot` |
| `05_validate.sql` | Checks row counts and control totals |

Expected output, abbreviated (2–5 minutes under emulation):

```
Created database ArcadiaHR
Schemas ready: raw, dw, rpt
raw.dim_worker                      19276 rows
raw.fact_job_history                26832 rows
raw.fact_compensation_history       65260 rows
...
TableName                       RowsLoaded
dw.DimWorker                         19276
dw.FactJobHistory                    26832
dw.FactCompensationHistory           64898
dw.MonthEndCalendar                     49
dw.WorkerMonthEndSnapshot           592823
Created view rpt.vw_workforce_cost_snapshot
1. Row counts
check_name                          actual   expected  result
dw.DimWorker rows                    19276      19276  PASS
...
3. Control totals (executive officers excluded)
month_end_date  headcount  fte       loaded_usd_nominal  loaded_usd_constant
2022-06-30      11000      10883.10  1126993109.33       1151151241.43
2026-06-30      13189      12928.00  1566743212.90       1551634565.71
```

Every row in section 1 should say `PASS`, and the control totals should match exactly.

**If `sqlcmd` isn't found,** older images keep it at `/opt/mssql-tools/bin/sqlcmd`. Use that path and drop the `-C`.

## Step 5. Install the SQL Server driver for Tableau

Tableau on a Mac needs Microsoft's ODBC driver to talk to SQL Server. The simplest install is with [Homebrew](https://brew.sh). If you don't have Homebrew, install it first with the one-line command on brew.sh.

```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql18
```

Expected last line:

```
==> Summary
🍺  /opt/homebrew/Cellar/msodbcsql18/...
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

**If you get an SSL or certificate error,** copy [`tableau/sqlserver_trust_local_certificate.tdc`](../tableau/sqlserver_trust_local_certificate.tdc) into `~/Documents/My Tableau Repository/Datasources/`, quit and reopen Tableau, and sign in again. The file tells the driver to trust the container's self-signed certificate.

## Step 7. Create the Custom SQL data source

1. On the Data Source page, double-click **New Custom SQL** in the left panel.
2. Paste the full contents of [`tableau/custom_sql_workforce_cost_bridge.sql`](../tableau/custom_sql_workforce_cost_bridge.sql).
3. Click **Preview Results** to check it runs, then **OK**.
4. Rename the data source (top left) to **Workforce Cost Bridge (SQL Server)**.
5. Set the connection to **Extract** (top right), then go to a sheet. Tableau saves the extract.

Expected: 20 columns and 11,317 rows. The extract takes about a minute under emulation.

Why it's written this way: Tableau wraps Custom SQL in a subquery, so CTEs, `ORDER BY` and trailing `--` comments all break it. The query uses derived tables and `CROSS APPLY` instead. Comments at the top of the file explain each layer.

Why Extract: the query aggregates about 600,000 worker-months on every refresh. An extract runs it once and makes the dashboard fast, which is the usual production pattern for heavy Custom SQL.

## Step 8. Add the snapshot as a second data source

1. **Data → New Data Source → Microsoft SQL Server**, with the same connection details.
2. Pick schema **rpt** and drag **vw_workforce_cost_snapshot** onto the canvas.
3. Rename it **Workforce Cost Snapshot (SQL Server)** and set it to **Extract**.

Expected: 24 columns and 136,806 rows.

Keep the two data sources separate. They have different grains, and joining them would duplicate dollars.

## Step 9. Build the first visualization: FY26 cost bridge waterfall

Use the **Workforce Cost Bridge** data source.

1. Drag **Fiscal Year** to Filters and keep only **2026**.
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
| Opening Run-Rate | 1,421,100,125 |
| Hires | +241,062,610 |
| Terminations | −182,610,580 |
| Transfers In / Out | +63,332,223 / −63,332,223 |
| Promotions | +15,029,490 |
| Merit & Adjustments | +49,922,724 |
| International Mobility | +310,822 |
| FTE Changes | −3,815,134 |
| Fringe Rate Changes | +11,351,582 |
| FX Rate Changes | +14,391,573 |
| **Grand Total (Closing)** | **1,566,743,213** |

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
