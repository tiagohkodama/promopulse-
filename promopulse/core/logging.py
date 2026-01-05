import logging
import sys

from .config import get_settings


def setup_logging() -> None:
    """
    Basic structured-ish logging setup.
    Includes a placeholder for correlation_id to be filled in later
    (e.g., with a logging.Filter or contextvar).
    """
    settings = get_settings()

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    log_format = (
        "%(asctime)s | %(levelname)s | %(name)s | "
        "correlation_id=%(correlation_id)s | %(message)s"
    )

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Ensure 'correlation_id' key always exists to avoid KeyError
    class CorrelationIdFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            if not hasattr(record, "correlation_id"):
                record.correlation_id = "-"
            return True

    root_logger = logging.getLogger()
    root_logger.addFilter(CorrelationIdFilter())

    # Optionally quiet noisy loggers later if needed
    logging.getLogger("uvicorn.error").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(log_level)
