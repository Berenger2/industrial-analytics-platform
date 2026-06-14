CREATE OR REPLACE VIEW analytics.latest_machine_metrics AS
SELECT DISTINCT ON (machine_id, metric_name)
    machine_id,
    site,
    metric_name,
    metric_value,
    unit,
    recorded_at
FROM analytics.production_metrics
ORDER BY machine_id, metric_name, recorded_at DESC;
