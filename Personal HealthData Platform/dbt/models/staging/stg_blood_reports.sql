
-- Clean blood reports — filter nulls, cast types
SELECT
    id                    AS report_id,
    customer_id,
    report_date::DATE     AS report_date,
    lab_name,
    glucose,
    hemoglobin,
    cholesterol_total,
    cholesterol_hdl,
    cholesterol_ldl,
    triglycerides,
    wbc,
    rbc,
    is_valid,
    minio_path,
    indexed_at
FROM public.blood_reports
WHERE customer_id  IS NOT NULL
  AND report_date  IS NOT NULL
