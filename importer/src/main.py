import csv
import logging
import os
from pathlib import Path

import psycopg

LOGGER = logging.getLogger(__name__)

INSERT_QUERY = """
    INSERT INTO analytics.production_metrics (
        machine_id,
        site,
        metric_name,
        metric_value,
        unit,
        recorded_at
    )
    VALUES (
        %(machine_id)s,
        %(site)s,
        %(metric_name)s,
        %(metric_value)s,
        %(unit)s,
        %(recorded_at)s
    )
    ON CONFLICT (machine_id, metric_name, recorded_at) DO NOTHING
"""


def read_rows(sample_file: Path) -> list[dict[str, str]]:
    with sample_file.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    database_url = os.environ["DATABASE_URL"]
    sample_file = Path(
        os.getenv("SAMPLE_FILE", "/data/samples/production_metrics.csv")
    )

    rows = read_rows(sample_file)
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(INSERT_QUERY, rows)
        connection.commit()

    LOGGER.info("Import terminé : %s ligne(s) analysée(s).", len(rows))


if __name__ == "__main__":
    main()
