-- Every worker appears once in the worker dimension.
SELECT worker_id, COUNT(*) AS rows_found
FROM staging.stg_worker
GROUP BY worker_id
HAVING COUNT(*) > 1
