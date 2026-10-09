-- Offices: valid coordinates, a real postal code everywhere except the UAE (which has
-- no postal codes), and nobody based in an office before it opened.
SELECT location_id, NULL AS month_end_date, NULL AS worker_id, 'bad coordinates or postal code' AS issue
FROM staging.stg_location
WHERE latitude IS NULL OR longitude IS NULL
   OR latitude NOT BETWEEN -90 AND 90 OR longitude NOT BETWEEN -180 AND 180
   OR (postal_code IS NULL AND country_code <> 'AE')
UNION ALL
SELECT s.location_id, s.month_end_date, s.worker_id, 'worker in an office before it opened'
FROM intermediate.int_worker_month_end_snapshot AS s
JOIN staging.stg_location AS l USING (location_id)
WHERE s.month_end_date < l.opened_date
