-- stg_candidate
-- One row per applicant to one requisition (applicant tracking). The hire is the
-- Accepted candidate, linked to the worker they became (or already were, for an
-- internal move). Applicants who were not hired carry no worker_id.
-- final_status: Accepted, Declined (turned an offer down), Rejected, Withdrawn, or
-- In process (requisition still open at the last month-end).
CREATE OR REPLACE TABLE staging.stg_candidate AS
SELECT
    candidate_id,
    requisition_id,
    CAST(is_internal AS BOOLEAN)                             AS is_internal,
    candidate_source,
    NULLIF(worker_id, '')                                    AS worker_id,
    final_status
FROM raw.dim_candidate;
