import os
from dataclasses import dataclass
from pathlib import Path

from .models import Dataset, SourceFile


class ConfigurationError(ValueError):
    """Raised when importer configuration is missing or invalid."""


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigurationError(f"{name} must be set")
    return value


def positive_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as error:
        raise ConfigurationError(f"{name} must be an integer") from error
    if value <= 0:
        raise ConfigurationError(f"{name} must be greater than zero")
    return value


def optional_env(name: str, default: str) -> str:
    value = os.getenv(name, default).strip()
    if not value:
        raise ConfigurationError(f"{name} must not be empty")
    return value


@dataclass(frozen=True, slots=True)
class Config:
    database_url: str
    input_directory: Path
    source_system: str
    sites_file: str
    products_file: str
    production_orders_file: str
    quality_controls_file: str
    quality_control_record_tag: str
    csv_delimiter: str
    log_level: str
    database_connect_timeout_seconds: int
    database_application_name: str
    batch_size: int
    max_error_details: int

    @classmethod
    def from_env(cls) -> "Config":
        input_directory = Path(require_env("IMPORT_INPUT_DIR"))
        if not input_directory.is_dir():
            raise ConfigurationError(
                f"IMPORT_INPUT_DIR is not a directory: {input_directory}"
            )

        source_system = require_env("IMPORT_SOURCE_SYSTEM")
        if len(source_system) > 80:
            raise ConfigurationError(
                "IMPORT_SOURCE_SYSTEM must contain at most 80 characters"
            )

        log_level = optional_env("LOG_LEVEL", "INFO").upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ConfigurationError(f"Unsupported LOG_LEVEL: {log_level}")

        csv_delimiter = optional_env("IMPORT_CSV_DELIMITER", ",")
        if len(csv_delimiter) != 1:
            raise ConfigurationError(
                "IMPORT_CSV_DELIMITER must contain exactly one character"
            )

        return cls(
            database_url=require_env("DATABASE_URL"),
            input_directory=input_directory,
            source_system=source_system,
            sites_file=optional_env("IMPORT_SITES_FILE", "sites.csv"),
            products_file=optional_env("IMPORT_PRODUCTS_FILE", "products.csv"),
            production_orders_file=optional_env(
                "IMPORT_PRODUCTION_ORDERS_FILE",
                "production_orders.csv",
            ),
            quality_controls_file=optional_env(
                "IMPORT_QUALITY_CONTROLS_FILE",
                "quality_controls.xml",
            ),
            quality_control_record_tag=optional_env(
                "IMPORT_QUALITY_CONTROL_RECORD_TAG",
                "quality_control",
            ),
            csv_delimiter=csv_delimiter,
            log_level=log_level,
            database_connect_timeout_seconds=positive_int_env(
                "DATABASE_CONNECT_TIMEOUT_SECONDS", 10
            ),
            database_application_name=optional_env(
                "DATABASE_APPLICATION_NAME",
                "industrial-analytics-importer",
            ),
            batch_size=positive_int_env("IMPORT_BATCH_SIZE", 500),
            max_error_details=positive_int_env("IMPORT_MAX_ERROR_DETAILS", 20),
        )

    def source_files(self) -> tuple[SourceFile, ...]:
        return (
            SourceFile(Dataset.SITES, self.input_directory / self.sites_file),
            SourceFile(Dataset.PRODUCTS, self.input_directory / self.products_file),
            SourceFile(
                Dataset.PRODUCTION_ORDERS,
                self.input_directory / self.production_orders_file,
            ),
            SourceFile(
                Dataset.QUALITY_CONTROLS,
                self.input_directory / self.quality_controls_file,
                self.quality_control_record_tag,
            ),
        )
