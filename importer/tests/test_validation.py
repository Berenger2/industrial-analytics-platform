import unittest
from datetime import UTC, date, datetime
from decimal import Decimal

from src.models import SourceRow
from src.validation import (
    ValidationError,
    validate_product,
    validate_production_order,
    validate_quality_control,
    validate_site,
)


def source(**values: str) -> SourceRow:
    return SourceRow(values=values, location="line 2")


class ValidationTests(unittest.TestCase):
    def test_validates_site(self) -> None:
        site = validate_site(
            source(
                site_code=" fr-lyo ",
                site_name=" Lyon  Manufacturing ",
                country_code="fr",
                city="Lyon",
                timezone="Europe/Paris",
                status="ACTIVE",
                commissioned_on="2014-09-15",
            )
        )

        self.assertEqual(site.site_code, "FR-LYO")
        self.assertEqual(site.site_name, "Lyon Manufacturing")
        self.assertEqual(site.commissioned_on, date(2014, 9, 15))

    def test_validates_product(self) -> None:
        product = validate_product(
            source(
                product_code="drv-x100",
                product_name="Variable Speed Drive",
                product_family="Industrial Drives",
                unit_of_measure=" Unit ",
                standard_cycle_time_seconds="84,5",
                target_scrap_rate="1.5",
                is_active="yes",
            )
        )

        self.assertEqual(product.product_code, "DRV-X100")
        self.assertEqual(product.standard_cycle_time_seconds, Decimal("84.5"))
        self.assertTrue(product.is_active)

    def test_validates_production_order(self) -> None:
        order = validate_production_order(
            source(
                order_number="po-001",
                site_code="fr-lyo",
                product_code="drv-x100",
                line_code="line-a",
                order_status="completed",
                planned_quantity="100",
                produced_quantity="98",
                rejected_quantity="2",
                planned_start_at="2026-05-01T06:00:00+02:00",
                planned_end_at="2026-05-01T14:00:00+02:00",
                actual_start_at="2026-05-01T06:05:00+02:00",
                actual_end_at="2026-05-01T13:50:00+02:00",
            )
        )

        self.assertEqual(order.order_number, "PO-001")
        self.assertEqual(order.planned_start_at, datetime(2026, 5, 1, 4, tzinfo=UTC))

    def test_validates_quality_control(self) -> None:
        control = validate_quality_control(
            source(
                control_reference="qc-001",
                order_number="po-001",
                controlled_at="2026-05-01T12:00:00Z",
                sample_size="20",
                passed_quantity="19",
                failed_quantity="1",
                result="warning",
                defect_category="Surface finish",
                inspector_name="Claire Bernard",
                notes="Review requested",
            )
        )

        self.assertEqual(control.control_reference, "QC-001")
        self.assertEqual(control.failed_quantity, 1)

    def test_rejects_missing_required_field(self) -> None:
        with self.assertRaisesRegex(ValidationError, "missing required"):
            validate_site(source(site_code="FR-LYO"))

    def test_rejects_inconsistent_production_quantities(self) -> None:
        with self.assertRaisesRegex(ValidationError, "rejected_quantity"):
            validate_production_order(
                source(
                    order_number="PO-001",
                    site_code="FR-LYO",
                    product_code="DRV-X100",
                    line_code="LINE-A",
                    order_status="completed",
                    planned_quantity="100",
                    produced_quantity="5",
                    rejected_quantity="6",
                    planned_start_at="2026-05-01T06:00:00Z",
                    planned_end_at="2026-05-01T14:00:00Z",
                )
            )

    def test_requires_defect_category_for_failed_units(self) -> None:
        with self.assertRaisesRegex(ValidationError, "defect_category"):
            validate_quality_control(
                source(
                    control_reference="QC-001",
                    order_number="PO-001",
                    controlled_at="2026-05-01T12:00:00Z",
                    sample_size="20",
                    passed_quantity="19",
                    failed_quantity="1",
                    result="warning",
                    inspector_name="Claire Bernard",
                )
            )


if __name__ == "__main__":
    unittest.main()
