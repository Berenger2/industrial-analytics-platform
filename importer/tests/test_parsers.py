import tempfile
import unittest
from pathlib import Path

from src.parsers import SourceFormatError, parse_csv, parse_xml


class ParserTests(unittest.TestCase):
    def test_parse_csv_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "metrics.csv")
            path.write_text(
                "machine_id,site,metric_name,metric_value,unit,recorded_at\n"
                " press-01 , Lyon , Temperature , 42.5 , C ,"
                "2026-01-01T10:00:00Z\n",
                encoding="utf-8",
            )

            rows = list(parse_csv(path, ","))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].location, "line 2")
        self.assertEqual(rows[0].values["machine_id"], " press-01 ")

    def test_parse_xml_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "metrics.xml")
            path.write_text(
                """
                <production_metrics>
                  <record>
                    <machine_id>PUMP-01</machine_id>
                    <site>Lyon</site>
                  </record>
                </production_metrics>
                """,
                encoding="utf-8",
            )

            rows = list(parse_xml(path, "record"))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].values["machine_id"], "PUMP-01")

    def test_rejects_xml_without_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "metrics.xml")
            path.write_text("<production_metrics />", encoding="utf-8")

            with self.assertRaises(SourceFormatError):
                list(parse_xml(path, "record"))


if __name__ == "__main__":
    unittest.main()
