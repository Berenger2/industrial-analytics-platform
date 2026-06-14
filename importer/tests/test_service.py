import tempfile
import unittest
from collections.abc import Sequence
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

from src.config import Config
from src.models import Dataset, ImportRecord, PersistenceError
from src.service import ImportService


class FakeRepository:
    def __init__(self) -> None:
        self.created_logs: list[dict[str, Any]] = []
        self.finished_logs: list[dict[str, Any]] = []
        self.records: dict[Dataset, list[ImportRecord]] = {
            dataset: [] for dataset in Dataset
        }
        self.persistence_errors: dict[Dataset, list[PersistenceError]] = {}
        self.was_rolled_back = False
        self.was_committed = False

    def transaction(self) -> Any:
        return nullcontext()

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

    def upsert_records(
        self,
        dataset: Dataset,
        records: Sequence[ImportRecord],
    ) -> list[PersistenceError]:
        self.records[dataset].extend(records)
        return self.persistence_errors.get(dataset, [])

    def finish_log(self, **values: Any) -> None:
        self.finished_logs.append(values)

    def commit(self) -> None:
        self.was_committed = True

    def rollback(self) -> None:
        self.was_rolled_back = True


def make_config(input_directory: Path, batch_size: int = 500) -> Config:
    return Config(
        database_url="postgresql://test",
        input_directory=input_directory,
        source_system="unit-tests",
        sites_file="sites.csv",
        products_file="products.csv",
        production_orders_file="production_orders.csv",
        quality_controls_file="quality_controls.xml",
        quality_control_record_tag="quality_control",
        csv_delimiter=",",
        log_level="INFO",
        database_connect_timeout_seconds=10,
        database_application_name="importer-tests",
        batch_size=batch_size,
        max_error_details=10,
    )


def write_valid_files(directory: Path) -> None:
    Path(directory, "sites.csv").write_text(
        "site_code,site_name,country_code,city,timezone,status,commissioned_on\n"
        "FR-LYO,Lyon Manufacturing,FR,Lyon,Europe/Paris,active,2014-09-15\n",
        encoding="utf-8",
    )
    Path(directory, "products.csv").write_text(
        "product_code,product_name,product_family,unit_of_measure,"
        "standard_cycle_time_seconds,target_scrap_rate,is_active\n"
        "DRV-X100,Variable Speed Drive,Industrial Drives,unit,84,1.5,true\n",
        encoding="utf-8",
    )
    Path(directory, "production_orders.csv").write_text(
        "order_number,site_code,product_code,line_code,order_status,"
        "planned_quantity,produced_quantity,rejected_quantity,"
        "planned_start_at,planned_end_at,actual_start_at,actual_end_at\n"
        "PO-001,FR-LYO,DRV-X100,LINE-A,completed,100,98,2,"
        "2026-05-01T06:00:00Z,2026-05-01T14:00:00Z,"
        "2026-05-01T06:05:00Z,2026-05-01T13:50:00Z\n",
        encoding="utf-8",
    )
    Path(directory, "quality_controls.xml").write_text(
        """
        <quality_controls>
          <quality_control>
            <control_reference>QC-001</control_reference>
            <order_number>PO-001</order_number>
            <controlled_at>2026-05-01T12:00:00Z</controlled_at>
            <sample_size>20</sample_size>
            <passed_quantity>19</passed_quantity>
            <failed_quantity>1</failed_quantity>
            <result>warning</result>
            <defect_category>Surface finish</defect_category>
            <inspector_name>Claire Bernard</inspector_name>
            <notes>Review requested</notes>
          </quality_control>
        </quality_controls>
        """,
        encoding="utf-8",
    )


class ImportServiceTests(unittest.TestCase):
    def test_imports_four_business_files_in_dependency_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_directory = Path(directory)
            write_valid_files(input_directory)
            repository = FakeRepository()

            summary = ImportService(
                make_config(input_directory),
                repository,
            ).run()

        self.assertEqual(summary.files_total, 4)
        self.assertEqual(summary.files_failed, 0)
        self.assertEqual(summary.rows_processed, 4)
        self.assertEqual(
            [log["source_file"].name for log in repository.created_logs],
            [
                "sites.csv",
                "products.csv",
                "production_orders.csv",
                "quality_controls.xml",
            ],
        )
        self.assertEqual(len(repository.records[Dataset.PRODUCTION_ORDERS]), 1)

    def test_records_validation_and_reference_errors_as_partial(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_directory = Path(directory)
            write_valid_files(input_directory)
            Path(input_directory, "sites.csv").write_text(
                "site_code,site_name,country_code,city,timezone,status\n"
                "FR-LYO,Lyon Manufacturing,FRA,Lyon,Europe/Paris,active\n",
                encoding="utf-8",
            )
            repository = FakeRepository()
            repository.persistence_errors[Dataset.PRODUCTION_ORDERS] = [
                PersistenceError(0, "unknown site_code FR-LYO")
            ]

            summary = ImportService(
                make_config(input_directory),
                repository,
            ).run()

        self.assertEqual(summary.rows_rejected, 2)
        self.assertEqual(repository.finished_logs[0]["status"], "partial")
        self.assertIn(
            "country_code",
            repository.finished_logs[0]["error_message"],
        )
        self.assertEqual(repository.finished_logs[2]["status"], "partial")

    def test_records_missing_file_as_failed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_directory = Path(directory)
            write_valid_files(input_directory)
            Path(input_directory, "quality_controls.xml").unlink()
            repository = FakeRepository()

            summary = ImportService(
                make_config(input_directory),
                repository,
            ).run()

        self.assertEqual(summary.files_failed, 1)
        self.assertTrue(repository.was_rolled_back)
        self.assertEqual(repository.finished_logs[-1]["status"], "failed")

    def test_records_database_error_as_failed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_directory = Path(directory)
            write_valid_files(input_directory)
            repository = FakeRepository()

            with patch.object(
                repository,
                "upsert_records",
                side_effect=RuntimeError("database unavailable"),
            ):
                summary = ImportService(
                    make_config(input_directory),
                    repository,
                ).run()

        self.assertEqual(summary.files_failed, 4)
        self.assertTrue(repository.was_rolled_back)
        self.assertTrue(repository.was_committed)
        self.assertTrue(
            all(log["status"] == "failed" for log in repository.finished_logs)
        )


if __name__ == "__main__":
    unittest.main()
