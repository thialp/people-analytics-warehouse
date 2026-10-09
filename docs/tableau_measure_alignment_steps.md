# Headcount & FTE Walk: cards that match the waterfall, and a period picker that cannot break

Two problems from your screenshots, one fix each. **No data change is needed**: the walk file already carries both headcount and FTE on every line (and the new `part_time_headcount` column is in the CSV I sent). Load that CSV once and do everything below in Tableau.

## 0. What is actually happening

In your Jul to Aug 2025 screenshot the toggle is on **FTE**, so the waterfall shows FTE (+377 hires, −221 voluntary leavers, −5 FTE changes, closing 12,389). The KPI cards 3 and 4 always show **people** (381 hires, 226 leavers). They are both right; they are two views of the same events. This is exactly what part-time does:

| Jul to Aug 2025 | People (headcount) | FTE | Why they differ |
|---|---|---|---|
| Hires | 381 | 376.9 | some hires work 0.8 or 0.5 schedules |
| Voluntary leavers | 226 | 221.3 | same, for leavers |
| Involuntary leavers | 44 | 43.4 | same |
| FTE changes | 0 | −5.4 | people who stayed but changed schedule (no headcount effect) |
| Opening → Closing | 12,510 → 12,621 | 12,281.7 → 12,388.5 | both reconcile exactly |

Headcount: 12,510 + 381 − 226 − 44 = 12,621. FTE: 12,281.7 + 376.9 − 221.3 − 43.4 − 5.4 = 12,388.5. A part-time hire is one person but less than one FTE, so the two lists can never be identical. What we can do is make sure the page never shows one unit next to the other without saying so. Four changes:

1. Cards 3 and 4 **follow the toggle**, so they always equal the bars beside them, and their titles say which unit they show.
2. The waterfall **title** follows the toggle too (today it quotes people while the bars show FTE).
3. The **tooltip** bridges people to FTE on every movement bar ("381 people = 376.9 FTE").
4. The toggle capsule is clearly visible, so the selected unit is obvious.

## 1. Cards 3 and 4 follow the Measure toggle

Rule: **Cards 1 and 2 are fixed** (closing headcount, closing FTE: they are the bridge between the units). **Cards 3 and 4 follow the toggle** and show the other unit in their note. Card 5 counts people changing teams (not a waterfall bar), so it stays in people.

New fields (FTE versions of hires and voluntary leavers):
```
// K Hires FTE
ZN(SUM(IF [In Range] AND [Movement Category] = "Hires" THEN [Fte] END))
```
```
// K Leavers Vol FTE
ZN(-SUM(IF [In Range] AND [Movement Category] = "Voluntary Terminations" THEN [Fte] END))
```
```
// K Hires Show   (the number the card headlines)
IF [Measure] = "Headcount" THEN [K Hires] ELSE ROUND([K Hires FTE], 0) END
```
Four text helpers, all the same comma pattern as `K Open Str`. Shown once, for the first; make the other three by swapping the field:
```
// K Hires HC Str
IF [K Hires] >= 1000
THEN STR(DIV(INT([K Hires]), 1000)) + "," + RIGHT("00" + STR(INT([K Hires]) % 1000), 3)
ELSE STR(INT([K Hires])) END
```
- `K Hires FTE Str` on `ROUND([K Hires FTE], 0)`
- `K Vol HC Str` on `[K Leavers Vol]`
- `K Vol FTE Str` on `ROUND([K Leavers Vol FTE], 0)`

(Wrap each in `INT(...)` as in the example.) The hire rate as text:
```
// K Hire Rate Str
STR(DIV(INT(ROUND(ZN([Hire Rate (annualized)]) * 1000, 0)), 10)) + "." +
STR(INT(ROUND(ZN([Hire Rate (annualized)]) * 1000, 0)) % 10) + "%"
```

Replace these four existing fields:
```
// KPI 3 Title
IF [Measure] = "Headcount" THEN "Hires" ELSE "Hires (FTE)" END
```
```
// KPI 3 Value
IF NOT [K Valid] THEN "—"
ELSEIF [K Hires Show] >= 1000
THEN STR(DIV(INT([K Hires Show]), 1000)) + "," + RIGHT("00" + STR(INT([K Hires Show]) % 1000), 3)
ELSE STR(INT([K Hires Show])) END
```
```
// KPI 3 Note
IF NOT [K Valid] THEN ""
ELSEIF [Measure] = "Headcount"
THEN [K Hire Rate Str] + " annualized · " + [K Hires FTE Str] + " FTE"
ELSE [K Hires HC Str] + " people · " + [K Hire Rate Str] + " annualized"
END
```
```
// KPI 4 Note   (the rate itself is always headcount-based; the note shows both units)
IF NOT [K Valid] THEN ""
ELSEIF [Measure] = "Headcount"
THEN [K Vol HC Str] + " left by choice · " + [K Vol FTE Str] + " FTE"
ELSE [K Vol FTE Str] + " FTE left by choice · " + [K Vol HC Str] + " people"
END
```
`KPI 3 Title` was a constant before; it is already on the Label shelf of its layer, so nothing else changes on the sheet.

