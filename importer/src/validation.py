import math
import re
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Mapping

from .models import Product, ProductionOrder, QualityControl, Site, SourceRow

SITE_STATUSES = frozenset({"active", "maintenance", "inactive"})
ORDER_STATUSES = frozenset(
    {"planned", "in_progress", "completed", "cancelled"}
)
QUALITY_RESULTS = frozenset({"passed", "warning", "failed"})


class ValidationError(ValueError):
    """Raised when a source row violates the import contract."""


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_keys(values: Mapping[str, str | None]) -> dict[str, str]:
    return {
        clean_text(key).lower(): clean_text(value)
        for key, value in values.items()
    }


def require_fields(values: Mapping[str, str], fields: tuple[str, ...]) -> None:
    missing = [field for field in fields if not values.get(field)]
    if missing:
        raise ValidationError(f"missing required field(s): {', '.join(missing)}")


def parse_decimal(value: str, field_name: str) -> Decimal:
    try:
        parsed = Decimal(value.replace(",", "."))
    except InvalidOperation as error:
        raise ValidationError(f"{field_name} must be numeric") from error
    if not math.isfinite(float(parsed)):
        raise ValidationError(f"{field_name} must be finite")
    return parsed


def parse_integer(value: str, field_name: str) -> int:
    try:
        return int(value)
    except ValueError as error:
        raise ValidationError(f"{field_name} must be an integer") from error


def parse_boolean(value: str, field_name: str) -> bool:
    normalized = value.lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ValidationError(f"{field_name} must be a boolean")


def parse_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValidationError(f"{field_name} must be an ISO 8601 date") from error


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


def optional_date(value: str, field_name: str) -> date | None:
    return parse_date(value, field_name) if value else None


def optional_timestamp(value: str, field_name: str) -> datetime | None:
    return parse_timestamp(value, field_name) if value else None


def optional_text(value: str) -> str | None:
    return value or None


def ensure_choice(value: str, field_name: str, choices: frozenset[str]) -> None:
    if value not in choices:
        raise ValidationError(
            f"{field_name} must be one of: {', '.join(sorted(choices))}"
        )


def validate_site(source_row: SourceRow) -> Site:
    values = normalize_keys(source_row.values)
    require_fields(
        values,
        ("site_code", "site_name", "country_code", "city", "timezone", "status"),
    )
    status = values["status"].lower()
    country_code = values["country_code"].upper()
    ensure_choice(status, "status", SITE_STATUSES)
    if not re.fullmatch(r"[A-Z]{2}", country_code):
        raise ValidationError("country_code must contain two uppercase letters")
    return Site(
        site_code=values["site_code"].upper(),
        site_name=values["site_name"],
        country_code=country_code,
        city=values["city"],
        timezone=values["timezone"],
        status=status,
        commissioned_on=optional_date(
            values.get("commissioned_on", ""),
            "commissioned_on",
        ),
    )


def validate_product(source_row: SourceRow) -> Product:
    values = normalize_keys(source_row.values)
    require_fields(
        values,
        (
            "product_code",
            "product_name",
            "product_family",
            "unit_of_measure",
            "standard_cycle_time_seconds",
            "target_scrap_rate",
            "is_active",
        ),
    )
    cycle_time = parse_decimal(
        values["standard_cycle_time_seconds"],
        "standard_cycle_time_seconds",
    )
    scrap_rate = parse_decimal(values["target_scrap_rate"], "target_scrap_rate")
    if cycle_time <= 0:
        raise ValidationError("standard_cycle_time_seconds must be greater than zero")
    if not Decimal("0") <= scrap_rate <= Decimal("100"):
        raise ValidationError("target_scrap_rate must be between 0 and 100")
    return Product(
        product_code=values["product_code"].upper(),
        product_name=values["product_name"],
        product_family=values["product_family"],
        unit_of_measure=values["unit_of_measure"].lower(),
        standard_cycle_time_seconds=cycle_time,
        target_scrap_rate=scrap_rate,
        is_active=parse_boolean(values["is_active"], "is_active"),
    )


