import math
import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Mapping

from .models import ProductionMetric, SourceRow

REQUIRED_FIELDS = (
    "machine_id",
    "site",
    "metric_name",
    "metric_value",
    "unit",
    "recorded_at",
)


class ValidationError(ValueError):
    """Raised when a source row violates the import contract."""


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_keys(values: Mapping[str, str | None]) -> dict[str, str]:
    return {
        clean_text(key).lower(): clean_text(value)
        for key, value in values.items()
    }


def parse_decimal(value: str, field_name: str) -> Decimal:
    normalized = value.replace(",", ".")
    try:
        parsed = Decimal(normalized)
    except InvalidOperation as error:
        raise ValidationError(f"{field_name} must be numeric") from error
    if not math.isfinite(float(parsed)):
        raise ValidationError(f"{field_name} must be finite")
    return parsed


def parse_timestamp(value: str, field_name: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith(("Z", "z")) else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValidationError(
            f"{field_name} must be an ISO 8601 timestamp"
        ) from error
    if parsed.tzinfo is None:
        raise ValidationError(f"{field_name} must include a timezone")
    return parsed.astimezone(UTC)


def validate_metric(source_row: SourceRow) -> ProductionMetric:
    values = normalize_keys(source_row.values)
    missing_fields = [field for field in REQUIRED_FIELDS if not values.get(field)]
    if missing_fields:
        raise ValidationError(
            f"missing required field(s): {', '.join(missing_fields)}"
        )

    return ProductionMetric(
        machine_id=values["machine_id"].upper(),
        site=values["site"],
        metric_name=values["metric_name"].lower(),
        metric_value=parse_decimal(values["metric_value"], "metric_value"),
        unit=values["unit"].lower(),
        recorded_at=parse_timestamp(values["recorded_at"], "recorded_at"),
    )
