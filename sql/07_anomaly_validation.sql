--Testing injected anomaly

WITH expected(reference_number, rule_code) AS (

    VALUES

    ('SYN0925269217', 'REC002'),
    ('SYN0925269217', 'REC011'),

    ('SYN2996964807', 'REC003'),

    ('SYN2833048818', 'REC004'),
    ('SYN2833048818', 'REC006'),

    ('SYN2982542250', 'REC005'),
    ('SYN2982542250', 'REC006'),

    ('SYN4233987521', 'REC007'),

    ('SYN9861874534', 'REC008'),

    ('SYN6600563652', 'REC009'),

    ('SYN7442536711', 'REC010'),
    ('SYN7442536711', 'REC012'),

    ('SYN9683821477', 'REC013'),
    ('SYN9683821477', 'REC014'),
    ('SYN9683821477', 'REC015'),

    ('SYN9503258174', 'REC016'),

    ('DUP8864459314', 'REC017'),

    ('SYN6586897743', 'REC018'),

    ('SYN0007357923', 'REC019'),

    ('SYN2566080170', 'REC020'),

    ('SYN5343727126', 'REC021'),

    ('SYN2590045896', 'REC022'),

    ('SYN8332718480', 'REC023'),
    ('SYN8332718480', 'REC024'),

    ('SYN5413361017', 'REC024'),

    ('ORPH1777102663', 'REC001')
),

actual AS (

    SELECT DISTINCT
        reference_number,
        rule_code

    FROM core.detected_reconciliation_rules

    WHERE reference_number IN (
        'SYN0925269217',
        'SYN2996964807',
        'SYN2833048818',
        'SYN2982542250',
        'SYN4233987521',
        'SYN9861874534',
        'SYN6600563652',
        'SYN7442536711',
        'SYN9683821477',
        'SYN9503258174',
        'DUP8864459314',
        'SYN6586897743',
        'SYN0007357923',
        'SYN2566080170',
        'SYN5343727126',
        'SYN2590045896',
        'SYN8332718480',
        'SYN5413361017',
        'ORPH1777102663'
    )
),

comparison AS (

    SELECT
        COALESCE(
            expected.reference_number,
            actual.reference_number
        ) AS reference_number,

        COALESCE(
            expected.rule_code,
            actual.rule_code
        ) AS rule_code,

        CASE
            WHEN expected.rule_code IS NOT NULL
             AND actual.rule_code IS NOT NULL
                THEN 'PASS'

            WHEN expected.rule_code IS NOT NULL
             AND actual.rule_code IS NULL
                THEN 'MISSED_RULE'

            WHEN expected.rule_code IS NULL
             AND actual.rule_code IS NOT NULL
                THEN 'FALSE_POSITIVE'
        END AS test_result

    FROM expected

    FULL OUTER JOIN actual
        ON expected.reference_number = actual.reference_number
       AND expected.rule_code = actual.rule_code
)

SELECT
    test_result,
    COUNT(*) AS rule_count
FROM comparison
GROUP BY test_result
ORDER BY test_result;