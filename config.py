"""
Configuration Management - Centralized constants and settings

All configuration values, constants, and environment-based settings.
"""

import os
from enum import Enum
from pathlib import Path


# ============================================================================
# PROJECT PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"
LOGS_DIR = PROJECT_ROOT / "logs"


# ============================================================================
# APPLICATION SETTINGS
# ============================================================================


class Environment(Enum):
    """Application environment"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


APP_ENV = Environment(os.getenv("APP_ENV", "development"))
DEBUG_MODE = os.getenv("DEBUG", "False").lower() == "true" and APP_ENV != Environment.PRODUCTION
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")


# ============================================================================
# WEB SERVER CONFIGURATION
# ============================================================================

FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
FLASK_THREADED = True


# ============================================================================
# AI TOOLING CONFIGURATION
# ============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
OPENAI_CODEX_ENABLED = os.getenv("OPENAI_CODEX_ENABLED", "false").lower() == "true"
OPENAI_CODEX_MODEL = os.getenv("OPENAI_CODEX_MODEL", "gpt-5-codex")
OPENAI_CODEX_TIMEOUT_SECONDS = int(os.getenv("OPENAI_CODEX_TIMEOUT_SECONDS", "45"))


# ============================================================================
# BUDGET CONFIGURATION
# ============================================================================


class BudgetConfig:
    """Budget allocations for all agents"""

    # Total budget
    TOTAL_BUDGET = 4500.0

    # Individual agent budgets
    LEGAL_BUDGET = 500.0
    BRANDING_BUDGET = 150.0
    WEB_DEV_BUDGET = 500.0
    MARTECH_BUDGET = 200.0
    CONTENT_BUDGET = 150.0
    CAMPAIGNS_BUDGET = 3000.0

    # Budget thresholds
    CRITICAL_THRESHOLD = 0.1  # 10% remaining
    WARNING_THRESHOLD = 0.25  # 25% remaining

    @classmethod
    def get_agent_budget(cls, agent_type: str) -> float:
        """Get budget for specific agent type"""
        budget_map = {
            "legal": cls.LEGAL_BUDGET,
            "branding": cls.BRANDING_BUDGET,
            "web_dev": cls.WEB_DEV_BUDGET,
            "martech": cls.MARTECH_BUDGET,
            "content": cls.CONTENT_BUDGET,
            "campaigns": cls.CAMPAIGNS_BUDGET,
        }
        return budget_map.get(agent_type.lower(), 0.0)

    @classmethod
    def validate_total_budget(cls) -> bool:
        """Ensure individual budgets sum to total"""
        total = (
            cls.LEGAL_BUDGET
            + cls.BRANDING_BUDGET
            + cls.WEB_DEV_BUDGET
            + cls.MARTECH_BUDGET
            + cls.CONTENT_BUDGET
            + cls.CAMPAIGNS_BUDGET
        )
        return abs(total - cls.TOTAL_BUDGET) < 0.01


# ============================================================================
# AGENT CONFIGURATION
# ============================================================================


class AgentConfig:
    """Configuration for agent behavior"""

    # Execution timeouts (seconds)
    DEFAULT_TIMEOUT = 300  # 5 minutes
    LONG_RUNNING_TIMEOUT = 900  # 15 minutes

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

    # Task limits
    MAX_TASKS_PER_AGENT = 10
    MAX_CONCURRENT_AGENTS = 6

    # Knowledge base
    ENABLE_KNOWLEDGE_BASE = True
    KNOWLEDGE_CACHE_TTL = 3600  # 1 hour


# ============================================================================
# GUARD RAIL CONFIGURATION
# ============================================================================


class GuardRailConfig:
    """Guard rail enforcement settings"""

    # Enforcement levels
    STRICT_MODE = os.getenv("STRICT_MODE", "True").lower() == "true"

    # Domain boundaries
    ALLOWED_DOMAINS = [
        "digital_marketing",
        "branding",
        "web_development",
        "legal_compliance",
        "content_creation",
        "martech_tools",
    ]

    # Vendor restrictions
    NO_VENDOR_RECOMMENDATIONS = True
    NO_EXTERNAL_AGENCIES = True
    AI_EXECUTION_ONLY = True

    # Quality standards
    MIN_DELIVERABLES_COUNT = 3
    REQUIRE_IMPLEMENTATION_PLAN = True


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================


class LogConfig:
    """Logging settings"""

    # Log levels
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Log format
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    # Log files
    ENABLE_FILE_LOGGING = True
    LOG_FILE = LOGS_DIR / "agent_system.log"
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
    BACKUP_COUNT = 5

    # Console logging
    ENABLE_CONSOLE_LOGGING = True


# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================


class SecurityConfig:
    """Security settings"""

    # Authentication
    ENABLE_AUTH = os.getenv("ENABLE_AUTH", "False").lower() == "true"
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    TOKEN_EXPIRATION = 3600  # 1 hour

    # Rate limiting
    ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "True").lower() == "true"
    RATE_LIMIT_PER_MINUTE = 60
    RATE_LIMIT_PER_HOUR = 1000

    # Input validation
    MAX_INPUT_LENGTH = 10000
    ALLOWED_FILE_EXTENSIONS = {".txt", ".md", ".json", ".yaml", ".yml"}

    # CORS
    ENABLE_CORS = True
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")


# ============================================================================
# PERFORMANCE CONFIGURATION
# ============================================================================


class PerformanceConfig:
    """Performance and caching settings"""

    # Caching
    ENABLE_CACHING = True
    CACHE_TYPE = os.getenv("CACHE_TYPE", "simple")  # simple, redis, memcached
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes

    # Redis configuration (if used)
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))

    # Connection pooling
    MAX_CONNECTIONS = 100
    CONNECTION_TIMEOUT = 30


# ============================================================================
# DATABASE CONFIGURATION (Future)
# ============================================================================


class DatabaseConfig:
    """Database settings for future implementation"""

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///langraph.db")
    POOL_SIZE = 10
    MAX_OVERFLOW = 20
    POOL_TIMEOUT = 30
    ECHO_SQL = DEBUG_MODE


# ============================================================================
# FEATURE FLAGS
# ============================================================================


class FeatureFlags:
    """Feature toggles for gradual rollout"""

    ENABLE_ASYNC_AGENTS = os.getenv("ENABLE_ASYNC", "False").lower() == "true"
    ENABLE_WEBSOCKET = True
    ENABLE_TASK_QUEUE = False
    ENABLE_METRICS = os.getenv("ENABLE_METRICS", "False").lower() == "true"
    ENABLE_API_V2 = False


# ============================================================================
# CONSTANTS
# ============================================================================


class Constants:
    """General constants"""

    # Agent types
    AGENT_TYPES = ["branding", "web_dev", "legal", "martech", "content", "campaigns"]

    # Task priorities
    PRIORITY_CRITICAL = "critical"
    PRIORITY_HIGH = "high"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_LOW = "low"

    # Execution phases
    PHASE_ANALYSIS = "analysis"
    PHASE_PLANNING = "planning"
    PHASE_EXECUTION = "execution"
    PHASE_REVIEW = "review"
    PHASE_COMPLETION = "completion"

    # Status codes
    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"


# ============================================================================
# AGENT DOMAIN MAPPING
# ============================================================================

AGENT_DOMAIN_MAP = {
    "branding": "BRANDING",
    "web_development": "WEB_DEVELOPMENT",
    "legal": "LEGAL",
    "martech": "MARTECH",
    "content": "CONTENT",
    "campaigns": "CAMPAIGNS",
}

ALLOWED_AGENT_TYPES = list(AGENT_DOMAIN_MAP.keys())


# ============================================================================
# VALIDATION
# ============================================================================


def validate_configuration():
    """Validate configuration on startup"""
    errors = []

    # Check budget totals
    if not BudgetConfig.validate_total_budget():
        errors.append("Budget totals don't match individual allocations")

    # Check required directories
    for directory in [LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    # Check environment variables in production
    if APP_ENV == Environment.PRODUCTION:
        if SECRET_KEY == "dev-secret-key-change-in-production":
            errors.append("SECRET_KEY must be set in production")
        if DEBUG_MODE:
            errors.append("DEBUG must be False in production")

    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

    return True


# Auto-validate on import
validate_configuration()
