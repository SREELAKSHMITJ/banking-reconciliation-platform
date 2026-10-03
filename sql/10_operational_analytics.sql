-- Operational Analytics

-- What is the overall exception situation right now?
SELECT 
    COUNT(*) AS total_exceptions,
    COUNT(*) FILTER ( WHERE status = 'OPEN') AS open_exceptions,
    COUNT(*) FILTER ( WHERE status = 'IN_PROGRESS') AS in_progress_exceptions,
    COUNT(*) FILTER ( WHERE status = 'RESOLVED') AS resolved_exceptions,
    COUNT(*) FILTER ( WHERE severity = 'CRITICAL') AS critical_exceptions,
    COUNT(*) FILTER ( WHERE severity = 'HIGH') AS high_exceptions
FROM core.reconciliation_exceptions;


-- Exceptions by status and severity

-- How are exceptions distributed across lifecycle status and severity?
SELECT status, severity, COUNT(*) AS exception_count
FROM core.reconciliation_exceptions
GROUP BY status, severity
ORDER BY status, severity;

-- Which reconciliation rules are causing the most exceptions
SELECT e.rule_code, r.rule_name, r.category, e.severity, COUNT(*) AS exception_count
FROM core.reconciliation_exceptions e
JOIN core.reconciliation_rules r
    ON e.rule_code = r.rule_code
GROUP BY e.rule_code, r.rule_name, r.category, e.severity
ORDER BY exception_count DESC, e.rule_code;

-- group exceptions by category -> Which type of reconciliation problem is most common overall?
SELECT r.category, COUNT(*) AS exception_count
FROM core.reconciliation_exceptions e
JOIN core.reconciliation_rules r
    ON e.rule_code = r.rule_code
GROUP BY r.category
ORDER BY exception_count DESC;

-- How old are our unresolved exceptions
WITH exception_aging AS (
    SELECT
        CASE
            WHEN CURRENT_TIMESTAMP - detected_at < INTERVAL '1 day'
                THEN '< 1 Day'
            WHEN CURRENT_TIMESTAMP - detected_at < INTERVAL '3 days'
                THEN '1 - 3 Days'
            WHEN CURRENT_TIMESTAMP - detected_at < INTERVAL '7 days'
                THEN '3 - 7 Days'
            ELSE '7+ Days'
        END AS aging_bucket,

        CASE
            WHEN CURRENT_TIMESTAMP - detected_at < INTERVAL '1 day'
                THEN 1
            WHEN CURRENT_TIMESTAMP - detected_at < INTERVAL '3 days'
                THEN 2
            WHEN CURRENT_TIMESTAMP - detected_at < INTERVAL '7 days'
                THEN 3
            ELSE 4
        END AS sort_order

    FROM core.reconciliation_exceptions
    WHERE status <> 'RESOLVED'
)

SELECT aging_bucket, COUNT(*) AS exception_count
FROM exception_aging
GROUP BY aging_bucket, sort_order
ORDER BY sort_order;


-- How are exceptions moving through their lifecycle
SELECT old_status, new_status, COUNT(*) AS transition_count
FROM core.exception_status_history
GROUP BY old_status, new_status
ORDER BY transition_count DESC;


-- Which DQ checks are currently passing or failing, and how many records are affected?
SELECT check_code, check_name, quality_dimension, target_table, result_status,
    checked_row_count, failure_count
FROM core.data_quality_summary
ORDER BY
    CASE result_status
        WHEN 'FAIL' THEN 1
        WHEN 'PASS' THEN 2
    END,
    failure_count DESC,
    check_code;



-- How has data quality changed from run to run?
-- failed_checks -> How many of the 20 rules failed?
-- SUM(d.failure_count) -> How many failure detections occurred across those rules?
SELECT r.run_id, r.started_at, r.completed_at, r.run_status, COUNT(*) FILTER (
        WHERE d.result_status = 'PASS'
    ) AS passed_checks,
    COUNT(*) FILTER (
        WHERE d.result_status = 'FAIL'
    ) AS failed_checks,
    SUM(d.failure_count) AS total_failures
FROM core.data_quality_runs r
JOIN core.data_quality_results d
    ON r.run_id = d.run_id
GROUP BY r.run_id, r.started_at, r.completed_at, r.run_status
ORDER BY r.run_id;






-- WITH exception_aging AS ( ... ) -> CTE: Common Table Expression
-- Create a temporary named result that exists only for this SQL query
-- It does not create a permanent PostgreSQL table