def validate_production_order(source_row: SourceRow) -> ProductionOrder:
    values = normalize_keys(source_row.values)
    require_fields(
        values,
        (
            "order_number",
            "site_code",
            "product_code",
            "line_code",
            "order_status",
            "planned_quantity",
            "produced_quantity",
            "rejected_quantity",
            "planned_start_at",
            "planned_end_at",
        ),
    )
    status = values["order_status"].lower()
    ensure_choice(status, "order_status", ORDER_STATUSES)
    planned_quantity = parse_integer(values["planned_quantity"], "planned_quantity")
    produced_quantity = parse_integer(
        values["produced_quantity"], "produced_quantity"
    )
    rejected_quantity = parse_integer(
        values["rejected_quantity"], "rejected_quantity"
    )
    planned_start = parse_timestamp(values["planned_start_at"], "planned_start_at")
    planned_end = parse_timestamp(values["planned_end_at"], "planned_end_at")
    actual_start = optional_timestamp(
        values.get("actual_start_at", ""), "actual_start_at"
    )
    actual_end = optional_timestamp(values.get("actual_end_at", ""), "actual_end_at")
    if planned_quantity <= 0:
        raise ValidationError("planned_quantity must be greater than zero")
    if produced_quantity < 0:
        raise ValidationError("produced_quantity must be zero or greater")
    if not 0 <= rejected_quantity <= produced_quantity:
        raise ValidationError(
            "rejected_quantity must be between zero and produced_quantity"
        )
    if planned_end <= planned_start:
        raise ValidationError("planned_end_at must be after planned_start_at")
    if actual_end is not None and (
        actual_start is None or actual_end < actual_start
    ):
        raise ValidationError(
            "actual_end_at requires actual_start_at and cannot precede it"
        )
    return ProductionOrder(
        order_number=values["order_number"].upper(),
        site_code=values["site_code"].upper(),
        product_code=values["product_code"].upper(),
        line_code=values["line_code"].upper(),
        order_status=status,
        planned_quantity=planned_quantity,
        produced_quantity=produced_quantity,
        rejected_quantity=rejected_quantity,
        planned_start_at=planned_start,
        planned_end_at=planned_end,
        actual_start_at=actual_start,
        actual_end_at=actual_end,
    )


def validate_quality_control(source_row: SourceRow) -> QualityControl:
    values = normalize_keys(source_row.values)
    require_fields(
        values,
        (
            "control_reference",
            "order_number",
            "controlled_at",
            "sample_size",
            "passed_quantity",
            "failed_quantity",
            "result",
            "inspector_name",
        ),
    )
    result = values["result"].lower()
    ensure_choice(result, "result", QUALITY_RESULTS)
    sample_size = parse_integer(values["sample_size"], "sample_size")
    passed_quantity = parse_integer(values["passed_quantity"], "passed_quantity")
    failed_quantity = parse_integer(values["failed_quantity"], "failed_quantity")
    defect_category = optional_text(values.get("defect_category", ""))
    if sample_size <= 0:
        raise ValidationError("sample_size must be greater than zero")
    if passed_quantity < 0 or failed_quantity < 0:
        raise ValidationError("quality quantities must be zero or greater")
    if passed_quantity + failed_quantity > sample_size:
        raise ValidationError(
            "passed_quantity plus failed_quantity cannot exceed sample_size"
        )
    if failed_quantity > 0 and defect_category is None:
        raise ValidationError(
            "defect_category is required when failed_quantity is greater than zero"
        )
    return QualityControl(
        control_reference=values["control_reference"].upper(),
        order_number=values["order_number"].upper(),
        controlled_at=parse_timestamp(values["controlled_at"], "controlled_at"),
        sample_size=sample_size,
        passed_quantity=passed_quantity,
        failed_quantity=failed_quantity,
        result=result,
        defect_category=defect_category,
        inspector_name=values["inspector_name"],
        notes=optional_text(values.get("notes", "")),
    )