## 2. Waterfall title follows the toggle

Two FIXED fields and three text helpers:
```
// WF FTE Hires
ZN({ FIXED : SUM(IF [In Range] AND [Movement Category] = "Hires" THEN [Fte] END) })
```
```
// WF FTE Leavers
ZN({ FIXED : -SUM(IF [In Range] AND ([Movement Category] = "Voluntary Terminations" OR [Movement Category] = "Involuntary Terminations") THEN [Fte] END) })
```
`WF FTE Hires Str` and `WF FTE Leavers Str`: the comma pattern on `ROUND([WF FTE Hires], 0)` and `ROUND([WF FTE Leavers], 0)`, wrapped in `INT(...)`. Then the signed net:
```
// WF FTE Net Str
IF ROUND([WF FTE Close] - [WF FTE Open], 0) < 0 THEN "−" ELSE "+" END +
STR(INT(ABS(ROUND([WF FTE Close] - [WF FTE Open], 0))))
```
Replace `WF Title` (the middle branch is your existing text, unchanged):
```
// WF Title
IF NOT [K Valid] THEN "Choose a start month on or before the end month"
ELSEIF [Measure] = "Headcount" THEN
     [WF Period] + ": " + [WF Hires Str] + " hires " +
     IF [WF Hires] >= [WF Leavers] THEN "outpaced " ELSE "fell short of " END +
     [WF Leavers Str] + " leavers, " +
     IF [WF Close] >= [WF Open] THEN "adding " ELSE "removing " END +
     [WF Net Str] + " people"
ELSE [WF Period] + " in FTE: " + [WF FTE Hires Str] + " FTE hired, " + [WF FTE Leavers Str] +
     " FTE left, " + [WF FTE Net Str] + " FTE net"
END
```
And make a single month read naturally. Replace `WF Period` so a one-month range says "Jul 2025" instead of "Jul 2025 – Jul 2025":
```
// WF Period
IF [Start Month] = [End Month]
THEN LEFT(DATENAME('month', [Start Month]), 3) + " " + STR(YEAR([Start Month]))
ELSEIF DATEDIFF('month', [Start Month], [End Month]) = 11
THEN "FY" + RIGHT(STR(YEAR([End Month]) + IF MONTH([End Month]) >= 7 THEN 1 ELSE 0 END), 2)
ELSE LEFT(DATENAME('month', [Start Month]), 3) + " " + STR(YEAR([Start Month])) + " – " +
     LEFT(DATENAME('month', [End Month]), 3) + " " + STR(YEAR([End Month]))
END
```

## 3. Tooltip: bridge people to FTE on every bar

Add two helpers and **replace** `TT Part Time` from the tooltip guide with the version below. Opening and Closing keep their part-time line; the movement bars now get the bridge.

```
// TT Bar T   (this bar's FTE in tenths, always positive)
INT(ROUND(ABS(SUM(IF [In Range] THEN [Fte] END)) * 10, 0))
```
```
// TT Bar HC
ABS(SUM(IF [In Range] THEN [Headcount] END))
```
```
// TT Part Time   (replaces the earlier version)
IF ATTR([Movement Category]) = "Opening" OR ATTR([Movement Category]) = "Closing" THEN
  IF [TT Level HC] = 0 THEN "" ELSE
    (IF [TT Level PT] >= 1000
     THEN STR(DIV(INT([TT Level PT]), 1000)) + "," + RIGHT("00" + STR(INT([TT Level PT]) % 1000), 3)
     ELSE STR(INT([TT Level PT])) END)
    + " part-time (" +
    STR(DIV(INT(ROUND([TT Level PT] / [TT Level HC] * 1000, 0)), 10)) + "." +
    STR(INT(ROUND([TT Level PT] / [TT Level HC] * 1000, 0)) % 10) + "%) · FTE is " +
    STR(DIV(INT(ROUND(([TT Level HC] - [TT Level FTE]) * 10, 0)), 10)) + "." +
    STR(INT(ROUND(([TT Level HC] - [TT Level FTE]) * 10, 0)) % 10) + " below headcount"
  END
ELSEIF [TT Bar HC] = 0 THEN ""
ELSE
  (IF [TT Bar HC] >= 1000
   THEN STR(DIV(INT([TT Bar HC]), 1000)) + "," + RIGHT("00" + STR(INT([TT Bar HC]) % 1000), 3)
   ELSE STR(INT([TT Bar HC])) END)
  + " people = " +
  (IF [TT Bar T] >= 10000
   THEN STR(DIV([TT Bar T], 10000)) + "," + RIGHT("00" + STR(DIV([TT Bar T], 10) % 1000), 3)
   ELSE STR(DIV([TT Bar T], 10)) END)
  + "." + STR([TT Bar T] % 10) + " FTE (part-timers count as a fraction)"
END
```
The tooltip's fourth line already points at `TT Part Time`, so nothing else changes on the sheet.

