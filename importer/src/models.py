from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True, slots=True)
class SourceRow:
    values: Mapping[str, str | None]
    location: str


@dataclass(frozen=True, slots=True)
class ProductionMetric:
    machine_id: str
    site: str
    metric_name: str
    metric_value: Decimal
    unit: str
    recorded_at: datetime


@dataclass(frozen=True, slots=True)
class RowError:
    location: str
    message: str

    def format(self) -> str:
        return f"{self.location}: {self.message}"


@dataclass(frozen=True, slots=True)
class FileImportResult:
    path: Path
    status: str
    rows_received: int
    rows_processed: int
    rows_rejected: int


@dataclass(frozen=True, slots=True)
class RunSummary:
    files_total: int
    files_failed: int
    rows_received: int
    rows_processed: int
    rows_rejected: int
