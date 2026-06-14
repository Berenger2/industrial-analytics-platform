-- Remove the superseded machine-metric model after its Cube definition is gone.
-- The statements are idempotent and safe on new installations.
DROP VIEW IF EXISTS analytics.latest_machine_metrics;
DROP TABLE IF EXISTS analytics.production_metrics;
