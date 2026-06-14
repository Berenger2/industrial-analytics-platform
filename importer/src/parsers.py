import csv
from collections.abc import Iterator
from pathlib import Path
from xml.etree.ElementTree import ParseError

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from .models import SourceRow


class UnsupportedFileError(ValueError):
    """Raised when no parser supports a source file."""


class SourceFormatError(ValueError):
    """Raised when a source file cannot be parsed."""


def parse_file(
    path: Path,
    xml_record_tag: str | None,
    csv_delimiter: str,
) -> Iterator[SourceRow]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        yield from parse_csv(path, csv_delimiter)
        return
    if suffix == ".xml":
        if not xml_record_tag:
            raise SourceFormatError("XML record tag is not configured")
        yield from parse_xml(path, xml_record_tag)
        return
    raise UnsupportedFileError(f"Unsupported file extension: {path.suffix}")


def parse_csv(path: Path, delimiter: str) -> Iterator[SourceRow]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source, delimiter=delimiter)
            if not reader.fieldnames:
                raise SourceFormatError("CSV header is missing")
            for line_number, values in enumerate(reader, start=2):
                if None in values:
                    raise SourceFormatError(
                        f"CSV line {line_number} has more values than columns"
                    )
                yield SourceRow(values=values, location=f"line {line_number}")
    except (OSError, UnicodeError, csv.Error) as error:
        raise SourceFormatError(str(error)) from error


def parse_xml(path: Path, record_tag: str) -> Iterator[SourceRow]:
    try:
        root = ElementTree.parse(path).getroot()
    except (OSError, ParseError, DefusedXmlException) as error:
        raise SourceFormatError(str(error)) from error

    records = root.findall(f".//{record_tag}")
    if root.tag == record_tag:
        records.insert(0, root)
    if not records:
        raise SourceFormatError(f"XML contains no <{record_tag}> elements")

    for position, record in enumerate(records, start=1):
        values = {
            child.tag: child.text
            for child in record
            if len(child) == 0
        }
        yield SourceRow(values=values, location=f"{record_tag} {position}")
