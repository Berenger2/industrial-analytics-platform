import tempfile
import unittest
from pathlib import Path

from src.parsers import SourceFormatError, parse_csv, parse_file, parse_xml


class ParserTests(unittest.TestCase):
    def test_parse_csv_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sites.csv")
            path.write_text(
                "site_code,site_name\n FR-LYO , Lyon Manufacturing \n",
                encoding="utf-8",
            )

            rows = list(parse_csv(path, ","))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].location, "line 2")
        self.assertEqual(rows[0].values["site_code"], " FR-LYO ")

    def test_parse_quality_control_xml_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "quality_controls.xml")
            path.write_text(
                """
                <quality_controls>
                  <quality_control>
                    <control_reference>QC-001</control_reference>
                    <order_number>PO-001</order_number>
                  </quality_control>
                </quality_controls>
                """,
                encoding="utf-8",
            )

            rows = list(parse_xml(path, "quality_control"))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].values["control_reference"], "QC-001")

    def test_rejects_xml_without_configured_tag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "quality_controls.xml")
            path.write_text("<quality_controls />", encoding="utf-8")

            with self.assertRaises(SourceFormatError):
                list(parse_file(path, None, ","))

    def test_rejects_xml_without_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "quality_controls.xml")
            path.write_text("<quality_controls />", encoding="utf-8")

            with self.assertRaises(SourceFormatError):
                list(parse_xml(path, "quality_control"))


if __name__ == "__main__":
    unittest.main()
