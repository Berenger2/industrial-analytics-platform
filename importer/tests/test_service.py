import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from collections.abc import Sequence
from typing import Any
from unittest.mock import patch

from src.config import Config
from src.models import ProductionMetric
from src.service import ImportService


class FakeRepository:
    def __init__(self) -> None:
        self.created_logs: list[dict[str, Any]] = []
        self.finished_logs: list[dict[str, Any]] = []
        self.metrics: list[ProductionMetric] = []
        self.was_rolled_back = False

    def create_log(
        self,
        import_reference: str,
        source_system: str,
        source_file: Path,
        started_at: datetime,
    ) -> None:
        self.created_logs.append(
            {
                "import_reference": import_reference,
                "source_system": source_system,
                "source_file": source_file,
                "started_at": started_at,
            }
        )

    def insert_metrics(self, metrics: Sequence[ProductionMetric]) -> None:
        self.metrics.extend(metrics)

    def finish_log(self, **values: Any) -> None:
        self.finished_logs.append(values)

    def rollback(self) -> None:
        self.was_rolled_back = True


def make_config(input_directory: Path) -> Config:
    return Config(
        database_url="postgresql://test",
        input_directory=input_directory,
        source_system="unit-tests",
        csv_pattern="*.csv",
        csv_delimiter=",",
        xml_pattern="*.xml",
        xml_record_tag="record",
        log_level="INFO",
        database_connect_timeout_seconds=10,
        database_application_name="importer-tests",
        batch_size=500,
        max_error_details=10,
    )


class ImportServiceTests(unittest.TestCase):
    def test_imports_valid_rows_and_records_validation_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_directory = Path(directory)
            Path(input_directory, "metrics.csv").write_text(
                "machine_id,site,metric_name,metric_value,unit,recorded_at\n"
                "PRESS-01,Lyon,temperature,42.5,celsius,"
                "2026-01-01T10:00:00Z\n"
                "PRESS-02,Lyon,temperature,invalid,celsius,"
                "2026-01-01T10:00:00Z\n",
                encoding="utf-8",
            )
            repository = FakeRepository()

            summary = ImportService(
                make_config(input_directory),
                repository,
            ).run()

        self.assertEqual(len(repository.metrics), 1)
        self.assertEqual(summary.rows_received, 2)
        self.assertEqual(summary.rows_processed, 1)
        self.assertEqual(summary.rows_rejected, 1)
        self.assertEqual(repository.finished_logs[0]["status"], "partial")
        self.assertIn(
            "metric_value must be numeric",
            repository.finished_logs[0]["error_message"],
        )

    def test_records_malformed_xml_as_failed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_directory = Path(directory)
            Path(input_directory, "metrics.xml").write_text(
                "<production_metrics><record>",
                encoding="utf-8",
            )
            repository = FakeRepository()

            summary = ImportService(
                make_config(input_directory),
                repository,
            ).run()

        self.assertEqual(summary.files_failed, 1)
        self.assertTrue(repository.was_rolled_back)
        self.assertEqual(repository.finished_logs[0]["status"], "failed")

    def test_records_database_error_as_failed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_directory = Path(directory)
            Path(input_directory, "metrics.csv").write_text(
                "machine_id,site,metric_name,metric_value,unit,recorded_at\n"
                "PRESS-01,Lyon,temperature,42.5,celsius,"
                "2026-01-01T10:00:00Z\n",
                encoding="utf-8",
            )
            repository = FakeRepository()

            with patch.object(
                repository,
                "insert_metrics",
                side_effect=RuntimeError("database unavailable"),
            ):
                summary = ImportService(
                    make_config(input_directory),
                    repository,
                ).run()

        self.assertEqual(summary.files_failed, 1)
        self.assertTrue(repository.was_rolled_back)
        self.assertEqual(repository.finished_logs[0]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
