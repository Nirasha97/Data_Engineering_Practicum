
-- File metadata from MinIO
SELECT
    customer_id,
    file_name,
    data_type,
    object_path,
    size_bytes,
    file_ext,
    last_modified,
    indexed_at
FROM public.customer_files
