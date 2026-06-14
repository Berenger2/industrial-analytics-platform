import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, Sequence
from uuid import uuid4

from .config import Config
from .models import (
    FileImportResult,
    ProductionMetric,
    RowError,
    RunSummary,
)
from .parsers import SourceFormatError, discover_files, parse_file
from .validation import ValidationError, validate_metric

LOGGER = logging.getLogger(__name__)


class Repository(Protocol):
    def create_log(
        self,
        import_reference: str,
        source_system: str,
        source_file: Path,
        started_at: datetime,
    ) -> None: ...

    def insert_metrics(self, metrics: Sequence[ProductionMetric]) -> None: ...

    def finish_log(
        self,
        import_reference: str,
        status: str,
        rows_received: int,
        rows_processed: int,
        rows_rejected: int,
        completed_at: datetime,
        error_message: str | None,
    ) -> None: ...

    def rollback(self) -> None: ...


def build_import_reference(started_at: datetime) -> str:
    timestamp = started_at.strftime("%Y%m%d%H%M%S")
    return f"IMP-{timestamp}-{uuid4().hex[:16]}"


def summarize_errors(
    errors: list[RowError],
    total_errors: int,
) -> str | None:
    if not errors:
        return None
    details = [error.format() for error in errors]
    remaining = total_errors - len(details)
    if remaining:
        details.append(f"{remaining} additional error(s) omitted")
    return " | ".join(details)


class ImportService:
    def __init__(self, config: Config, repository: Repository) -> None:
        self.config = config
        self.repository = repository

    def run(self) -> RunSummary:
        files = discover_files(
            self.config.input_directory,
            self.config.csv_pattern,
            self.config.xml_pattern,
        )
        LOGGER.info(
            "Input files discovered",
            extra={
                "event": "files_discovered",
                "input_directory": str(self.config.input_directory),
                "files_total": len(files),
            },
        )

        results = [self.import_file(path) for path in files]
        return RunSummary(
            files_total=len(results),
            files_failed=sum(result.status == "failed" for result in results),
            rows_received=sum(result.rows_received for result in results),
            rows_processed=sum(result.rows_processed for result in results),
            rows_rejected=sum(result.rows_rejected for result in results),
        )

    def import_file(self, path: Path) -> FileImportResult:
        started_at = datetime.now(UTC)
        import_reference = build_import_reference(started_at)
        rows_received = 0

        self.repository.create_log(
            import_reference,
            self.config.source_system,
            path,
            started_at,
        )
        LOGGER.info(
            "File import started",
            extra={
                "event": "file_import_started",
                "import_reference": import_reference,
                "source_file": path.name,
            },
        )

        try:
            metrics_batch: list[ProductionMetric] = []
            errors: list[RowError] = []
            rows_processed = 0
            rows_rejected = 0
            for source_row in parse_file(
                path,
                self.config.xml_record_tag,
                self.config.csv_delimiter,
            ):
                rows_received += 1
                try:
                    metrics_batch.append(validate_metric(source_row))
                    rows_processed += 1
                    if len(metrics_batch) >= self.config.batch_size:
                        self.repository.insert_metrics(metrics_batch)
                        metrics_batch.clear()
                except ValidationError as error:
                    rows_rejected += 1
                    if len(errors) < self.config.max_error_details:
                        errors.append(RowError(source_row.location, str(error)))

            self.repository.insert_metrics(metrics_batch)
            status = "partial" if errors else "completed"
            self.repository.finish_log(
                import_reference=import_reference,
                status=status,
                rows_received=rows_received,
                rows_processed=rows_processed,
                rows_rejected=rows_rejected,
                completed_at=datetime.now(UTC),
                error_message=summarize_errors(errors, rows_rejected),
            )
        except SourceFormatError as error:
            return self._record_failure(
                import_reference,
                path,
                rows_received,
                f"Invalid source format: {error}",
            )
        except Exception as error:
            LOGGER.exception(
                "File import failed",
                extra={
                    "event": "file_import_failed",
                    "import_reference": import_reference,
                    "source_file": path.name,
                },
            )
            return self._record_failure(
                import_reference,
                path,
                rows_received,
                f"{type(error).__name__}: {error}",
            )

        result = FileImportResult(
            path=path,
            status=status,
            rows_received=rows_received,
            rows_processed=rows_processed,
            rows_rejected=rows_rejected,
        )
        LOGGER.info(
            "File import completed",
            extra={
                "event": "file_import_completed",
                "import_reference": import_reference,
                "source_file": path.name,
                "status": status,
                "rows_received": rows_received,
                "rows_processed": rows_processed,
                "rows_rejected": rows_rejected,
            },
        )
        return result

    def _record_failure(
        self,
        import_reference: str,
        path: Path,
        rows_received: int,
        message: str,
    ) -> FileImportResult:
        self.repository.rollback()
        self.repository.finish_log(
            import_reference=import_reference,
            status="failed",
            rows_received=rows_received,
            rows_processed=0,
            rows_rejected=rows_received,
            completed_at=datetime.now(UTC),
            error_message=message,
        )
        LOGGER.error(
            "File import recorded as failed",
            extra={
                "event": "file_import_failed",
                "import_reference": import_reference,
                "source_file": path.name,
                "error": message,
            },
        )
        return FileImportResult(
            path=path,
            status="failed",
            rows_received=rows_received,
            rows_processed=0,
            rows_rejected=rows_received,
        )
