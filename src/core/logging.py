import json
import logging
import sys
from datetime import UTC, datetime

from src.config import settings

# Attributes every LogRecord carries by default; anything else on a record is
# a structured extra passed via `extra={...}` and gets merged into the output.
_RESERVED_ATTRS = frozenset(vars(logging.makeLogRecord({}))) | {"message", "asctime"}


class _JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for container environments."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_ATTRS and key not in entry:
                entry[key] = value
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        if record.stack_info:
            entry["stack"] = self.formatStack(record.stack_info)
        return json.dumps(entry, ensure_ascii=False, default=str)


def _root_level() -> int:
    if settings.environment == "production":
        return logging.WARNING
    if settings.environment == "staging":
        return logging.INFO
    return logging.DEBUG  # development / local


def _use_json() -> bool:
    return settings.environment in ("production", "staging")


def setup_logging() -> None:
    root_level = _root_level()
    handler = logging.StreamHandler(sys.stdout)

    if _use_json():
        handler.setFormatter(_JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    logging.basicConfig(level=root_level, handlers=[handler])

    # basicConfig is a no-op if the root logger already has handlers (e.g. when
    # uvicorn or pytest configured it first), so set the level explicitly.
    logging.getLogger().setLevel(root_level)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