## 4. Make the toggle capsule visible

In your screenshot the pill shows but the dark capsule behind it does not, because the sheet colour matches the header band. Set it so the two segments read as one control:
1. Measure Toggle sheet: Format → Shading → Worksheet and Pane `#243A57`.
2. Dashboard: select the Measure Toggle object → Layout pane → Background `#243A57`, Corner Radius 16 on all four corners.

## 5. Period picker

### 5.1 Same month is valid, and it is not "beginning equals close"

A walk always starts at the **end of the month before** the first month. So Start Jul 2025 and End Jul 2025 is the one-month walk of July: opening is 30 Jun (12,510), closing is 31 Jul (12,572), and the card correctly says +0.5%. The labels are what misled; "Start Jul / End Jul" sounds like a single point in time. Relabel the controls as a range:
- `Start Month` → Properties → Display format → Custom → `"From "mmm yyyy`
- `End Month` → `"To "mmm yyyy`

"From Jul 2025 To Jul 2025" reads as one whole month. (With the `WF Period` change above, the title says "Jul 2025".)

### 5.2 End before start: fix in Tableau, not in the data

Nothing in the data can stop a viewer picking a reversed pair; the choice happens in the control. Tableau cannot filter one dropdown by another, so the dependable fix is to **swap the pair automatically**: picking May 2026 to Aug 2025 simply shows Aug 2025 to May 2026, and the title states the period. The red "—" state disappears.

1. Right-click parameter **Start Month** → **Duplicate** and rename the copy `From (pick)`. Same for **End Month**, copy named `To (pick)`.
2. Create:
   ```
   // Range Start
   MIN([From (pick)], [To (pick)])
   ```
   ```
   // Range End
   MAX([From (pick)], [To (pick)])
   ```
3. Right-click the **original** `Start Month` parameter → **Replace References…** → choose `Range Start`. Original `End Month` → `Range End`. Tableau rewrites every field that used them (about 18: `In Range`, `Walk Value`, `K Open HC`, the `WF …` and `TT …` fields) in one go.
4. On the dashboard: **Show Parameter** for `From (pick)` and `To (pick)`, put them in the same boxes (x 840 and 996, y 22, 146 × 32, Corner Radius 0, Background white), apply the display formats from 5.1 to these two, then delete the old controls.
5. Then `K Valid` is always true, so the "Choose a start month…" message can never appear. Leave the field in place; it costs nothing.

If you do not see **Replace References** on a parameter in your version, tell me and I will give you the field-by-field edit list instead.

## 6. Check (Jul to Aug 2025)

| Item | Measure = Headcount | Measure = FTE |
|---|---|---|
| Waterfall title | Jul 2025 – Aug 2025: 381 hires outpaced 270 leavers, adding 111 people | Jul 2025 – Aug 2025 in FTE: 377 FTE hired, 265 FTE left, +107 FTE net |
| Card 3 | **Hires** 381, "18.2% annualized · 377 FTE" | **Hires (FTE)** 377, "381 people · 18.2% annualized" |
| Card 4 note | 226 left by choice · 221 FTE | 221 FTE left by choice · 226 people |
| Waterfall bars | +381, −226, −44 | +377, −221, −43, FTE changes −5 |
| Hires tooltip | 381 people = 376.9 FTE (part-timers count as a fraction) | same line |
| Cards 1 and 2 | 12,621 and 12,388.5 (always both) | same |

Pick From Jul 2025 To Jul 2025: title "Jul 2025: …", opening 12,510, closing 12,572. Pick From May 2026 To Aug 2025: the page shows Aug 2025 to May 2026 with no dashes.
