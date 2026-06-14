from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Mapping, TypeAlias


class Dataset(StrEnum):
    SITES = "sites"
    PRODUCTS = "products"
    PRODUCTION_ORDERS = "production_orders"
    QUALITY_CONTROLS = "quality_controls"


@dataclass(frozen=True, slots=True)
class SourceFile:
    dataset: Dataset
    path: Path
    xml_record_tag: str | None = None


@dataclass(frozen=True, slots=True)
class SourceRow:
    values: Mapping[str, str | None]
    location: str


@dataclass(frozen=True, slots=True)
class Site:
    site_code: str
    site_name: str
    country_code: str
    city: str
    timezone: str
    status: str
    commissioned_on: date | None


@dataclass(frozen=True, slots=True)
class Product:
    product_code: str
    product_name: str
    product_family: str
    unit_of_measure: str
    standard_cycle_time_seconds: Decimal
    target_scrap_rate: Decimal
    is_active: bool


@dataclass(frozen=True, slots=True)
class ProductionOrder:
    order_number: str
    site_code: str
    product_code: str
    line_code: str
    order_status: str
    planned_quantity: int
    produced_quantity: int
    rejected_quantity: int
    planned_start_at: datetime
    planned_end_at: datetime
    actual_start_at: datetime | None
    actual_end_at: datetime | None


@dataclass(frozen=True, slots=True)
class QualityControl:
    control_reference: str
    order_number: str
    controlled_at: datetime
    sample_size: int
    passed_quantity: int
    failed_quantity: int
    result: str
    defect_category: str | None
    inspector_name: str
    notes: str | None


ImportRecord: TypeAlias = Site | Product | ProductionOrder | QualityControl


@dataclass(frozen=True, slots=True)
class PersistenceError:
    index: int
    message: str


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
