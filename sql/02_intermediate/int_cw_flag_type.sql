-- int_cw_flag_type
-- Grain: one row per reconciliation flag (F01 to F09).
--
-- A flag is a comparison between the two systems that puts Finance's month-end report at risk:
-- what Keystone shows against what Bridgeway (or the PID ledger) has. The words describe a
-- mismatch, not a fault: the page helps people find what to align, it does not blame a team.
--
-- Each flag belongs to one of five risks and is fixed by default in one of three places. The
-- numbers and names are chosen so that all three columns of the Sankey read in alphabetical order:
-- the Sankey extension orders the first column by its sort and every later column by first
-- appearance in that order, so the flags are numbered in risk order (risks A to S) and the first
-- risk reaches Bridgeway before Keystone and Keystone before the system feed, at every close.
--
--   risk (risk_order)               flags
--   Active headcount mismatch (1)   F01 One person, two IDs; F02 Bridgeway ID missing or different;
--                                   F03 In Bridgeway, not in Keystone
--   Billing after the end date (2)  F04 Order open or billed after the end date
--   Cost center mismatch (3)        F05 Cost center differs
--   PID mismatch (4)                F06 PID still filled after the end date; F07 Two active PID records
--   Status mismatch (5)             F08 Working in Bridgeway, ended in Keystone;
--                                   F09 Active in Keystone, not working in Bridgeway
--
-- The routing rule in int_cw_flag sends feed and load problems to the system feed instead of the
-- default place.
CREATE OR REPLACE TABLE intermediate.int_cw_flag_type AS
SELECT t.*, LPAD(SUBSTR(t.flag_code, 2), 2, '0') || ' ' || t.flag_name AS flag_label
FROM (VALUES
    ('F01', 'One person, two IDs',                          'Active headcount mismatch',  1, 'Bridgeway',
     'Merge the two Bridgeway IDs'),
    ('F02', 'Bridgeway ID missing or different',            'Active headcount mismatch',  1, 'Keystone',
     'Align the Bridgeway ID stored in Keystone'),
    ('F03', 'In Bridgeway, not in Keystone',                'Active headcount mismatch',  1, 'Keystone',
     'Create the contractor in Keystone'),
    ('F04', 'Order open or billed after the end date',      'Billing after the end date', 2, 'Bridgeway',
     'Close the order in Bridgeway; request a credit for time billed after the end'),
    ('F05', 'Cost center differs',                          'Cost center mismatch',       3, 'Bridgeway',
     'Confirm the cost center with the manager; align the Bridgeway order or Keystone'),
    ('F06', 'PID still filled after the end date',          'PID mismatch',               4, 'Keystone',
     'End the job record and release the PID in Keystone'),
    ('F07', 'Two active PID records',                       'PID mismatch',               4, 'Keystone',
     'End the older job record in Keystone'),
    ('F08', 'Working in Bridgeway, ended in Keystone',      'Status mismatch',            5, 'Keystone',
     'Reactivate the contractor in Keystone'),
    ('F09', 'Active in Keystone, not working in Bridgeway', 'Status mismatch',            5, 'Keystone',
     'Confirm with the manager; inactivate in Keystone or raise a Bridgeway order')
) AS t(flag_code, flag_name, risk, risk_order, default_place, next_step);
