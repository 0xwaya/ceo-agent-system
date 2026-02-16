"""
Centralized Logging Module
Provides consistent logging across the multi-agent system
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, Any


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}" f"{record.levelname}" f"{self.COLORS['RESET']}"
            )
        return super().format(record)


class AgentLogger:
    """Enhanced logger for multi-agent system"""

    def __init__(
        self,
        name: str,
        log_file: Optional[str] = None,
        level: str = "INFO",
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5,
    ):
        """
        Initialize logger

        Args:
            name: Logger name (usually module name)
            log_file: Path to log file (optional)
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = ColoredFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler (if log_file specified)
        if log_file:
            # Create logs directory if it doesn't exist
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info, extra=kwargs)

    def critical(self, message: str, exc_info: bool = True, **kwargs):
        """Log critical message"""
        self.logger.critical(message, exc_info=exc_info, extra=kwargs)

    def agent_execution(self, agent_type: str, action: str, status: str = "started", **details):
        """
        Log agent execution with structured format

        Args:
            agent_type: Type of agent (branding, legal, etc.)
            action: Action being performed
            status: Status (started, completed, failed)
            details: Additional context
        """
        message = f"[AGENT:{agent_type.upper()}] {action} - Status: {status}"
        if details:
            message += f" | Details: {details}"

        if status == "failed":
            self.error(message)
        elif status == "completed":
            self.info(message)
        else:
            self.debug(message)

    def api_request(self, method: str, endpoint: str, status_code: int, duration_ms: float):
        """
        Log API request with performance metrics

        Args:
            method: HTTP method
            endpoint: API endpoint
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
        """
        level = "info" if status_code < 400 else "error"
        message = f"[API] {method} {endpoint} - {status_code} ({duration_ms:.2f}ms)"
        getattr(self, level)(message)

    def validation_error(self, field: str, value: Any, reason: str):
        """
        Log validation error

        Args:
            field: Field name that failed validation
            value: Value that failed
            reason: Reason for failure
        """
        self.warning(f"[VALIDATION] Field '{field}' failed: {reason} (value: {value})")

    def security_event(self, event_type: str, details: dict, severity: str = "warning"):
        """
        Log security-related events

        Args:
            event_type: Type of security event
            details: Event details
            severity: Severity level
        """
        message = f"[SECURITY:{event_type.upper()}] {details}"
        getattr(self, severity)(message)


def get_logger(name: str, log_file: Optional[str] = None) -> AgentLogger:
    """
    Get or create a logger instance

    Args:
        name: Logger name (usually __name__)
        log_file: Optional log file path

    Returns:
        AgentLogger instance
    """
    return AgentLogger(name=name, log_file=log_file or "logs/app.log", level="DEBUG")


# Create default loggers for common modules
app_logger = get_logger("app", "logs/app.log")
agent_logger = get_logger("agents", "logs/agents.log")
api_logger = get_logger("api", "logs/api.log")
