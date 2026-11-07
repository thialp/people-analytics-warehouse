-- Release 7 "at work on" calendar: on every weekday, for every leader and worker type, people at work
-- plus people off equals the people in the team, and the three reasons add up to the people off.
SELECT leader_id, worker_type, day, people, at_work, off, off_time_off, off_leave, off_public_holiday
FROM marts.mart_leader_availability
WHERE (NOT is_weekend AND at_work + off <> people)
   OR off_time_off + off_leave + off_public_holiday <> off
   OR (is_weekend AND at_work IS NOT NULL)
