"""
Logging System - Centralized logging configuration

Professional logging with multiple handlers, formatters, and levels.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from config import LogConfig


# ============================================================================
# LOGGING SETUP
# ============================================================================


def setup_logging(
    name: Optional[str] = None, level: Optional[str] = None, log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Set up logging with console and file handlers

    Args:
        name: Logger name (defaults to root logger)
        level: Log level (defaults to config value)
        log_file: Log file path (defaults to config value)

    Returns:
        Configured logger
    """
    # Get or create logger
    logger = logging.getLogger(name or __name__)

    # Set level
    log_level = getattr(logging, level or LogConfig.LOG_LEVEL)
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(fmt=LogConfig.LOG_FORMAT, datefmt=LogConfig.DATE_FORMAT)

    # Console handler
    if LogConfig.ENABLE_CONSOLE_LOGGING:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if LogConfig.ENABLE_FILE_LOGGING:
        log_path = log_file or LogConfig.LOG_FILE
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path,
            maxBytes=LogConfig.MAX_LOG_SIZE,
            backupCount=LogConfig.BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


# ============================================================================
# SPECIALIZED LOGGERS
# ============================================================================


class AgentLogger:
    """Logger for agent-specific operations"""

    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.logger = setup_logging(f"agent.{agent_type}")

    def log_execution_start(self, task_description: str):
        """Log agent execution start"""
        self.logger.info(f"[{self.agent_type.upper()}] Starting execution: {task_description}")

    def log_execution_complete(self, duration: float, cost: float):
        """Log agent execution completion"""
        self.logger.info(
            f"[{self.agent_type.upper()}] Execution complete - "
            f"Duration: {duration:.2f}s, Cost: ${cost:.2f}"
        )

    def log_execution_error(self, error: str):
        """Log agent execution error"""
        self.logger.error(f"[{self.agent_type.upper()}] Execution failed: {error}")

    def log_deliverable(self, deliverable: str):
        """Log deliverable creation"""
        self.logger.info(f"[{self.agent_type.upper()}] Deliverable: {deliverable}")

    def log_budget_usage(self, amount: float, remaining: float):
        """Log budget usage"""
        self.logger.info(
            f"[{self.agent_type.upper()}] Budget used: ${amount:.2f}, "
            f"Remaining: ${remaining:.2f}"
        )

    def log_guard_rail_violation(self, violation: str):
        """Log guard rail violation"""
        self.logger.warning(f"[{self.agent_type.upper()}] Guard rail violation: {violation}")


class OrchestrationLogger:
    """Logger for orchestration operations"""

    def __init__(self):
        self.logger = setup_logging("orchestration")

    def log_orchestration_start(self, company_name: str):
        """Log orchestration start"""
        self.logger.info(f"Starting orchestration for: {company_name}")

    def log_phase_start(self, phase: str):
        """Log phase start"""
        self.logger.info(f"Phase started: {phase}")

    def log_phase_complete(self, phase: str, duration: float):
        """Log phase completion"""
        self.logger.info(f"Phase complete: {phase} (Duration: {duration:.2f}s)")

    def log_agent_deployment(self, agent_type: str):
        """Log agent deployment"""
        self.logger.info(f"Deploying agent: {agent_type}")

    def log_orchestration_complete(
        self, duration: float, total_cost: float, success_count: int, total_agents: int
    ):
        """Log orchestration completion"""
        self.logger.info(
            f"Orchestration complete - Duration: {duration:.2f}s, "
            f"Cost: ${total_cost:.2f}, Success: {success_count}/{total_agents}"
        )

    def log_orchestration_error(self, error: str):
        """Log orchestration error"""
        self.logger.error(f"Orchestration failed: {error}")


class APILogger:
    """Logger for API operations"""

    def __init__(self):
        self.logger = setup_logging("api")

    def log_request(self, method: str, endpoint: str, client_ip: str):
        """Log API request"""
        self.logger.info(f"{method} {endpoint} from {client_ip}")

    def log_response(self, endpoint: str, status_code: int, duration: float):
        """Log API response"""
        self.logger.info(f"{endpoint} -> {status_code} ({duration:.3f}s)")

    def log_error(self, endpoint: str, error: str):
        """Log API error"""
        self.logger.error(f"{endpoint} error: {error}")

    def log_rate_limit(self, client_ip: str):
        """Log rate limit hit"""
        self.logger.warning(f"Rate limit exceeded for {client_ip}")


