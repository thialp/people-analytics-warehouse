# Dashboard #3 kickoff: where things stand (2026-10-23)

Read this first in a new conversation about Dashboard #3, then the plan: `claude/release_3_rebuild_dashboard_3.md` (repo: `docs/projects/workforce-planning/release_3_rebuild_dashboard_3.md`).

## What this dashboard is

**Workforce Planning** (case study 3), not the Global Workforce Footprint. Unit everywhere: **PID** (position). Question: how many PIDs do we have, how many are vacant, how well do we fill them against the Budget, and what changes when we refill one (seat vs. butt: the PID's level and office before and after).

## Done

| Phase | Status |
|---|---|
| 0. Plan, shapes, mocks | Plan revision 3.1 approved; mocks in `docs/images/workforce_planning_*mock.png` |
| 1. Data release 3.1 | Merged to `main` (PR #53). Contractors hold PIDs in Keystone; new PIDs are created at requisition approval; 81 tests pass; T-SQL checker matches |
| 2. Mac | On `main`; SQL Server rebuilt; 08, 12, 14 all PASS; Custom SQL files copied to `~/Documents/Tableau/Tableau Public/ArcadiaHR/Custom SQL - Release 3/03 Workforce Planning`; shapes `d3_field_capsule`, `d3_reset` in `My Tableau Repository/Shapes/Arcadia D3` |

PID ledger, Jun 30, 2026 (FY26 · Company): **51,163** = 30,005 filled by employees + 11,941 by contractors + 8,689 vacant previously held (7,712 contractor PIDs) + 528 vacant new.
Mock state FY25 · Company: 48,017 = 28,438 + 10,707 + 8,294 + 578.

## Decisions to keep

- No Version toggle; plan = Budget (data source filter). Top bar like #1 with Period and View popovers, info ⓘ and the short reset icon.
- KPIs: PIDs · Vacant, previously held · Vacant, new · PIDs filled · Backfills with a level change. Hovers are small bar charts (Viz in Tooltip).
- KPI 2 keeps contractor PIDs; its hover says how many are contractor PIDs (D17).
- Main card = map of backfilled PIDs that changed office (prior holder's office to new holder's), with a From / To routes table. Right cards: backfill changes (5 exclusive categories), net-new by function (bar inside a bar), vacant PIDs by age.
- No "→" or "▾" glyphs in text; chevron is drawn in the capsule; periods named by months ("FY26 Q3 · Jan – Mar 26").
- **New workbook** (D15). The first build (`Arcadia Workforce Planning.twb`, left rail) is archived; only formulas listed in plan section 5.1 are copied from it.

## Next: phase 3 onward (Thiago builds in Tableau, Claude guides and checks)

Sections 5 → 7 (workbook, sources, parameters, calcs; checkpoints 1–2), then 8, 9, 13 (top bar, popovers, actions), 10 (KPI band and hovers), 11 (cards), 12 (layout), 14–15 (checks, click tests), 16 (publish as `arcadia_workforce_planning`). One screenshot per phase; Claude checks it against section 14.

## Later

Case study 7, PID Fill Forecast: its own dashboard after this one is published (plan section 18).
