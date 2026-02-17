import sys
import structlog
import logging

def configure_logging(level: str = "INFO", json_format: bool = False):
    """
    Configures structured logging for the NvsN framework.

    Args:
        level: Logging level (DEBUG, INFO, WARN, ERROR)
        json_format: Whether to output logs in JSON format (for production)
    """

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        processors = shared_processors + [
            structlog.processors.JSONRenderer()
        ]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer()
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    # Redirect standard logging to structlog
    # for log_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
    #     logging.getLogger(log_name).handlers = []
    #     logging.getLogger(log_name).propagate = True

    return structlog.get_logger()
