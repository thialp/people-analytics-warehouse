# Region walk and career moves

Two queries added in release 2 for the Compensation Walk dashboard, keyed exactly like the walk (date pair × view × group), so the same parameters (`p_From`, `p_To`, `p_View`, `p_Group`) filter them. Each is a Tableau Custom SQL file with a DuckDB twin that produces the same rows:

| Query | Tableau Custom SQL | DuckDB mart | Rows |
|---|---|---|---:|
| Region walk | [`custom_sql_region_walk.sql`](../../../tableau/custom_sql_region_walk.sql) | `mart_region_walk` | 26,520 |
| Career moves | [`custom_sql_career_moves.sql`](../../../tableau/custom_sql_career_moves.sql) | `mart_career_moves` | 34,532 |

Arcadia Systems is fictional and all data is synthetic.

## Region walk

**Question.** For the selected period and group, how did headcount move in each region, and where did people leave from?

The walk has no region split inside a group, so the Growth by Region card could only show the whole company. This query is a headcount walk per region for every group of the six views, and it closes exactly in every row:

```
opening + hires - exits + transfers_in - transfers_out + region_moves_in - region_moves_out = closing
```

| Column | Meaning |
|---|---|
| `from_month_end`, `to_month_end`, `report_start_date`, `report_as_of_date`, `from_fiscal_period`, `to_fiscal_period`, `months_between` | As in the walk |
| `view_order`, `view_name`, `group_id`, `group_name` | As in the walk |
| `region` | The region of the person's office at that end of the pair |
| `opening_headcount`, `closing_headcount` | People in the group and region at the From and To month-ends |
| `hires`, `exits` | People hired into, or who left the company from, the group and region |
| `transfers_in`, `transfers_out` | People who joined or left the **group** (the walk's Transfers In and Out), counted in the region of their office at the end where they were in the group |
| `region_moves_in`, `region_moves_out` | People who stayed in the group but moved to an office in another region |

**Departures by region** = `exits + transfers_out + region_moves_out`. **Growth %** = `SUM(closing_headcount) / SUM(opening_headcount) - 1`.

**Ties (test 57).** Summed over regions, each group's opening, hires, exits, transfers and closing equal the walk's headcount lines, and region moves in and out cancel inside a group. Company opening and closing by region equal the month-end snapshot counted by office region, and every view has the same region totals as the company (each view splits the whole company once).

**FY26, company (30 Jun 2025 → 30 Jun 2026):**

| Region | Opening | Closing |
|---|---:|---:|
| North America | 9,909 | 10,426 |
| Asia Pacific | 8,524 | 9,005 |
| Europe | 6,665 | 7,043 |
| Latin America | 2,225 | 2,356 |
| Middle East & Africa | 1,115 | 1,175 |
| **Total** | **28,438** | **30,005** |

In the Function view, Technology closes North America at 3,431 (opening 3,211): the card now follows the group.

## Career moves

**Question.** Who was promoted or demoted in the period, from which grade to which, and how many moves reached Director and above?

| Column | Meaning |
|---|---|
| `from_month_end` … `group_name` | As in the walk; the group is the one the person is in at the **To** date (as the walk's Promotions and Demotions) |
| `move_type` | `Promotion` or `Demotion` |
| `from_grade`, `from_grade_level`, `to_grade`, `to_grade_level` | The grade left and the grade reached (1–12; level names as in `dim_job_level`) |
| `director_and_above` | The move is at grade 7 (Director) or above on either side |
| `into_director` | A promotion that crosses into Director and above (from grade 6 or below to 7 or above) |
| `moves` | Grade changes on this row. A person promoted twice in the period is two moves |
| `workers` | People on this row (distinct within the row) |

A move is a change of grade in the job history. The population is the walk's: people present at both month-ends, executive officers excluded.

**Two sources, one answer (test 58).** The walk counts promotions from pay records (the pay ledger), this query from grade changes in the job history. The number of people promoted, and demoted, agrees for every date pair; career moves never has fewer moves than the walk has people in a group; and every view adds up to the company.

**FY26, company:** 1,850 promotions (1,824 people: 26 were promoted twice), 148 demotions, **16 promotions into Director and above** (all grade 6 → 7) and 2 more within that bracket (grade 7 → 8).

## Running them

Both run in SQL Server with [`09_validate_region_walk_and_career_moves.sql`](../../../sqlserver/09_validate_region_walk_and_career_moves.sql), which also runs the walk and checks the ties. Without SQL Server, [`check_tsql_in_duckdb.py`](../../../sqlserver/check_tsql_in_duckdb.py) compares both files with their DuckDB marts row for row.
