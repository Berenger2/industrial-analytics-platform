import json
import logging
from datetime import UTC, datetime
from typing import Any

STANDARD_ATTRIBUTES = frozenset(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(
            {
                key: value
                for key, value in record.__dict__.items()
                if key not in STANDARD_ATTRIBUTES
                and key not in {"message", "asctime"}
            }
        )
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True, default=str)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(
        level=level,
        handlers=[handler],
        force=True,
    )
