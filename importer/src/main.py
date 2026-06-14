import logging
import sys

import psycopg

from .config import Config, ConfigurationError
from .database import ImportRepository
from .logging_config import configure_logging
from .service import ImportService

LOGGER = logging.getLogger(__name__)


def run() -> int:
    try:
        config = Config.from_env()
    except ConfigurationError as error:
        configure_logging("INFO")
        LOGGER.error(
            "Invalid importer configuration",
            extra={"event": "configuration_error", "error": str(error)},
        )
        return 2

    configure_logging(config.log_level)

    try:
        with psycopg.connect(
            config.database_url,
            connect_timeout=config.database_connect_timeout_seconds,
            application_name=config.database_application_name,
        ) as connection:
            service = ImportService(config, ImportRepository(connection))
            summary = service.run()
    except psycopg.Error:
        LOGGER.exception(
            "Database connection failed",
            extra={"event": "database_connection_failed"},
        )
        return 1
    except Exception:
        LOGGER.exception(
            "Unexpected importer failure",
            extra={"event": "importer_failed"},
        )
        return 1

    LOGGER.info(
        "Import run completed",
        extra={
            "event": "import_run_completed",
            "files_total": summary.files_total,
            "files_failed": summary.files_failed,
            "rows_received": summary.rows_received,
            "rows_processed": summary.rows_processed,
            "rows_rejected": summary.rows_rejected,
        },
    )
    return 1 if summary.files_failed else 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
