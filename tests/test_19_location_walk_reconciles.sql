-- Every office reconciles every month:
-- opening + hires - leavers + relocations in - relocations out = closing.
SELECT *
FROM marts.mart_location_headcount
WHERE opening_headcount + hires - voluntary_terminations - involuntary_terminations
      + relocations_in - relocations_out <> closing_headcount
