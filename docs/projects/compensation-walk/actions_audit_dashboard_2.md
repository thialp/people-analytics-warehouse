# Dashboard #2: actions audit (workbook as of Oct 17, 2026)

Read from the Dashboard > Actions dialog (61 actions). Verdict per action; nothing here needs a rebuild, only four renames, three additions and two deletions.

## Works as built (keep)

| Group | Actions | Check |
|---|---|---|
| Open one popover, close the others | `Open period panel`, `Open group panel`, `Open info`; `Close group panel when period opens`, `Close info when period opens`, `Close period when info opens`, `Close group when info opens`, `Close info when group opens` | Each opener sets the other two parameters FALSE. Complete: 3 openers × 2 others |
| Close on ✕ / pick / view change | `Close on ✕` (Period Close), `Close panel on X` (Panel Close), `Close on pick` (Period Panel), `Close panel on pick` (Group Panel), `Close on view change`, `Close panel on view change`, `Close info on view change` (Rail View), `Close info on reset` | Info closes through the ⓘ/ⓧ button itself, so no `Close info on ✕` is needed (unlike #1, where the ✕ sheet is a separate sheet) |
| Selections | `Set From`, `Set To` (Period Panel), `Set span` / `Set group` (Group Panel), `Set group from view`, `Set view` (Rail View), `Set lens`, `Set cost`, `Set currency` | One action per parameter |
| Reset | `Reset from, to, span, view, group, lens, cost, currency, period panel, group panel` | Ten parameters, all from the Reset sheet |
| Deselect (13) | Cost Toggle, Currency Toggle, Group Field, Group Panel, Info Button, Lens Toggle, Panel Close, Period Close, Period Field, Period Panel, Rail View, Reset, Span List | All `zzTrue` → `zzFalse`, Select, same sheet |

## Fix: two names are swapped (behaviour is right, names mislead)

| Now | Source → target | Rename to |
|---|---|---|
| `Close period panel when group opens` | Span List → `p_Span` | `Set span` (it is the span picker) |
| `Set span` | Group Field → `p_PeriodOpen` | `Close period panel when group opens` |

Optional tidy so the list sorts by popover (do while you are in the dialog): `Close on pick` → `Close period on pick`; `Close on view change` → `Close period on view change`; `Close on ✕` → `Close period on ✕`; `Close panel on pick` → `Close group on pick`; `Close panel on view change` → `Close group on view change`; `Close panel on X` → `Close group on ✕`; `Close group panel when period opens` and `Close period panel when group opens` stay.

## Add

| Action | Source → target | When |
|---|---|---|
| `Set detail` (Change Parameter, Select) | `Detail Toggle` → `p_Expand` ← `Detail Pick` | Phase 4 (Summary \| By driver toggle), G1 8.1 |
| `Reset detail` (Change Parameter, Select) | `Reset` → `p_Expand` ← `Default Expand` (= FALSE, added to the Reset sheet's Detail) | Phase 4. #2 has no such action today; without it Reset would leave "By driver" open |
| `Deselect` filter for every sheet that is clickable but not yet listed | `Detail Toggle`, `KPI Hover 1..5`, `Title`, `Rail Footnote` is a text object (no action needed) | Phases 3 and 4; follow G2 5.4 (Titles and headline sheets are set "not selectable" in #1, no action) |

## Delete (phase 4)

`Expand` and `Collapse` (`p_Expand`, source "Summary" with no sheet: orphans). They go when the Summary | By driver toggle replaces `Btn Expand` / `Btn Collapse`. Before that they are the actions behind the "Expand · 9 drivers" button, so keep them until then.

## Check after any change

Open each popover in turn: opening one closes the other two; picking a value, clicking ✕, changing the view and pressing Reset all close what they should; no sheet keeps a highlight after a click.
