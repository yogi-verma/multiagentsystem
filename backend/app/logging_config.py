import contextvars
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Level colors
    DEBUG = "\033[36m"      # Cyan
    INFO = "\033[32m"       # Green
    WARNING = "\033[33m"    # Yellow
    ERROR = "\033[31m"      # Red
    CRITICAL = "\033[35m"   # Magenta
    
    # Component colors
    TIMESTAMP = "\033[90m"  # Gray
    LOGGER = "\033[94m"     # Blue
    SESSION = "\033[96m"    # Bright Cyan
    AGENT = "\033[95m"      # Bright Magenta
    ROUTE = "\033[93m"      # Bright Yellow
    
_log_context: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    "log_context", default={}
)

LOG_FILE = os.getenv("LOG_FILE", "multi-agent-starter.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_HANDLERS = [
    item.strip()
    for item in os.getenv("LOG_HANDLERS", "console,file").split(",")
    if item.strip()
]
LOG_FORMAT_JSON = os.getenv("LOG_FORMAT_JSON", "false").lower() == "true"
MAX_LOG_SIZE = int(os.getenv("MAX_LOG_SIZE", str(10 * 1024 * 1024)))
BACKUP_COUNT = int(os.getenv("BACKUP_COUNT", "3"))


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        context = _log_context.get()
        payload: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "session_id": context.get("session_id", "-"),
            "transaction_id": context.get("transaction_id", "-"),
            "agent_type": context.get("agent_type", "-"),
            "user_id": context.get("user_id", "-"),
            "route": context.get("route", "-"),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        excluded_fields = {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "thread",
            "threadName",
            "exc_info",
            "exc_text",
            "stack_info",
            "session_id",
            "transaction_id",
            "agent_type",
            "user_id",
            "route",
        }

        for key, value in record.__dict__.items():
            if key not in excluded_fields and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload)
    

class ContextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        context = _log_context.get()
        record.session_id = context.get("session_id", "-")
        record.transaction_id = context.get("transaction_id", "-")
        record.agent_type = context.get("agent_type", "-")
        record.user_id = context.get("user_id", "-")
        record.route = context.get("route", "-")
        return super().format(record)
    

class ColoredFormatter(ContextFormatter):
    """Colored formatter for console output"""
    
    LEVEL_COLORS = {
        'DEBUG': Colors.DEBUG,
        'INFO': Colors.INFO,
        'WARNING': Colors.WARNING,
        'ERROR': Colors.ERROR,
        'CRITICAL': Colors.CRITICAL,
    }
    
    def format(self, record: logging.LogRecord) -> str:
        context = _log_context.get()
        record.session_id = context.get("session_id", "-")
        record.transaction_id = context.get("transaction_id", "-")
        record.agent_type = context.get("agent_type", "-")
        record.user_id = context.get("user_id", "-")
        record.route = context.get("route", "-")
        
        level_color = self.LEVEL_COLORS.get(record.levelname, Colors.RESET)
        
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        colored_timestamp = f"{Colors.TIMESTAMP}{timestamp}{Colors.RESET}"
        
        colored_level = f"{level_color}{record.levelname:<8}{Colors.RESET}"
        
        colored_logger = f"{Colors.LOGGER}{record.name}{Colors.RESET}"
        
        session_short = record.session_id[:8] if record.session_id != "-" else "-"
        txn_short = record.transaction_id[:8] if record.transaction_id != "-" else "-"
        
        colored_context = (
            f"[{Colors.SESSION}session={session_short}{Colors.RESET}] "
            f"[{Colors.SESSION}txn={txn_short}{Colors.RESET}] "
            f"[{Colors.AGENT}agent={record.agent_type}{Colors.RESET}] "
            f"[user={record.user_id}] "
            f"[{Colors.ROUTE}route={record.route}{Colors.RESET}]"
        )
        
        message = record.getMessage()
        
        log_line = (
            f"{colored_timestamp} - {colored_level} - "
            f"[{record.filename}:{record.lineno}] - {colored_logger} - "
            f"{colored_context} - {message}"
        )
        
        if record.exc_info:
            log_line += "\n" + self.formatException(record.exc_info)
        
        return log_line
    
    
class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        context = _log_context.get()
        record.session_id = context.get("session_id", "-")
        record.transaction_id = context.get("transaction_id", "-")
        record.agent_type = context.get("agent_type", "-")
        record.user_id = context.get("user_id", "-")
        record.route = context.get("route", "-")
        return True


def set_log_context(
    thread_id: str,
    agent_type: Optional[str] = None,
    user_id: Optional[str] = None,
    route: Optional[str] = None,
) -> None:
    context: Dict[str, Any] = {
        "session_id": thread_id,
        "transaction_id": str(uuid.uuid4()),
    }
    if agent_type:
        context["agent_type"] = agent_type
    if user_id:
        context["user_id"] = user_id
    if route:
        context["route"] = route
    _log_context.set(context)
    
def update_log_context(**kwargs: Any) -> None:
    current_context = _log_context.get().copy()
    current_context.update(kwargs)
    _log_context.set(current_context)
    
def clear_log_context() -> None:
    _log_context.set({})


def _get_log_level() -> int:
    try:
        return getattr(logging, LOG_LEVEL.upper())
    except AttributeError:
        return logging.INFO


def _create_file_handler(formatter: logging.Formatter) -> logging.Handler:
    os.makedirs("logs", exist_ok=True)
    handler = RotatingFileHandler(
        os.path.join("logs", LOG_FILE),
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
    )
    handler.setFormatter(formatter)
    return handler

def configure_root_logger() -> logging.Logger:
    root_logger = logging.getLogger()
    root_logger.setLevel(_get_log_level())

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    for current_filter in root_logger.filters[:]:
        root_logger.removeFilter(current_filter)

    root_logger.addFilter(ContextFilter())

    formatter: logging.Formatter
    if LOG_FORMAT_JSON:
        formatter = JSONFormatter()
    else:
        formatter = ContextFormatter(
            "%(asctime)s - %(levelname)-8s - [%(filename)s:%(lineno)d] - %(name)s - "
            "[session=%(session_id)s] [txn=%(transaction_id)s] [agent=%(agent_type)s] "
            "[user=%(user_id)s] [route=%(route)s] - %(message)s"
        )

    if "file" in LOG_HANDLERS:
        root_logger.addHandler(_create_file_handler(formatter))

    if "console" in LOG_HANDLERS:
        console_handler = logging.StreamHandler(sys.stdout)
        # Use colored formatter for console, regular formatter for file
        if sys.stdout.isatty() and not LOG_FORMAT_JSON:
            console_formatter = ColoredFormatter(
                "%(asctime)s - %(levelname)-8s - [%(filename)s:%(lineno)d] - %(name)s - "
                "[session=%(session_id)s] [txn=%(transaction_id)s] [agent=%(agent_type)s] "
                "[user=%(user_id)s] [route=%(route)s] - %(message)s"
            )
            console_handler.setFormatter(console_formatter)
        else:
            console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    return root_logger

def configure_uvicorn_logging() -> bool:
    configure_root_logger()

    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        logger = logging.getLogger(logger_name)
        logger.propagate = True
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    return True
