from __future__ import annotations

from datetime import datetime
import logging
import os
import sys

import structlog
from structlog.stdlib import BoundLogger
from structlog.types import EventDict, Processor

from utils.tracing import get_current_trace_ids

# Mkdir logs dir
os.makedirs("../logs", exist_ok=True)


def add_opentelemetry_ids(_, __, event_dict: EventDict) -> EventDict:
    """
    Fetches trace_id and span_id from the current OpenTelemetry span
    and adds them to the log event dictionary.
    """
    trace_id, span_id = get_current_trace_ids()
    if trace_id:
        event_dict["trace_id"] = trace_id
    if span_id:
        event_dict["span_id"] = span_id
    return event_dict


def add_custom_fields(_, __, event_dict: EventDict) -> EventDict:
    """
    Add the service name to the event dict
    """
    event_dict["service_name"] = "BE-PRE-PROCESSING"
    event_dict["level"] = event_dict.get("level", "")
    event_dict["trace_id"] = event_dict.get("trace_id", "")

    event_dict["client_ip"] = event_dict.get("http", {}).get("client_ip", "")
    event_dict["uri"] = event_dict.get("http", {}).get("uri", "")
    event_dict["status_code"] = event_dict.get("http", {}).get("status_code", "")
    event_dict["span_id"] = event_dict.get("span_id", "")

    event_dict["method"] = event_dict.get("http", {}).get("method", "")

    event_dict["exception"] = event_dict.get("exception", "")
    event_dict["msg_log"] = event_dict.get("event", "")
    event_dict["user_id"] = event_dict.get("user_id", "")
    event_dict["class"] = event_dict.get("logger", "")

    ########################################
    # Unknown field
    event_dict["error_code"] = event_dict.get("error_code", "")
    event_dict["query_string"] = event_dict.get("query_string", "")

    ########################################

    for key in ["logger", "http", "event", "request_id", "color_message"]:
        event_dict.pop(key, None)
    return event_dict


def setup_logging(json_logs: bool = False, log_level: str = "INFO"):
    """set-up logging for the application

    Args:
        json_logs (bool, optional): True if logs should be in JSON format. Defaults to False.
        log_level (str, optional): The log level to use. Defaults to "INFO".
    """

    shared_processors: list[Processor] = [
        add_opentelemetry_ids,
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso", key="@timestamp"),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S,%f", key="time"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.stdlib.ExtraAdder(),
        add_custom_fields,
        structlog.processors.StackInfoRenderer(),
    ]

    if json_logs:
        # We rename the `event` key to `message` only in JSON logs, as Datadog looks for the
        # `message` key but the pretty ConsoleRenderer looks for `event`
        # Format the exception only for JSON logs, as we want to pretty-print them when
        # using the ConsoleRenderer
        shared_processors.append(structlog.processors.format_exc_info)

    structlog.configure(
        processors=shared_processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        # cache_logger_on_first_use=True,
    )

    log_renderer: structlog.types.Processor
    if json_logs:
        log_renderer = structlog.processors.JSONRenderer()
    else:
        log_renderer = structlog.dev.ConsoleRenderer()

    formatter = structlog.stdlib.ProcessorFormatter(
        # These run ONLY on `logging` entries that do NOT originate within
        # structlog.
        foreign_pre_chain=shared_processors,
        # These run on ALL entries after the pre_chain is done.
        processors=[
            # Remove _record & _from_structlog.
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            log_renderer,
        ],
    )

    handler = logging.StreamHandler()
    # Use OUR `ProcessorFormatter` to format all `logging` entries.
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Log to console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Log to file
    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y%m%d-%H%M")
    file_handler = logging.FileHandler(f"../logs/{formatted_date}.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    # Add 2 logger to the main logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.setLevel(log_level.upper())

    for _log in ["uvicorn", "uvicorn.error"]:
        # Clear the log handlers for uvicorn loggers, and enable propagation
        # so the messages are caught by our root logger and formatted correctly
        # by structlog
        logging.getLogger(_log).handlers.clear()
        logging.getLogger(_log).propagate = True

    # Since we re-create the access logs ourselves, to add all information
    # in the structured log (see the `logging_middleware` in main.py), we clear
    # the handlers and prevent the logs to propagate to a logger higher up in the
    # hierarchy (effectively rendering them silent).
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False

    def handle_exception(exc_type, exc_value, exc_traceback):
        """
        Log any uncaught exception instead of letting it be printed by Python
        (but leave KeyboardInterrupt untouched to allow users to Ctrl+C to stop)
        See https://stackoverflow.com/a/16993115/3641865
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        root_logger.error(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = handle_exception


def get_logger(name: str) -> BoundLogger:
    """Get a logger with the given name

    Args:
        name (str): The name of the logger

    Returns:
        BoundLogger: The logger
    """

    return structlog.stdlib.get_logger(name)
