-- stg_candidate_stage_event
-- The stages each candidate reached, in order: Applied, Screen, Interview, Offer, then
-- an outcome (Accepted, Declined, Rejected, Withdrawn). A seat refilled immediately
-- (succession, a team handed to a new manager) has only Offer and Accepted.
CREATE OR REPLACE TABLE staging.stg_candidate_stage_event AS
SELECT
    candidate_event_id,
    candidate_id,
    stage,
    CAST(stage_order AS INTEGER)                             AS stage_order,
    CAST(stage_date AS DATE)                                 AS stage_date
FROM raw.fact_candidate_stage_event;
