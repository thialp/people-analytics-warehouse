-- int_cw_flag_type
-- Grain: one row per reconciliation flag (F01 to F12).
--
-- A flag is a comparison between the two systems that puts Finance's month-end report at risk:
-- what Keystone shows against what Bridgeway (or the PID ledger) has. Each creates one of six
-- risks, in a fixed order, and is fixed by default in one place: Bridgeway for the cost center,
-- billing and duplicate-ID flags (F01 to F05), Keystone for the rest. The routing rule in
-- int_cw_flag sends timing and load problems to Integration instead.
--
-- F01 and F02 split a wrong cost center by how far it moves the cost: into another function, or
-- into another department of the same function (every cost center change in the data crosses a
-- department, within one country).
CREATE OR REPLACE TABLE intermediate.int_cw_flag_type AS
SELECT * FROM (VALUES
    ('F01', 'Function different',                          'Wrong cost center',    1, 'Bridgeway',
     'Confirm the cost center with the manager; correct the Bridgeway order or Keystone'),
    ('F02', 'Department different, same function',         'Wrong cost center',    1, 'Bridgeway',
     'Confirm the cost center with the manager; correct the Bridgeway order or Keystone'),
    ('F03', 'Order open after the end date',               'Paying after the end', 2, 'Bridgeway',
     'Close the order in Bridgeway'),
    ('F04', 'Billed after the end date',                   'Paying after the end', 2, 'Bridgeway',
     'Request a credit from the supplier'),
    ('F05', 'One person, two IDs',                         'Wrong headcount',      3, 'Bridgeway',
     'Merge the two Bridgeway IDs'),
    ('F06', 'Bridgeway ID missing or wrong',               'Wrong headcount',      3, 'Keystone',
     'Repair the Bridgeway ID stored in Keystone'),
    ('F07', 'One person, two active PID records',          'Wrong PID',            4, 'Keystone',
     'End the old job record in Keystone'),
    ('F08', 'PID still filled after the contract ended',   'Wrong PID',            4, 'Keystone',
     'End the job record and release the PID in Keystone'),
    ('F09', 'Ended in Bridgeway, still active in Keystone', 'Access kept',         5, 'Keystone',
     'Inactivate the contractor in Keystone and remove access'),
    ('F10', 'In Keystone only',                            'Access kept',          5, 'Keystone',
     'Confirm with the manager; inactivate in Keystone or raise a Bridgeway order'),
    ('F11', 'Working in Bridgeway, ended in Keystone',     'Access lost',          6, 'Keystone',
     'Reactivate the contractor in Keystone'),
    ('F12', 'In Bridgeway, missing in Keystone',           'Access lost',          6, 'Keystone',
     'Create the contractor in Keystone')
) AS t(flag_code, flag_name, risk, risk_order, default_place, next_step);
