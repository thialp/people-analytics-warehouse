# Headcount & FTE Walk: cards that match the waterfall, and a clearer period picker

Two problems from your screenshots, two fixes. **No data change is needed**: the walk file already carries both headcount and FTE on every line (and the new `part_time_headcount` column is in the CSV I sent). Load that CSV once and do everything below in Tableau.

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
Four text helpers. Each one must return **text** (the `STR(...)` around every branch is what makes it text; a branch without it returns a number and breaks anything that adds it to a string):
```
// K Hires HC Str
IF [K Hires] >= 1000
THEN STR(DIV(INT([K Hires]), 1000)) + "," + RIGHT("00" + STR(INT([K Hires]) % 1000), 3)
ELSE STR(INT([K Hires])) END
```
```
// K Hires FTE Str
IF ROUND([K Hires FTE], 0) >= 1000
THEN STR(DIV(INT(ROUND([K Hires FTE], 0)), 1000)) + "," + RIGHT("00" + STR(INT(ROUND([K Hires FTE], 0)) % 1000), 3)
ELSE STR(INT(ROUND([K Hires FTE], 0))) END
```
```
// K Vol HC Str
IF [K Leavers Vol] >= 1000
THEN STR(DIV(INT([K Leavers Vol]), 1000)) + "," + RIGHT("00" + STR(INT([K Leavers Vol]) % 1000), 3)
ELSE STR(INT([K Leavers Vol])) END
```
```
// K Vol FTE Str
IF ROUND([K Leavers Vol FTE], 0) >= 1000
THEN STR(DIV(INT(ROUND([K Leavers Vol FTE], 0)), 1000)) + "," + RIGHT("00" + STR(INT(ROUND([K Leavers Vol FTE], 0)) % 1000), 3)
ELSE STR(INT(ROUND([K Leavers Vol FTE], 0))) END
```

The hire rate as text:
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

Two FIXED fields and three text helpers (all written out below):
```
// WF FTE Hires
ZN({ FIXED : SUM(IF [In Range] AND [Movement Category] = "Hires" THEN [Fte] END) })
```
```
// WF FTE Leavers
ZN({ FIXED : -SUM(IF [In Range] AND ([Movement Category] = "Voluntary Terminations" OR [Movement Category] = "Involuntary Terminations") THEN [Fte] END) })
```
Two text helpers (both must return **text**: if Tableau says "Can't add string and float values" on `WF Title`, one of these is returning a number, usually a branch missing its `STR(...)`):
```
// WF FTE Hires Str
IF ROUND([WF FTE Hires], 0) >= 1000
THEN STR(DIV(INT(ROUND([WF FTE Hires], 0)), 1000)) + "," + RIGHT("00" + STR(INT(ROUND([WF FTE Hires], 0)) % 1000), 3)
ELSE STR(INT(ROUND([WF FTE Hires], 0))) END
```
```
// WF FTE Leavers Str
IF ROUND([WF FTE Leavers], 0) >= 1000
THEN STR(DIV(INT(ROUND([WF FTE Leavers], 0)), 1000)) + "," + RIGHT("00" + STR(INT(ROUND([WF FTE Leavers], 0)) % 1000), 3)
ELSE STR(INT(ROUND([WF FTE Leavers], 0))) END
```
Then the signed net:
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

## 5. Period dropdowns

### 5.1 Same month is valid, and it is not "beginning equals close"

A walk always starts at the **end of the month before** the first month. So Start Jul 2025 and End Jul 2025 is the one-month walk of July: opening is 30 Jun (12,510), closing is 31 Jul (12,572), and the card correctly says +0.5%. The labels are what misled; "Start Jul / End Jul" sounds like a single point in time. Relabel the controls as a range:
- `Start Month` → Properties → Display format → Custom → `"From "mmm yyyy`
- `End Month` → `"To "mmm yyyy`

"From Jul 2025 To Jul 2025" reads as one whole month. (With the `WF Period` change above, the title says "Jul 2025".)

### 5.2 End before start

Tableau cannot limit one parameter by another (a dropdown's list is fixed, **Replace References** only swaps a parameter for another parameter, and a chart-driven picker was tried and dropped as less intuitive than two dropdowns). So the controls stay as two plain dropdowns and a reversed pair is handled, not prevented: the cards show "—" and the waterfall title reads "Choose a start month on or before the end month". Nothing breaks, and the message says what to do.

**Clean up what we tried:** delete the parameters `From (pick)` and `To (pick)`, the calculated fields `Range Start` and `Range End`, and, if you added them, the two Change Parameter actions *Pick start* and *Pick end* (Dashboard → Actions → select each → Delete). Keep the original `Start Month` and `End Month`; every formula already uses them.

## 6. Check (Jul to Aug 2025)

| Item | Measure = Headcount | Measure = FTE |
|---|---|---|
| Waterfall title | Jul 2025 – Aug 2025: 381 hires outpaced 270 leavers, adding 111 people | Jul 2025 – Aug 2025 in FTE: 377 FTE hired, 265 FTE left, +107 FTE net |
| Card 3 | **Hires** 381, "18.2% annualized · 377 FTE" | **Hires (FTE)** 377, "381 people · 18.2% annualized" |
| Card 4 note | 226 left by choice · 221 FTE | 221 FTE left by choice · 226 people |
| Waterfall bars | +381, −226, −44 | +377, −221, −43, FTE changes −5 |
| Hires tooltip | 381 people = 376.9 FTE (part-timers count as a fraction) | same line |
| Cards 1 and 2 | 12,621 and 12,388.5 (always both) | same |

Pick From Jul 2025 To Jul 2025: title "Jul 2025: …", opening 12,510, closing 12,572. Reversed pair (From May 2026, To Aug 2025): cards show "—" and the title asks for a start on or before the end.
