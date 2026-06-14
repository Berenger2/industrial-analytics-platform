from collections.abc import Sequence
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, ContextManager

import psycopg

from .models import (
    Dataset,
    ImportRecord,
    PersistenceError,
    Product,
    ProductionOrder,
    QualityControl,
    Site,
)

UPSERT_SITE_QUERY = """
    INSERT INTO analytics.dim_sites (
        site_code, site_name, country_code, city, timezone, status, commissioned_on
    )
    VALUES (
        %(site_code)s, %(site_name)s, %(country_code)s, %(city)s,
        %(timezone)s, %(status)s, %(commissioned_on)s
    )
    ON CONFLICT (site_code) DO UPDATE SET
        site_name = EXCLUDED.site_name,
        country_code = EXCLUDED.country_code,
        city = EXCLUDED.city,
        timezone = EXCLUDED.timezone,
        status = EXCLUDED.status,
        commissioned_on = EXCLUDED.commissioned_on
"""

UPSERT_PRODUCT_QUERY = """
    INSERT INTO analytics.dim_products (
        product_code, product_name, product_family, unit_of_measure,
        standard_cycle_time_seconds, target_scrap_rate, is_active
    )
    VALUES (
        %(product_code)s, %(product_name)s, %(product_family)s,
        %(unit_of_measure)s, %(standard_cycle_time_seconds)s,
        %(target_scrap_rate)s, %(is_active)s
    )
    ON CONFLICT (product_code) DO UPDATE SET
        product_name = EXCLUDED.product_name,
        product_family = EXCLUDED.product_family,
        unit_of_measure = EXCLUDED.unit_of_measure,
        standard_cycle_time_seconds = EXCLUDED.standard_cycle_time_seconds,
        target_scrap_rate = EXCLUDED.target_scrap_rate,
        is_active = EXCLUDED.is_active
"""

UPSERT_PRODUCTION_ORDER_QUERY = """
    INSERT INTO analytics.fact_production_orders (
        order_number, site_id, product_id, line_code, order_status,
        planned_quantity, produced_quantity, rejected_quantity,
        planned_start_at, planned_end_at, actual_start_at, actual_end_at
    )
    SELECT
        %(order_number)s, site.site_id, product.product_id, %(line_code)s,
        %(order_status)s, %(planned_quantity)s, %(produced_quantity)s,
        %(rejected_quantity)s, %(planned_start_at)s, %(planned_end_at)s,
        %(actual_start_at)s, %(actual_end_at)s
    FROM analytics.dim_sites AS site
    CROSS JOIN analytics.dim_products AS product
    WHERE site.site_code = %(site_code)s
      AND product.product_code = %(product_code)s
    ON CONFLICT (order_number) DO UPDATE SET
        site_id = EXCLUDED.site_id,
        product_id = EXCLUDED.product_id,
        line_code = EXCLUDED.line_code,
        order_status = EXCLUDED.order_status,
        planned_quantity = EXCLUDED.planned_quantity,
        produced_quantity = EXCLUDED.produced_quantity,
        rejected_quantity = EXCLUDED.rejected_quantity,
        planned_start_at = EXCLUDED.planned_start_at,
        planned_end_at = EXCLUDED.planned_end_at,
        actual_start_at = EXCLUDED.actual_start_at,
        actual_end_at = EXCLUDED.actual_end_at
"""

