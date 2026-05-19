
-- Join patients with blood report averages + abnormal flags
SELECT
    p.customer_id,
    p.name,
    p.age,
    p.gender,
    p.blood_type,
    p.city,
    COUNT(b.report_id)                           AS total_reports,
    ROUND(AVG(b.glucose)::numeric,        2)     AS avg_glucose,
    ROUND(AVG(b.hemoglobin)::numeric,     2)     AS avg_hemoglobin,
    ROUND(AVG(b.cholesterol_total)::numeric, 2)  AS avg_cholesterol,
    MAX(b.report_date)                           AS latest_report_date,
    SUM(CASE WHEN b.glucose          > 126 THEN 1 ELSE 0 END) AS high_glucose_count,
    SUM(CASE WHEN b.cholesterol_total > 200 THEN 1 ELSE 0 END) AS high_cholesterol_count,
    SUM(CASE WHEN b.hemoglobin        < 12  THEN 1 ELSE 0 END) AS low_hemoglobin_count
FROM {{ ref('stg_patients') }} p
LEFT JOIN {{ ref('stg_blood_reports') }} b
    ON p.customer_id = b.customer_id
GROUP BY
    p.customer_id, p.name, p.age,
    p.gender, p.blood_type, p.city
