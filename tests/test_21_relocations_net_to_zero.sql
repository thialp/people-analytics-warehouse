-- Relocations move people between offices, never in or out of the company:
-- each month, total relocations in must equal total relocations out.
SELECT month_end_date, SUM(relocations_in) AS rel_in, SUM(relocations_out) AS rel_out
FROM marts.mart_location_headcount
GROUP BY 1
HAVING SUM(relocations_in) <> SUM(relocations_out)
