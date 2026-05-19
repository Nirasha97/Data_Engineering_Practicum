
-- Clean and standardise raw customers table
SELECT
    customer_id,
    name,
    age,
    gender,
    blood_type,
    city,
    first_seen   AS registered_date
FROM public.customers
WHERE customer_id IS NOT NULL
