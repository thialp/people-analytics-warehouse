# Release 2: move Dashboards #1 and #2 to the new Custom SQL (Replace References guide)

How to point both published dashboards at the release 2 data on SQL Server, field by field, so nothing is missed and nothing is counted twice. Arcadia Systems is fictional and all data is synthetic.

| | Dashboard #1, Headcount & FTE Walk | Dashboard #2, Compensation Walk |
|---|---|---|
| Data today | Six CSVs from `data/marts/`, joined with relationships | Two Custom SQL extracts (`ArcadiaHR` = the walk, `Office Moves`) |
| Data after | **One Custom SQL**: [`tableau/custom_sql_headcount_fte_walk.sql`](../../../tableau/custom_sql_headcount_fte_walk.sql) | The same two Custom SQL files, updated: [`custom_sql_compensation_walk.sql`](../../../tableau/custom_sql_compensation_walk.sql), [`custom_sql_office_moves.sql`](../../../tableau/custom_sql_office_moves.sql); optional third: [`custom_sql_region_walk.sql`](../../../tableau/custom_sql_region_walk.sql) |
| Field names | **Kept**: every column has its CSV name, so every field keeps its caption | **Kept**: no field removed or renamed; three added |
| What changes in calcs | Nothing | Two **values** changed: `Leader` → `Sub-function` (view), `Relocation Adjustments` → `Same-Country Transfer Adjustments` (step) |
| Check on SQL Server | [`sqlserver/10_validate_headcount_fte_walk.sql`](../../../sqlserver/10_validate_headcount_fte_walk.sql) | `06`, `07`, `09` |
| Expected values | [Dashboard #1 check table](../headcount-fte-walk/expected_values.md) | [Dashboard #2 check table](../compensation-walk/expected_values.md) |

The new Dashboard #1 query was compared with the six CSVs joined together: **521,029 rows, the same 33 columns in the same order, every value identical** (`sqlserver/check_tsql_in_duckdb.py`). It runs in seconds.

## 0. Before Tableau (Mac)

```bash
cd ~/GitHub/people-analytics-warehouse
git pull
export MSSQL_SA_PASSWORD="$(docker exec arcadia-sql printenv MSSQL_SA_PASSWORD)"
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -i /repo/sqlserver/10_validate_headcount_fte_walk.sql
```

Expected:

```
Headcount & FTE walk Custom SQL returned 521029 rows in N seconds
1. Shape ...                      rows 521029 PASS · distinct keys 521029 PASS · month-ends 60 PASS
                                  functions 9 PASS · rows without a name from a dimension 0 PASS
2. Every slice and month closes   slice-months that do not close  0  PASS
3. FY26 ...                       opening 28447 · hires 5235 · voluntary 2942 · involuntary 726
                                  internal moves 3633 · promotions 2015 · closing 30014
                                  closing FTE x 10 293635 · closing part-time 2330      (all PASS)
```

Save a copy of each workbook first (File > Save As, `_release1`).

---

## 1. Dashboard #1: from six CSVs to one Custom SQL

### 1.1 Why one flat query is safe here

The CSV model was a fact (`mart_headcount_fte_walk.csv`) with five dimension files related on their keys. The Custom SQL joins the same five dimensions into each fact row. Each dimension key is unique in its dimension (one row per month, department, country, job family, grade), so the join is many-to-one: **no fact row is repeated, and every SUM is the same as before.** Check 1 of `10_validate` proves it (rows = distinct keys = 521,029).

### 1.2 Steps in Tableau, in order

1. **Add the new source.** Data > New Data Source > **Microsoft SQL Server**: the same connection as Dashboard #2 (server `localhost`, database `ArcadiaHR`, the trust-certificate setting from `tableau/sqlserver_trust_local_certificate.tdc`). Drag **New Custom SQL** to the canvas, paste the whole of `tableau/custom_sql_headcount_fte_walk.sql`, OK. Rename the source **Headcount Walk (SQL)**.
2. **Check types** on the Data Source tab, so they match what the workbook set on the CSVs:
   - `grade` and `fiscal_year` come as **String** (the query returns them as text);
   - `month_end_date` and `prior_month_end_date` are **Date**;
   - `headcount` and `part_time_headcount` are whole numbers, `fte` a decimal; default aggregation **Sum**.
3. **Replace Data Source.** Data > **Replace Data Source...**: Current = the CSV source, Replacement = **Headcount Walk (SQL)**, OK. This moves every calculated field, parameter reference, alias, sort, color and default format to the new source and remaps fields **by name**, which is why the names were kept. Fields that exist only in the old source are left with a red **!**.
4. **Replace References** for anything still red, in the order of the table in 1.3. For each: right-click the old field > **Replace References...** > pick the new field. Rows 9 to 13 are the only ones expected to be red (key columns that existed twice in the CSV model).
5. **Month lists.** Parameters `Start Month` and `End Month` > Edit > Allowable values **List** > **When workbook opens**: `Month End Date` (from **Headcount Walk (SQL)**). The list now runs Jul 2021 to Jun 2026 (60 months). Current values stay Jul 2025 and Jun 2026.
6. **Extract.** Data Source tab > Connection **Extract** > Extract Data (Hide All Unused Fields first). Expected about 521,029 rows.
7. **Close the CSV source** only when no field shows a red **!** (right-click the old source > Close). If Tableau says a field is still in use, find it with the Data pane search, Replace References, then close.
8. **Check every number** against the [Dashboard #1 check table](../headcount-fte-walk/expected_values.md) (FY26 first: 30,014 closing, +5.5%; 29,363.5 FTE; 5,235 hires, 17.9%; 10.1% voluntary turnover; 3,633 internal moves, 2,015 promotions).

### 1.3 Field mapping, in Replace References order

Old field = the field as Tableau named it on the CSV source (column name in title case; a key that existed in two files got the file name in brackets). New field = the field on **Headcount Walk (SQL)**. Used on the dashboard = the field is referenced by a sheet or a calc in the [build book](../headcount-fte-walk/executive_summary_build_book.md).

| # | Old field (CSV source) | From file | New field (Custom SQL) | Type | Used on the dashboard |
|---:|---|---|---|---|---|
| 1 | Month End Date | `mart_headcount_fte_walk.csv` | Month End Date | Date | **Yes**: `In Range`, every `K` and `WF` calc, `Start Month` / `End Month` lists, Trend |
| 2 | Movement Category | fact | Movement Category | String | **Yes**: every measure calc, waterfall columns, Trend filter (Closing), `Measure Option` |
| 3 | Movement Order | fact | Movement Order | Number | **Yes**: sort of the waterfall columns (Field, Minimum) |
| 4 | Movement Reason | fact | Movement Reason | String | **Yes**: `K Promotions`, `WF Promos` |
| 5 | Headcount | fact | Headcount | Number (whole) | **Yes**: every headcount measure |
| 6 | Fte | fact | Fte | Number (decimal) | **Yes**: every FTE measure |
| 7 | Part Time Headcount | fact | Part Time Headcount | Number (whole) | **Yes**: `K Close PT`, `TT Level PT` |
| 8 | Function Name | `mart_dim_department.csv` | Function Name | String | **Yes**: Turnover by function rows, `TO Top Function` |
| 9 | Month End Date (mart_dim_month.csv) | `mart_dim_month.csv` | Month End Date | Date | Only if a calc or the month lists used the dimension's copy |
| 10 | Department Id (mart_dim_department.csv) | `mart_dim_department.csv` | Department Id | String | Relationship key only |
| 11 | Country Code (mart_dim_country.csv) | `mart_dim_country.csv` | Country Code | String | Relationship key only |
| 12 | Job Family Code (mart_dim_job_family.csv) | `mart_dim_job_family.csv` | Job Family Code | String | Relationship key only |
| 13 | Grade (mart_dim_grade.csv) | `mart_dim_grade.csv` | Grade | String | Relationship key only |
| 14 | Department Id | fact | Department Id | String | No |
| 15 | Country Code | fact | Country Code | String | No |
| 16 | Job Family Code | fact | Job Family Code | String | No |
| 17 | Grade | fact | Grade | String | No |
| 18 | Prior Month End Date | `mart_dim_month.csv` | Prior Month End Date | Date | No |
| 19 | Fiscal Year | `mart_dim_month.csv` | Fiscal Year | String | No (`WF Period` builds the FY label from the date) |
| 20 | Fiscal Year Label | `mart_dim_month.csv` | Fiscal Year Label | String | No |
| 21 | Fiscal Quarter Label | `mart_dim_month.csv` | Fiscal Quarter Label | String | No |
| 22 | Fiscal Period | `mart_dim_month.csv` | Fiscal Period | String | No |
| 23 | Fiscal Month | `mart_dim_month.csv` | Fiscal Month | Number | No |
| 24 | Is Fiscal Year End | `mart_dim_month.csv` | Is Fiscal Year End | Boolean | No |
| 25 | Department Name | `mart_dim_department.csv` | Department Name | String | No |
| 26 | Sub Function | `mart_dim_department.csv` | Sub Function | String | No |
| 27 | Parent Org Unit Id | `mart_dim_department.csv` | Parent Org Unit Id | String | No |
| 28 | Cost Center | `mart_dim_department.csv` | Cost Center | String | No |
| 29 | Head Grade | `mart_dim_department.csv` | Head Grade | Number | No |
| 30 | Country Name | `mart_dim_country.csv` | Country Name | String | No |
| 31 | Region | `mart_dim_country.csv` | Region | String | No |
| 32 | Currency Code | `mart_dim_country.csv` | Currency Code | String | No |
| 33 | Pay Index | `mart_dim_country.csv` | Pay Index | Number | No |
| 34 | Job Family | `mart_dim_job_family.csv` | Job Family | String | No |
| 35 | Level Code | `mart_dim_grade.csv` | Level Code | String | No |
| 36 | Grade Level | `mart_dim_grade.csv` | Grade Level | String | No |
| 37 | Career Track | `mart_dim_grade.csv` | Career Track | String | No |
| 38 | Us Base Salary Usd | `mart_dim_grade.csv` | Us Base Salary Usd | Number | No |
| 39 | mart_headcount_fte_walk.csv (Count) and the other `(Count)` fields | each file | the new source's `(Count)` field | Number | Only if a sheet counts rows (none in the build book). Rows are slice lines, not people, so never use the count as a headcount |

The unused fields (14 to 38) map by name in step 3; they are listed so the check is complete, and they are ready for the Movement Drivers and Diagnostics pages.

### 1.4 Double counting: what to check, and the calcs that already prevent it

No new calculation is needed. The data has one row per month × slice × category × reason, as before, and the calcs already take levels from one month:

| Risk | Why it does not happen | Keep it that way |
|---|---|---|
| Dimension join repeats a fact row | Each dimension key is unique; `10_validate` check 1: rows = distinct keys | Do not add another table to this source without a unique key |
| Opening or Closing summed over several months | `K Open HC` reads Opening of the **Start Month** only, `K Close HC` Closing of the **End Month** only; `Walk Value` does the same | Never SUM `Headcount` over a range without a Movement Category and month condition |
| Internal moves counted twice (out and in) | Every move calc reads `Internal Moves In` only (`Internal Moves`, `K Promotions`, `WF Moves`) | Count moves from Moves In, never from Moves In + Out |
| FTE Changes counted as people | Their `Headcount` is 0 by design; the bar shows only in FTE mode (`Show Category`) | |
| Part-time counted on movement rows | `part_time_headcount` is 0 on every movement row; only Opening and Closing carry it | |
| Row count read as people | `(Count)` counts slice lines | Use SUM(Headcount) |

A one-minute check after step 3, on a scratch sheet: `Movement Category` = Closing and `Month End Date` = 30 Jun 2026 gives SUM(Headcount) **30,014** and SUM(Fte) **29,363.50**; the whole source has **521,029** rows (`(Count)`).

---

## 2. Dashboard #2: same fields, new SQL

No field was removed or renamed, so there is **no Replace References to do** if the Custom SQL is edited in place: Data Source tab > the Custom SQL table > **Edit Custom SQL Query** > paste the new file > OK. Tableau keeps every field, calc and format.

If you prefer the same route as Dashboard #1 (a new data source, then Replace Data Source), every field maps by name one to one; the tables below are the complete list to check.

### 2.1 Walk source (`ArcadiaHR`) — `custom_sql_compensation_walk.sql`

| # | Field | Type | Status | Used on the dashboard |
|---:|---|---|---|---|
| 1 | From Month End | Date | Unchanged | **Yes**: `In Pair`, period picker, Period Key |
| 2 | To Month End | Date | Unchanged | **Yes**: `In Pair`, period picker |
| 3 | Report Start Date | Date | **New** | For the "Data covers" note and `Default From` ([runbook B1](release_2_republish.md#b-new-columns-small-additions)) |
| 4 | Report As Of Date | Date | **New** | For the "Data covers" note and `Default To` |
| 5 | From Fiscal Period | String | Unchanged | Period labels |
| 6 | To Fiscal Period | String | Unchanged | **Yes**: `Pair Name` |
| 7 | From Fiscal Quarter | String | Unchanged | Period labels |
| 8 | To Fiscal Quarter | String | Unchanged | Period labels |
| 9 | Months Between | Number | Unchanged | Period labels |
| 10 | Pair Type | String | Unchanged; the value **Custom Range** no longer exists (88 pairs) | **Yes**: period picker, `Pair Name`, quick picks |
| 11 | View Order | Number | Unchanged | View rail sort |
| 12 | View Name | String | Unchanged; value **`Leader` → `Sub-function`** | **Yes**: `In Pair`, `p_View`, View rail, `Panel Title`, `Group In View` |
| 13 | Group Id | String | Unchanged | Group picker |
| 14 | Group Name | String | Unchanged | **Yes**: `In Pair`, `p_Group`, group picker |
| 15 | Group Parent | String | Unchanged | Growth by region (today; replaced by the region walk in B3) |
| 16 | Group Leader | String | Unchanged | Tooltips |
| 17 | Step Order | Number | Unchanged | Waterfall sort |
| 18 | Step | String | Unchanged; value **`Relocation Adjustments` → `Same-Country Transfer Adjustments`** | **Yes**: waterfall, `TD Key`, `Waterfall Size`, `step` aliases |
| 19 | Step Group | String | Unchanged | **Yes**: compact waterfall, `TD Group`, `TD Step Count` |
| 20 | Movement Reason | String | Unchanged | Tooltips |
| 21 | Worker Count | Number | Unchanged | **Yes**: `TD People` |
| 22 | Headcount | Number | Unchanged | **Yes**: KPI cards, Growth by region (today) |
| 23 | Fte | Number | Unchanged | KPI cards |
| 24–27 | Base Usd Nominal, Base Usd Constant, Loaded Usd Nominal, Loaded Usd Constant | Number | Unchanged | **Yes**: `Lens Value` / `Walk Row` (Total payroll lens, Cost and Currency toggles) |
| 28–31 | Avg Base Usd Nominal, Avg Base Usd Constant, Avg Loaded Usd Nominal, Avg Loaded Usd Constant | Number | Unchanged | **Yes**: `Lens Value` / `Walk Row` (Pay per FTE lens) |
| 32–35 | Pct Base Usd Nominal, Pct Base Usd Constant, Pct Loaded Usd Nominal, Pct Loaded Usd Constant | Number | Unchanged | Percent labels, if used |

### 2.2 Office moves source (`Office Moves`) — `custom_sql_office_moves.sql`

| # | Field | Type | Status | Used on the dashboard |
|---:|---|---|---|---|
| 1–2 | From Month End, To Month End | Date | Unchanged | **Yes**: `Move In Scope` |
| 3–4 | Report Start Date, Report As Of Date | Date | **New** | Optional |
| 5–7 | From Fiscal Period, To Fiscal Period, Months Between | String / Number | Unchanged | Labels |
| 8 | View Order | Number | Unchanged | |
| 9 | View Name | String | Unchanged; value **`Leader` → `Sub-function`** | **Yes**: `Move In Scope` |
| 10 | Group Id | String | Unchanged | |
| 11 | Group Name | String | Unchanged | **Yes**: `Move In Scope`, `Moves Scope` |
| 12 | Group Parent | String | Unchanged | |
| 13 | Group Side | String | Unchanged | **Yes**: see 2.5 |
| 14–20 | From Location Id, From Office, From City, From Country, From Region, From Latitude, From Longitude | | Unchanged | **Yes**: map lines, `Office Pair`, routes |
| 21–27 | To Location Id, To Office, To City, To Country, To Region, To Latitude, To Longitude | | Unchanged | **Yes**: map lines and arrival dots, `Office Label`, routes |
| 28 | Flow Scope | String | Unchanged | **Yes**: `Movers Within`, `Movers Across`, `Route Class` |
| 29–31 | Flow Scope Label, Region Scope, Move Reason | String | Unchanged | Tooltips |
| 32 | Workers | Number | Unchanged | **Yes**: every mover count |
| 33 | Open Headcount | Number | **New** | Map title share ([runbook B2](release_2_republish.md#b-new-columns-small-additions)) |

### 2.3 Calcs to edit because two values changed

| Calc or setting | Change |
|---|---|
| Parameter `p_View` (list value) | `Leader` → `Sub-function` |
| Alias on `View Name` | Clear the alias on `Leader` (the data now says `Sub-function`) |
| `Panel Title` (and `Selected Group` if the fallback pickers exist) | `WHEN "Leader"` → `WHEN "Sub-function"`; parameter `p_GroupLeader` → `p_GroupSubfunction` |
| `TD Key` | `WHEN "Relocation Adjustments" THEN "Relocation"` → `WHEN "Same-Country Transfer Adjustments" THEN "Same-country move"` |
| `TD Why` | `WHEN "Relocation"` → `WHEN "Same-country move"` |
| Alias on `Step` | Give `Same-Country Transfer Adjustments` the alias `Same-country move` |
| `Pair Name` | The `Custom Range` branch is never reached now; leave it or delete it |

Search the Data pane for `Leader` and `Relocation` afterwards: nothing should remain.

### 2.4 Optional third source: region walk

For Growth by region to follow View and Group ([runbook B3](release_2_republish.md#b-new-columns-small-additions)): `custom_sql_region_walk.sql`, fields From Month End, To Month End, Report Start Date, Report As Of Date, From Fiscal Period, To Fiscal Period, Months Between, View Order, View Name, Group Id, Group Name, **Region**, **Opening Headcount**, **Hires**, **Exits**, **Transfers In**, **Transfers Out**, **Region Moves In**, **Region Moves Out**, **Closing Headcount**. All new; nothing to replace.

### 2.5 Double counting: the filters every sheet needs

These sources are pre-computed for **every** date pair, view and group, so the same people appear many times on purpose. Each sheet must narrow to one pair, one view and one group before it sums.

| Source | Repeats on purpose | Guard (existing or new calc) |
|---|---|---|
| Walk | Every person once per view (6 views) and once per date pair that covers them | `In Pair` = True on every sheet (pair + view + group). Never total across views or pairs |
| Walk | Opening and Closing are levels | Read them from the Opening / Closing steps only, never summed over steps |
| Walk | `worker_count` counts people per step; a person can be in several steps (a hire who is also promoted) | Do not SUM `worker_count` across steps for "people"; the KPI people come from Opening / Closing `headcount` |
| Walk | `avg_*` are contributions to one group's average | Add them only within one pair + view + group (the waterfall does) |
| Office moves | In the Office and Country views a mover appears **twice**: `group_side` From (left the office) and To (joined it); Company view has each mover once (`Both`) | `Move In Scope` = True, and on Office or Country views filter `Group Side` to `To` for arrivals or `From` for departures. The company totals use the Company view |
| Office moves | `open_headcount` is repeated on every row of a group | Use MIN or ATTR, never SUM: `Moves Open HC` = `MIN(IF [Move In Scope] THEN [open_headcount] END)` |
| Region walk (new) | One row per region inside every group of every view and pair | `RW In Pair` = True (pair + view + group); then SUM over regions is the group total |

FY26 Company checks after the switch: waterfall "Average pay per FTE rose $3,579 (+3.3%)" and "Total payroll rose $270.4M (+8.8%)"; map "725 people changed office (2.5% of headcount); 83% stayed inside one country"; Growth by region "Arcadia overall +5.5% (28,438 | 30,005)". Full table: [Dashboard #2 check table](../compensation-walk/expected_values.md).

---

## 3. After both

Refresh the extracts, reset each dashboard to its default view, and **File > Save to Tableau Public As...** with the same names (`arcadia_headcount_fte_walk`, `Arcadia Compensation Walk`), so the URLs stay. Details: [release_2_republish.md](release_2_republish.md), section C.
