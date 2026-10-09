# Office moves: who changed office, and where to

The office-moves query is the companion of the compensation walk. It answers one question for any two month-ends and any group of people: **which people changed office, from which office to which.** It exists so that a map of office moves on the Compensation Walk dashboard follows the same filters (date pair, view, group) as every other sheet, instead of showing a company-wide picture next to a filtered one.

| | |
|---|---|
| Tableau file | [`tableau/custom_sql_office_moves.sql`](../../../tableau/custom_sql_office_moves.sql), a second Custom SQL on the same SQL Server connection as the walk |
| DuckDB twin | [`sql/03_marts/mart_office_moves.sql`](../../../sql/03_marts/mart_office_moves.sql), 260,464 rows, same columns and values |
| Checks | tests 39 and 40 (DuckDB, CI); [`sqlserver/07_validate_office_moves.sql`](../../../sqlserver/07_validate_office_moves.sql) (SQL Server) |
| Not exported | the mart is not written to `data/marts/` as a CSV: the workbook reads SQL Server |

`mart_mobility_flows` (monthly, company-wide, used by the Workforce Footprint case study) is unchanged. It cannot be filtered by department, function or leader because its rows carry only the two offices; this query carries the same keys as the walk.

## Rules

1. **A mover** is a worker present at both month-ends whose office differs. Only the From and To snapshots are compared, as in the walk: A → B → C is one move A → C, and A → B → A is no move. That is why FY26 shows 345 movers here and 392 in the monthly flows (the monthly view counts every hop).
2. **Executive officers** are excluded, as in the walk.
3. **The same grid** as the walk (136 quarter-end pairs plus 48 month-over-month pairs, shown at the two `GRID` markers). Keep both files identical, or a date pair on the dashboard will have a walk and no map.
4. **The same six views and group keys** as the walk: Company (`ORG-000`), Function, Leader, Department, Office (`LOC-nnn`) and Country (ISO code). `group_name` is built the same way, so `view_name = [p_View] AND group_name = [p_Group]` filters both queries.

## Which group a move belongs to: `group_side`

A move belongs to the group the person is in at each end of the pair.

| `group_side` | Meaning | Where it appears |
|---|---|---|
| `Both` | The group is the same at both ends: a move inside the group | Company (always); Function, Leader and Department when the mover stayed in the group; Country for moves inside one country |
| `From` | The person was in this group at the From date and left it | Office (always); Country for moves across a border; org views when the mover also changed department |
| `To` | The person joined this group by the To date | Same as `From`, on the receiving group |

So for any one selected group, the people moving in that group are `SUM(workers)`; `group_side` splits inbound from outbound where that matters. A mover who changed office *and* department appears once in each group they were in, never twice in the same group.

**Ties to the walk (test 39).** In the Office and Country views, `To` equals the walk's Transfers In headcount and `From` equals Transfers Out, for every group and date pair. The count of people moving across a border (118 in FY26) equals the walk's *International Transfer Adjustments* people, while relocations inside a country (227) are more than the walk's *Relocation Adjustments* people (216), because a relocation only produces a pay adjustment when the new office has a different pay zone.

## Columns

| Column | Meaning |
|---|---|
| `from_month_end`, `to_month_end` | The date pair, as in the walk |
| `from_fiscal_period`, `to_fiscal_period`, `months_between` | Labels for the pair |
| `view_order`, `view_name`, `group_id`, `group_name`, `group_parent` | The view and group, identical to the walk's columns of the same names |
| `group_side` | `Both`, `From` or `To` (above) |
| `from_location_id`, `from_office`, `from_city`, `from_country`, `from_region`, `from_latitude`, `from_longitude` | The office the person left |
| `to_location_id`, `to_office`, `to_city`, `to_country`, `to_region`, `to_latitude`, `to_longitude` | The office they moved to |
| `flow_scope` | `Domestic` or `International` |
| `flow_scope_label` | `Within one country` or `Across a border`, for legends |
| `region_scope` | `Same region` or `Across regions` |
| `move_reason` | `Relocation` (inside a country) or `International Transfer`, from the pay ledger; `Other` if the ledger has none |
| `workers` | People who moved on this office pair under this group, side and reason |

Every office has coordinates (test 32), so a line is always `MAKELINE(MAKEPOINT(from_latitude, from_longitude), MAKEPOINT(to_latitude, to_longitude))`.

## Worked example: FY26, 30 Jun 2025 to 30 Jun 2026

| View | Side | People | Reads as |
|---|---|---|---|
| Company | Both | 345 | 345 people changed office: 227 within one country, 118 across a border |
| Office | To | 345 | The same 345, counted at the office each joined |
| Office | From | 345 | ... and at the office each left (Bengaluru 61, Hyderabad 50 and Austin HQ 42 lose the most) |
| Country | Both | 227 | Moves inside one country |
| Country | To | 118 | The cross-border moves, counted at the receiving country |

## Size and run time

Movers are aggregated by date pair, departments, offices and reason before the six-view expansion, which keeps the result at 260,464 rows. Only people who changed office go through the six-view expansion (the walk expands everyone), so the query does less work than the walk. Run [`07_validate_office_moves.sql`](../../../sqlserver/07_validate_office_moves.sql) to print the actual SQL Server time on your machine.
