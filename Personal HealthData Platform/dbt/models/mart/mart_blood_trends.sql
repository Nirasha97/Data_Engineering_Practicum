
-- Monthly blood test trends per patient
SELECT
    customer_id,
    DATE_TRUNC('month', report_date)             AS month,
    COUNT(*)                                     AS reports_count,
    ROUND(AVG(glucose)::numeric,          2)     AS avg_glucose,
    ROUND(AVG(hemoglobin)::numeric,       2)     AS avg_hemoglobin,
    ROUND(AVG(cholesterol_total)::numeric, 2)    AS avg_cholesterol,
    ROUND(AVG(triglycerides)::numeric,    2)     AS avg_triglycerides,
    SUM(CASE WHEN glucose > 126           THEN 1 ELSE 0 END) AS abnormal_glucose,
    SUM(CASE WHEN cholesterol_total > 200 THEN 1 ELSE 0 END) AS abnormal_cholesterol
FROM {{ ref('stg_blood_reports') }}
GROUP BY customer_id, DATE_TRUNC('month', report_date)
ORDER BY customer_id, month
