"""Export the FY26 numbers the map preview draws from the warehouse into build/data.json."""
import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[3]
con = duckdb.connect(str(ROOT / "warehouse" / "arcadia.duckdb"), read_only=True)
FY = con.execute("SELECT MAX(fiscal_year) FROM marts.mart_dim_month").fetchone()[0]


def rows(sql, params=()):
    cur = con.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return [{k: (float(v) if v is not None and not isinstance(v, (int, float, str, bool)) else v)
             for k, v in zip(cols, r)} for r in cur.fetchall()]


offices = rows("""
    SELECT d.location_id, d.city, d.country_name, d.region, d.site_type,
           d.latitude::DOUBLE AS lat, d.longitude::DOUBLE AS lon,
           SUM(opening_headcount) FILTER (WHERE m.fiscal_month = 1)  AS opening,
           SUM(closing_headcount) FILTER (WHERE m.fiscal_month = 12) AS closing
    FROM marts.mart_location_headcount AS l
    JOIN marts.mart_dim_location AS d USING (location_id)
    JOIN marts.mart_dim_month AS m USING (month_end_date)
    WHERE m.fiscal_year = ? GROUP BY ALL ORDER BY closing DESC""", [FY])
for o in offices:
    o["growth"] = (o["closing"] - o["opening"]) / o["opening"]
flows = rows("""
    SELECT from_city, to_city, from_latitude::DOUBLE AS flat, from_longitude::DOUBLE AS flon,
           to_latitude::DOUBLE AS tlat, to_longitude::DOUBLE AS tlon, flow_scope, SUM(workers) AS workers
    FROM marts.mart_mobility_flows JOIN marts.mart_dim_month USING (month_end_date)
    WHERE fiscal_year = ? AND has_coordinates GROUP BY ALL""", [FY])
region = rows("""
    SELECT d.region,
           SUM(opening_headcount) FILTER (WHERE m.fiscal_month = 1)  AS fy25,
           SUM(closing_headcount) FILTER (WHERE m.fiscal_month = 12) AS fy26
    FROM marts.mart_location_headcount JOIN marts.mart_dim_location AS d USING (location_id)
    JOIN marts.mart_dim_month AS m USING (month_end_date)
    WHERE m.fiscal_year = ? GROUP BY 1""", [FY])
tot = rows("""
    SELECT SUM(workers) AS rel, SUM(workers) FILTER (WHERE flow_scope = 'International') AS intl
    FROM marts.mart_mobility_flows JOIN marts.mart_dim_month USING (month_end_date) WHERE fiscal_year = ?""", [FY])[0]
out = Path(__file__).with_name("data.json")
out.write_text(json.dumps({"offices": offices, "flows": flows, "region": region, "tot": tot}, indent=1))
print(f"Wrote {out.name}: {len(offices)} offices, {len(flows)} flows")
