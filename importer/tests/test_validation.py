import unittest
from datetime import UTC, datetime
from decimal import Decimal

from src.models import SourceRow
from src.validation import ValidationError, validate_metric


class ValidationTests(unittest.TestCase):
    def test_cleans_and_converts_metric(self) -> None:
        source = SourceRow(
            values={
                " machine_id ": " press-001 ",
                "site": " Lyon  North ",
                "metric_name": " Temperature ",
                "metric_value": "68,4",
                "unit": " Celsius ",
                "recorded_at": "2026-01-15T08:00:00Z",
            },
            location="line 2",
        )

        metric = validate_metric(source)

        self.assertEqual(metric.machine_id, "PRESS-001")
        self.assertEqual(metric.site, "Lyon North")
        self.assertEqual(metric.metric_name, "temperature")
        self.assertEqual(metric.metric_value, Decimal("68.4"))
        self.assertEqual(metric.unit, "celsius")
        self.assertEqual(
            metric.recorded_at,
            datetime(2026, 1, 15, 8, tzinfo=UTC),
        )

    def test_rejects_missing_required_field(self) -> None:
        source = SourceRow(
            values={"machine_id": "PRESS-001"},
            location="line 2",
        )

        with self.assertRaisesRegex(ValidationError, "missing required"):
            validate_metric(source)

    def test_rejects_timestamp_without_timezone(self) -> None:
        source = SourceRow(
            values={
                "machine_id": "PRESS-001",
                "site": "Lyon",
                "metric_name": "temperature",
                "metric_value": "68.4",
                "unit": "celsius",
                "recorded_at": "2026-01-15T08:00:00",
            },
            location="line 2",
        )

        with self.assertRaisesRegex(ValidationError, "timezone"):
            validate_metric(source)


if __name__ == "__main__":
    unittest.main()
