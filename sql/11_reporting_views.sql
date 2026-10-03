-- =========================================================
-- REPORTING VIEWS
-- Reusable datasets for Excel and Power BI
-- =========================================================


-- 1. OVERALL EXCEPTION KPI SUMMARY
CREATE OR REPLACE VIEW core.exception_kpi_summary AS
SELECT 
    COUNT(*) AS total_exceptions,
    COUNT(*) FILTER ( WHERE status = 'OPEN' ) AS open_exceptions,
    COUNT(*) FILTER ( WHERE status = 'IN_PROGRESS') AS in_progress_exceptions,
    COUNT(*) FILTER ( WHERE status = 'RESOLVED') AS resolved_exceptions,
    COUNT(*) FILTER ( WHERE severity = 'CRITICAL') AS critical_exceptions,
    COUNT(*) FILTER ( WHERE severity = 'HIGH') AS high_exceptions,
    COUNT(*) FILTER ( WHERE severity = 'MEDIUM') AS medium_exceptions
FROM core.reconciliation_exceptions;



-- 2. EXCEPTIONS BY RULE
CREATE OR REPLACE VIEW core.exception_rule_summary AS
SELECT e.rule_code, r.rule_name, r.category, e.severity, COUNT(*) AS exception_count
FROM core.reconciliation_exceptions e
JOIN core.reconciliation_rules r
    ON e.rule_code = r.rule_code
GROUP BY e.rule_code, r.rule_name, r.category, e.severity;



-- 3. EXCEPTIONS BY CATEGORY
CREATE OR REPLACE VIEW core.exception_category_summary AS
SELECT r.category, COUNT(*) AS exception_count
FROM core.reconciliation_exceptions e
JOIN core.reconciliation_rules r
    ON e.rule_code = r.rule_code
GROUP BY r.category;



-- 4. UNRESOLVED EXCEPTION AGING
CREATE OR REPLACE VIEW core.exception_aging_summary AS
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
SELECT aging_bucket, sort_order, COUNT(*) AS exception_count
FROM exception_aging
GROUP BY aging_bucket, sort_order;



-- 5. EXCEPTION LIFECYCLE MOVEMENT
CREATE OR REPLACE VIEW core.exception_lifecycle_summary AS
SELECT old_status, new_status, COUNT(*) AS transition_count
FROM core.exception_status_history
GROUP BY old_status, new_status;



-- 6. CURRENT DATA QUALITY SUMMARY
CREATE OR REPLACE VIEW core.dq_current_summary AS
SELECT check_code, check_name, quality_dimension, target_table, result_status, checked_row_count, failure_count,
    ROUND(
        failure_count * 100.0
        / NULLIF(checked_row_count, 0),
        2
    ) AS failure_rate_percent
FROM core.data_quality_summary;



-- 7. DATA QUALITY RUN TREND
CREATE OR REPLACE VIEW core.dq_run_trend AS
SELECT r.run_id, r.started_at, r.completed_at, r.run_status,
    COUNT(*) FILTER ( WHERE d.result_status = 'PASS') AS passed_checks,
    COUNT(*) FILTER ( WHERE d.result_status = 'FAIL') AS failed_checks,
    COUNT(*) FILTER ( WHERE d.result_status = 'ERROR') AS error_checks,
    SUM(d.failure_count) AS total_failures
FROM core.data_quality_runs r
JOIN core.data_quality_results d
    ON r.run_id = d.run_id
GROUP BY r.run_id, r.started_at, r.completed_at, r.run_status;

