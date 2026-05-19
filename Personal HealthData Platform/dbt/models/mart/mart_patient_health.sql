
-- Final patient health summary — one row per patient
SELECT
    customer_id,
    name,
    age,
    gender,
    blood_type,
    city,
    total_reports,
    avg_glucose,
    avg_hemoglobin,
    avg_cholesterol,
    latest_report_date,
    high_glucose_count,
    high_cholesterol_count,
    low_hemoglobin_count,
    CASE
        WHEN high_glucose_count      > 0
          OR high_cholesterol_count  > 0
          OR low_hemoglobin_count    > 0
        THEN 'AT RISK'
        ELSE 'NORMAL'
    END                 AS health_status,
    NOW()               AS last_updated
FROM {{ ref('int_patient_blood_summary') }}
