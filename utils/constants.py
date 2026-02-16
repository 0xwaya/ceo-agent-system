"""
Application Constants
Centralized location for all hard-coded values
"""

import os
from typing import Dict, List


class AppConstants:
    """Application-wide constants"""

    # Server Configuration
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 5001))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "surfacecraft-ai-agents-2026-change-in-prod")

    # CORS Configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # Default Company Values
    DEFAULT_COMPANY_NAME = "Amazon Granite LLC"
    DEFAULT_DBA_NAME = "SURFACECRAFT STUDIO"
    DEFAULT_INDUSTRY = "Granite & Engineered Quartz Countertops"
    DEFAULT_LOCATION = "Cincinnati, Ohio"

    # Budget Configuration
    DEFAULT_BUDGET = 5000.0
    MIN_BUDGET = 1000.0
    MAX_BUDGET = 100000.0
    BUDGET_WARNING_THRESHOLD = 2000.0
    BUDGET_DANGER_THRESHOLD = 1000.0

    # Timeline Configuration
    DEFAULT_TIMELINE_DAYS = 90
    MIN_TIMELINE_DAYS = 30
    MAX_TIMELINE_DAYS = 365

    # Agent Configuration
    MAX_CONCURRENT_AGENTS = 6
    AGENT_TIMEOUT_SECONDS = 300
    MAX_TASKS_PER_AGENT = 10

    # Orchestration Configuration
    MAX_ORCHESTRATION_THREADS = 5
    ORCHESTRATION_TIMEOUT_SECONDS = 600
    DEMO_TASK_LIMIT = 3  # Deploy first 3 tasks in demo mode
    TASK_PROCESSING_DELAY = 1.0  # Seconds between task deployments

    # API Response Codes
    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    SERVER_ERROR = 500

    # State Phases
    PHASE_INITIALIZATION = "initialization"
    PHASE_ANALYSIS = "strategic_analysis"
    PHASE_DECOMPOSITION = "task_decomposition"
    PHASE_DEPLOYMENT = "agent_deployment"
    PHASE_EXECUTION = "execution"
    PHASE_MONITORING = "monitoring"
    PHASE_COMPLETION = "completion"

    # Agent Types
    AGENT_TYPES = [
        "branding",
        "web_development",
        "legal",
        "martech",
        "content",
        "campaigns",
        "security",
    ]

    # Agent Domain Mapping (for guard rails)
    AGENT_DOMAIN_MAP: Dict[str, str] = {
        "branding": "BRANDING",
        "web_development": "WEB_DEVELOPMENT",
        "legal": "LEGAL",
        "martech": "MARTECH",
        "content": "CONTENT",
        "campaigns": "CAMPAIGNS",
        "security": "SECURITY",
    }

    # Agent Icons
    AGENT_ICONS: Dict[str, str] = {
        "branding": "🎨",
        "web_development": "💻",
        "legal": "⚖️",
        "martech": "📊",
        "content": "✍️",
        "campaigns": "📱",
        "security": "🛡️",
    }

    # Default Strategic Objectives
    DEFAULT_OBJECTIVES: List[str] = [
        "Launch business with professional digital presence",
        "Build strong brand identity and market positioning",
        "Establish legal compliance and protection",
        "Implement scalable marketing technology",
        "Create compelling content strategy",
        "Execute data-driven advertising campaigns",
    ]

    # Log Retention
    LOG_RETENTION_DAYS = 30
    MAX_LOG_SIZE_MB = 100

    # Session Configuration
    SESSION_TIMEOUT_MINUTES = 30
    MAX_ACTIVE_SESSIONS = 50

    # Validation Patterns
    COMPANY_NAME_MIN_LENGTH = 1
    COMPANY_NAME_MAX_LENGTH = 200
    INDUSTRY_MIN_LENGTH = 3
    INDUSTRY_MAX_LENGTH = 100
    LOCATION_MIN_LENGTH = 3
    LOCATION_MAX_LENGTH = 100

    # SocketIO Configuration
    SOCKETIO_PING_TIMEOUT = 60
    SOCKETIO_PING_INTERVAL = 25
    SOCKETIO_MAX_HTTP_BUFFER_SIZE = 1000000

    # Error Messages
    ERROR_INVALID_REQUEST = "Invalid request data"
    ERROR_AGENT_NOT_FOUND = "Agent type not found"
    ERROR_BUDGET_EXCEEDED = "Budget limit exceeded"
    ERROR_TIMEOUT = "Operation timed out"
    ERROR_INTERNAL = "Internal server error"
    ERROR_UNAUTHORIZED = "Unauthorized access"

    # Success Messages
    MSG_ANALYSIS_COMPLETE = "Strategic analysis completed successfully"
    MSG_AGENT_DEPLOYED = "Agent deployed successfully"
    MSG_ORCHESTRATION_COMPLETE = "Orchestration completed successfully"
    MSG_TASK_ASSIGNED = "Task assigned to agent"

    @classmethod
    def get_agent_icon(cls, agent_type: str) -> str:
        """Get icon for agent type"""
        return cls.AGENT_ICONS.get(agent_type.lower(), "🤖")

    @classmethod
    def get_agent_domain(cls, agent_type: str) -> str:
        """Get domain name for agent type"""
        return cls.AGENT_DOMAIN_MAP.get(agent_type.lower(), agent_type.upper())

    @classmethod
    def is_valid_agent_type(cls, agent_type: str) -> bool:
        """Check if agent type is valid"""
        return agent_type.lower() in cls.AGENT_TYPES

    @classmethod
    def get_default_state_template(cls) -> dict:
        """Get default state template for CFO agent"""
        return {
            # Top-level company info
            "company_name": cls.DEFAULT_COMPANY_NAME,
            "industry": cls.DEFAULT_INDUSTRY,
            "location": cls.DEFAULT_LOCATION,
            # Strategic objectives
            "strategic_objectives": cls.DEFAULT_OBJECTIVES.copy(),
            # Budget management
            "total_budget": cls.DEFAULT_BUDGET,
            "budget_allocated": {},
            "budget_spent": {},
            "budget_remaining": cls.DEFAULT_BUDGET,
            # Timeline
            "target_completion_days": cls.DEFAULT_TIMELINE_DAYS,
            "current_day": 0,
            "milestones": [],
            # Multi-agent orchestration
            "active_agents": [],
            "agent_outputs": [],
            "agent_status": {},
            # Task breakdown
            "identified_tasks": [],
            "assigned_tasks": {},
            "completed_tasks": [],
            # Risk management
            "risks": [],
            "opportunities": [],
            # Deliverables
            "deliverables": [],
            "status_reports": [],
            "final_executive_summary": "",
            # Workflow
            "current_phase": cls.PHASE_INITIALIZATION,
            "completed_phases": [],
        }
