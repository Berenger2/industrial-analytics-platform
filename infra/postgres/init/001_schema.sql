CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.production_metrics (
    id BIGSERIAL PRIMARY KEY,
    machine_id TEXT NOT NULL,
    site TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    unit TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT production_metrics_source_key
        UNIQUE (machine_id, metric_name, recorded_at)
);

CREATE INDEX IF NOT EXISTS production_metrics_recorded_at_idx
    ON analytics.production_metrics (recorded_at);

CREATE INDEX IF NOT EXISTS production_metrics_machine_id_idx
    ON analytics.production_metrics (machine_id);
