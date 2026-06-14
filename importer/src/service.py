import logging
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ContextManager, Protocol
from uuid import uuid4

from .config import Config
from .models import (
    Dataset,
    FileImportResult,
    ImportRecord,
    PersistenceError,
    RowError,
    RunSummary,
    SourceFile,
    SourceRow,
)
from .parsers import SourceFormatError, parse_file
from .validation import (
    ValidationError,
    validate_product,
    validate_production_order,
    validate_quality_control,
    validate_site,
)

LOGGER = logging.getLogger(__name__)
Validator = Callable[[SourceRow], ImportRecord]

VALIDATORS: dict[Dataset, Validator] = {
    Dataset.SITES: validate_site,
    Dataset.PRODUCTS: validate_product,
    Dataset.PRODUCTION_ORDERS: validate_production_order,
    Dataset.QUALITY_CONTROLS: validate_quality_control,
}


class FileProcessingError(RuntimeError):
    def __init__(self, rows_received: int, cause: Exception) -> None:
        super().__init__(str(cause))
        self.rows_received = rows_received
        self.cause = cause


class Repository(Protocol):
    def transaction(self) -> ContextManager[Any]: ...

    def create_log(
        self,
        import_reference: str,
        source_system: str,
        source_file: Path,
        started_at: datetime,
    ) -> None: ...

    def upsert_records(
        self,
        dataset: Dataset,
        records: Sequence[ImportRecord],
    ) -> list[PersistenceError]: ...

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

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


def build_import_reference(dataset: Dataset, started_at: datetime) -> str:
    timestamp = started_at.strftime("%Y%m%d%H%M%S")
    return f"IMP-{dataset.value.upper()}-{timestamp}-{uuid4().hex[:8]}"


def summarize_errors(errors: list[RowError], total_errors: int) -> str | None:
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
        source_files = self.config.source_files()
        LOGGER.info(
            "Business source files scheduled",
            extra={
                "event": "files_scheduled",
                "input_directory": str(self.config.input_directory),
                "files_total": len(source_files),
            },
        )
        results = [self.import_file(source_file) for source_file in source_files]
        return RunSummary(
            files_total=len(results),
            files_failed=sum(result.status == "failed" for result in results),
            rows_received=sum(result.rows_received for result in results),
            rows_processed=sum(result.rows_processed for result in results),
            rows_rejected=sum(result.rows_rejected for result in results),
        )

    def import_file(self, source_file: SourceFile) -> FileImportResult:
        started_at = datetime.now(UTC)
        reference = build_import_reference(source_file.dataset, started_at)
        self.repository.create_log(
            reference,
            self.config.source_system,
            source_file.path,
            started_at,
        )
        LOGGER.info(
            "File import started",
            extra={
                "event": "file_import_started",
                "dataset": source_file.dataset.value,
                "import_reference": reference,
                "source_file": source_file.path.name,
            },
        )

        try:
            with self.repository.transaction():
                result, errors = self._process_file(source_file)
                self.repository.finish_log(
                    import_reference=reference,
                    status=result.status,
                    rows_received=result.rows_received,
                    rows_processed=result.rows_processed,
                    rows_rejected=result.rows_rejected,
                    completed_at=datetime.now(UTC),
                    error_message=summarize_errors(
                        errors,
                        result.rows_rejected,
                    ),
                )
        except FileProcessingError as error:
            if not isinstance(error.cause, SourceFormatError):
                LOGGER.exception(
                    "File import failed",
                    extra={
                        "event": "file_import_failed",
                        "dataset": source_file.dataset.value,
                        "import_reference": reference,
                        "source_file": source_file.path.name,
                    },
                )
            prefix = (
                "Invalid source format"
                if isinstance(error.cause, SourceFormatError)
                else type(error.cause).__name__
            )
            return self._record_failure(
                reference,
                source_file,
                error.rows_received,
                f"{prefix}: {error.cause}",
            )
        except Exception as error:
            LOGGER.exception(
                "File import failed",
                extra={
                    "event": "file_import_failed",
                    "dataset": source_file.dataset.value,
                    "import_reference": reference,
                    "source_file": source_file.path.name,
                },
            )
            return self._record_failure(
                reference,
                source_file,
                0,
                f"{type(error).__name__}: {error}",
            )

        LOGGER.info(
            "File import completed",
            extra={
                "event": "file_import_completed",
                "dataset": source_file.dataset.value,
                "import_reference": reference,
                "source_file": source_file.path.name,
                "status": result.status,
                "rows_received": result.rows_received,
                "rows_processed": result.rows_processed,
                "rows_rejected": result.rows_rejected,
            },
        )
        return result

    def _process_file(
        self,
        source_file: SourceFile,
    ) -> tuple[FileImportResult, list[RowError]]:
        rows_received = 0
        rows_processed = 0
        rows_rejected = 0
        errors: list[RowError] = []
        batch: list[tuple[SourceRow, ImportRecord]] = []
        validator = VALIDATORS[source_file.dataset]

        try:
            for source_row in parse_file(
                source_file.path,
                source_file.xml_record_tag,
                self.config.csv_delimiter,
            ):
                rows_received += 1
                try:
                    batch.append((source_row, validator(source_row)))
                except ValidationError as error:
                    rows_rejected += 1
                    self._append_error(errors, source_row.location, str(error))
                if len(batch) >= self.config.batch_size:
                    processed, rejected = self._flush_batch(
                        source_file.dataset, batch, errors
                    )
                    rows_processed += processed
                    rows_rejected += rejected
                    batch.clear()

            processed, rejected = self._flush_batch(
                source_file.dataset, batch, errors
            )
        except Exception as error:
            raise FileProcessingError(rows_received, error) from error
        rows_processed += processed
        rows_rejected += rejected
        status = "partial" if rows_rejected else "completed"
        return (
            FileImportResult(
                path=source_file.path,
                status=status,
                rows_received=rows_received,
                rows_processed=rows_processed,
                rows_rejected=rows_rejected,
            ),
            errors,
        )

    def _flush_batch(
        self,
        dataset: Dataset,
        batch: list[tuple[SourceRow, ImportRecord]],
        errors: list[RowError],
    ) -> tuple[int, int]:
        if not batch:
            return 0, 0
        persistence_errors = self.repository.upsert_records(
            dataset,
            [record for _, record in batch],
        )
        for error in persistence_errors:
            source_row = batch[error.index][0]
            self._append_error(errors, source_row.location, error.message)
        rejected = len(persistence_errors)
        return len(batch) - rejected, rejected

    def _append_error(
        self,
        errors: list[RowError],
        location: str,
        message: str,
    ) -> None:
        if len(errors) < self.config.max_error_details:
            errors.append(RowError(location, message))

    def _record_failure(
        self,
        reference: str,
        source_file: SourceFile,
        rows_received: int,
        message: str,
    ) -> FileImportResult:
        self.repository.rollback()
        self.repository.finish_log(
            import_reference=reference,
            status="failed",
            rows_received=rows_received,
            rows_processed=0,
            rows_rejected=rows_received,
            completed_at=datetime.now(UTC),
            error_message=message,
        )
        self.repository.commit()
        LOGGER.error(
            "File import recorded as failed",
            extra={
                "event": "file_import_failed",
                "dataset": source_file.dataset.value,
                "import_reference": reference,
                "source_file": source_file.path.name,
                "error": message,
            },
        )
        return FileImportResult(
            path=source_file.path,
            status="failed",
            rows_received=rows_received,
            rows_processed=0,
            rows_rejected=rows_received,
        )
