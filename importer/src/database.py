from datetime import datetime
from pathlib import Path
from typing import Sequence

import psycopg

from .models import ProductionMetric

INSERT_METRIC_QUERY = """
    INSERT INTO analytics.production_metrics (
        machine_id,
        site,
        metric_name,
        metric_value,
        unit,
        recorded_at
    )
    VALUES (
        %(machine_id)s,
        %(site)s,
        %(metric_name)s,
        %(metric_value)s,
        %(unit)s,
        %(recorded_at)s
    )
    ON CONFLICT (machine_id, metric_name, recorded_at) DO NOTHING
"""

INSERT_LOG_QUERY = """
    INSERT INTO analytics.import_logs (
        import_reference,
        source_system,
        source_file,
        import_status,
        rows_received,
        rows_processed,
        rows_rejected,
        started_at
    )
    VALUES (%s, %s, %s, 'running', 0, 0, 0, %s)
"""

UPDATE_LOG_QUERY = """
    UPDATE analytics.import_logs
    SET
        import_status = %s,
        rows_received = %s,
        rows_processed = %s,
        rows_rejected = %s,
        completed_at = %s,
        error_message = %s
    WHERE import_reference = %s
"""


class ImportRepository:
    def __init__(self, connection: psycopg.Connection[tuple[object, ...]]) -> None:
        self.connection = connection

    def create_log(
        self,
        import_reference: str,
        source_system: str,
        source_file: Path,
        started_at: datetime,
    ) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                INSERT_LOG_QUERY,
                (
                    import_reference,
                    source_system,
                    source_file.name,
                    started_at,
                ),
            )
        self.connection.commit()

    def insert_metrics(self, metrics: Sequence[ProductionMetric]) -> None:
        parameters = [
            {
                "machine_id": metric.machine_id,
                "site": metric.site,
                "metric_name": metric.metric_name,
                "metric_value": metric.metric_value,
                "unit": metric.unit,
                "recorded_at": metric.recorded_at,
            }
            for metric in metrics
        ]
        if not parameters:
            return
        with self.connection.cursor() as cursor:
            cursor.executemany(INSERT_METRIC_QUERY, parameters)

    def finish_log(
        self,
        import_reference: str,
        status: str,
        rows_received: int,
        rows_processed: int,
        rows_rejected: int,
        completed_at: datetime,
        error_message: str | None,
    ) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                UPDATE_LOG_QUERY,
                (
                    status,
                    rows_received,
                    rows_processed,
                    rows_rejected,
                    completed_at,
                    error_message,
                    import_reference,
                ),
            )
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()