UPSERT_QUALITY_CONTROL_QUERY = """
    INSERT INTO analytics.fact_quality_controls (
        control_reference, production_order_id, controlled_at, sample_size,
        passed_quantity, failed_quantity, result, defect_category,
        inspector_name, notes
    )
    SELECT
        %(control_reference)s, production_order.production_order_id,
        %(controlled_at)s, %(sample_size)s, %(passed_quantity)s,
        %(failed_quantity)s, %(result)s, %(defect_category)s,
        %(inspector_name)s, %(notes)s
    FROM analytics.fact_production_orders AS production_order
    WHERE production_order.order_number = %(order_number)s
    ON CONFLICT (control_reference) DO UPDATE SET
        production_order_id = EXCLUDED.production_order_id,
        controlled_at = EXCLUDED.controlled_at,
        sample_size = EXCLUDED.sample_size,
        passed_quantity = EXCLUDED.passed_quantity,
        failed_quantity = EXCLUDED.failed_quantity,
        result = EXCLUDED.result,
        defect_category = EXCLUDED.defect_category,
        inspector_name = EXCLUDED.inspector_name,
        notes = EXCLUDED.notes
"""

INSERT_LOG_QUERY = """
    INSERT INTO analytics.import_logs (
        import_reference, source_system, source_file, import_status,
        rows_received, rows_processed, rows_rejected, started_at
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

    def transaction(self) -> ContextManager[Any]:
        return self.connection.transaction()

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
                (import_reference, source_system, source_file.name, started_at),
            )
        self.connection.commit()

    def upsert_records(
        self,
        dataset: Dataset,
        records: Sequence[ImportRecord],
    ) -> list[PersistenceError]:
        if not records:
            return []
        if dataset == Dataset.PRODUCTION_ORDERS:
            return self._upsert_production_orders(records)
        if dataset == Dataset.QUALITY_CONTROLS:
            return self._upsert_quality_controls(records)
        query = (
            UPSERT_SITE_QUERY
            if dataset == Dataset.SITES
            else UPSERT_PRODUCT_QUERY
        )
        self._executemany(query, records)
        return []

    def _upsert_production_orders(
        self,
        records: Sequence[ImportRecord],
    ) -> list[PersistenceError]:
        orders = [record for record in records if isinstance(record, ProductionOrder)]
        known_sites = self._known_values(
            "analytics.dim_sites", "site_code", {order.site_code for order in orders}
        )
        known_products = self._known_values(
            "analytics.dim_products",
            "product_code",
            {order.product_code for order in orders},
        )
        errors: list[PersistenceError] = []
        valid: list[ProductionOrder] = []
        for index, order in enumerate(orders):
            missing = []
            if order.site_code not in known_sites:
                missing.append(f"unknown site_code {order.site_code}")
            if order.product_code not in known_products:
                missing.append(f"unknown product_code {order.product_code}")
            if missing:
                errors.append(PersistenceError(index, ", ".join(missing)))
            else:
                valid.append(order)
        self._executemany(UPSERT_PRODUCTION_ORDER_QUERY, valid)
        return errors

    def _upsert_quality_controls(
        self,
        records: Sequence[ImportRecord],
    ) -> list[PersistenceError]:
        controls = [
            record for record in records if isinstance(record, QualityControl)
        ]
        known_orders = self._known_values(
            "analytics.fact_production_orders",
            "order_number",
            {control.order_number for control in controls},
        )
        errors: list[PersistenceError] = []
        valid: list[QualityControl] = []
        for index, control in enumerate(controls):
            if control.order_number not in known_orders:
                errors.append(
                    PersistenceError(
                        index,
                        f"unknown order_number {control.order_number}",
                    )
                )
            else:
                valid.append(control)
        self._executemany(UPSERT_QUALITY_CONTROL_QUERY, valid)
        return errors

    def _known_values(
        self,
        table: str,
        column: str,
        values: set[str],
    ) -> set[str]:
        if not values:
            return set()
        query = f"SELECT {column} FROM {table} WHERE {column} = ANY(%s)"
        with self.connection.cursor() as cursor:
            cursor.execute(query, (list(values),))
            return {str(row[0]) for row in cursor.fetchall()}

    def _executemany(
        self,
        query: str,
        records: Sequence[Site | Product | ProductionOrder | QualityControl],
    ) -> None:
        if not records:
            return
        with self.connection.cursor() as cursor:
            cursor.executemany(query, [asdict(record) for record in records])

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

    def commit(self) -> None:
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()