class SecurityLogger:
    """Logger for security events"""

    def __init__(self):
        self.logger = setup_logging("security")

    def log_authentication_attempt(self, username: str, success: bool):
        """Log authentication attempt"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Authentication {status} for user: {username}")

    def log_authorization_failure(self, username: str, resource: str):
        """Log authorization failure"""
        self.logger.warning(f"Authorization denied for user '{username}' on resource '{resource}'")

    def log_invalid_input(self, endpoint: str, reason: str):
        """Log invalid input"""
        self.logger.warning(f"Invalid input on {endpoint}: {reason}")

    def log_suspicious_activity(self, description: str, client_ip: str):
        """Log suspicious activity"""
        self.logger.warning(f"Suspicious activity from {client_ip}: {description}")


class PerformanceLogger:
    """Logger for performance metrics"""

    def __init__(self):
        self.logger = setup_logging("performance")

    def log_slow_query(self, query: str, duration: float, threshold: float = 1.0):
        """Log slow database query"""
        if duration > threshold:
            self.logger.warning(f"Slow query ({duration:.2f}s > {threshold:.2f}s): {query}")

    def log_cache_hit(self, key: str):
        """Log cache hit"""
        self.logger.debug(f"Cache hit: {key}")

    def log_cache_miss(self, key: str):
        """Log cache miss"""
        self.logger.debug(f"Cache miss: {key}")

    def log_resource_usage(self, cpu_percent: float, memory_mb: float, active_connections: int):
        """Log system resource usage"""
        self.logger.info(
            f"Resources - CPU: {cpu_percent:.1f}%, Memory: {memory_mb:.1f}MB, "
            f"Connections: {active_connections}"
        )


# ============================================================================
# CONTEXT LOGGER
# ============================================================================


class ContextLogger:
    """Logger with automatic context injection"""

    def __init__(self, logger: logging.Logger, context: dict):
        self.logger = logger
        self.context = context

    def _format_message(self, message: str) -> str:
        """Add context to message"""
        context_str = " ".join(f"{k}={v}" for k, v in self.context.items())
        return f"[{context_str}] {message}"

    def debug(self, message: str):
        self.logger.debug(self._format_message(message))

    def info(self, message: str):
        self.logger.info(self._format_message(message))

    def warning(self, message: str):
        self.logger.warning(self._format_message(message))

    def error(self, message: str):
        self.logger.error(self._format_message(message))

    def critical(self, message: str):
        self.logger.critical(self._format_message(message))


# ============================================================================
# GLOBAL LOGGERS
# ============================================================================

# Main application logger
app_logger = setup_logging("app")

# Specialized loggers
orchestration_logger = OrchestrationLogger()
api_logger = APILogger()
security_logger = SecurityLogger()
performance_logger = PerformanceLogger()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_agent_logger(agent_type: str) -> AgentLogger:
    """Get logger for specific agent"""
    return AgentLogger(agent_type)


def log_exception(logger: logging.Logger, exception: Exception, context: Optional[str] = None):
    """
    Log exception with full traceback

    Args:
        logger: Logger instance
        exception: Exception to log
        context: Optional context description
    """
    message = f"Exception: {str(exception)}"
    if context:
        message = f"{context} - {message}"

    logger.exception(message)


def log_startup_info():
    """Log application startup information"""
    from config import APP_ENV, FLASK_PORT, BudgetConfig

    app_logger.info("=" * 80)
    app_logger.info("MULTI-AGENT SYSTEM STARTING")
    app_logger.info("=" * 80)
    app_logger.info(f"Environment: {APP_ENV.value}")
    app_logger.info(f"Port: {FLASK_PORT}")
    app_logger.info(f"Total Budget: ${BudgetConfig.TOTAL_BUDGET:,.2f}")
    app_logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    app_logger.info("=" * 80)


def log_shutdown_info():
    """Log application shutdown information"""
    app_logger.info("=" * 80)
    app_logger.info("MULTI-AGENT SYSTEM SHUTTING DOWN")
    app_logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    app_logger.info("=" * 80)


# ============================================================================
# INITIALIZATION
# ============================================================================

# Ensure log directory exists
LogConfig.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Set up root logger
logging.basicConfig(
    level=getattr(logging, LogConfig.LOG_LEVEL),
    format=LogConfig.LOG_FORMAT,
    datefmt=LogConfig.DATE_FORMAT,
)
