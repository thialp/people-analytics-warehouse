"""
Settings for the PID fill forecast (release 5, Dashboard #5, Seats to Fill).

Every number the method depends on lives here, so a reviewer can read the assumptions in one
place. Arcadia Systems is fictional; all data is synthetic.
"""

from __future__ import annotations

SEED = 20260630                 # one seed for the whole forecast; each origin draws its own stream from it
DRAWS = 100                     # simulated futures per forecast: the page shows their average and the range P10 to P90

# Time to fill is modelled in 10-day periods after approval, so 30, 60 and 90 days fall on a
# period boundary and the survival curve reads them exactly.
PERIOD_DAYS = 10
OBSERVED_PERIODS = 21           # 210 days: an approved requisition still open after that is cancelled
SIM_PERIODS = 40                # 400 days: how far a simulated requisition is followed (none is left open)

# The waiting-time baseline: each bin of periods has its own fill chance (the hazard's shape).
PERIOD_BINS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 15]            # bin starts; the last runs to the end

LEVEL_BANDS = {1: "L1-L2", 2: "L1-L2", 3: "L3-L4", 4: "L3-L4", 5: "L5-L6", 6: "L5-L6"}
LEVEL_BAND_LEADER = "L7+"
LEVEL_BAND_ORDER = ["L1-L2", "L3-L4", "L5-L6", "L7+"]
GRADUATE_BAND = "L1-L2"         # graduate hiring: the model learns a month effect per country for this band only

RIDGE = 2.0                     # L2 penalty on every coefficient except the waiting-time baseline
IRLS_ITERATIONS = 30
COEF_DECIMALS = 6               # coefficients are rounded before simulating, so runs reproduce byte for byte

# Demand
RATE_QUARTERS = 8               # backfill rates per head come from the last eight quarters before the origin
MIX_QUARTERS = 8                # level-band mix and office shares: the last eight quarters

# Backtest: origins at the eight quarter-ends before the last one; each forecasts the quarters its
# known plan versions cover (up to four), using only what was known on the origin date.
BACKTEST_ORIGINS = 8
BACKTEST_DRAWS = 100
RANGE_Z = 1.2816                # the backtest range on the page: mean ± this many standard deviations (an 80% normal range)

EXCLUDED_DEPARTMENT = "D-901"   # executive officers, excluded from every Arcadia dashboard
