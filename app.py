#!/usr/bin/env python3
"""
CEO Agent - Executive AI System
Flask backend serving admin dashboard and multi-agent orchestration
"""

from flask import Flask, render_template, jsonify, request, session, g
from flask_socketio import SocketIO, emit
import json
import os
import uuid
import copy
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import threading
import time
import traceback
from functools import wraps

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def bootstrap_environment() -> None:
    """Load environment variables from .env or encrypted env files."""
    project_root = Path(__file__).resolve().parent
    env_path = project_root / ".env"
    encrypted_path = project_root / ".env.encrypted"
    key_path = project_root / ".env.key"

    if load_dotenv:
        load_dotenv(dotenv_path=env_path, override=False)

    if env_path.exists() or not (encrypted_path.exists() and key_path.exists()):
        return

    try:
        from tools.encrypted_env_demo import EncryptedEnvManager

        manager = EncryptedEnvManager(project_root=project_root)
        manager.load_env(decrypt_first=True)

        if load_dotenv and env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)

        print("✅ Loaded environment from encrypted configuration")
    except Exception as e:
        print(f"⚠️ Could not load encrypted environment: {e}")


bootstrap_environment()

# Import agent systems - CEO Agent (new architecture)
try:
    from agents.ceo_agent import (
        CEOAgentState,
        analyze_strategic_objectives as ceo_analyze,
    )
    from agents.new_cfo_agent import (
        CFOAgentState as NewCFOState,
        generate_financial_report,
    )

    CEO_AGENT_AVAILABLE = True
except ImportError:
    CEO_AGENT_AVAILABLE = False
    print("⚠️ CEO/CFO agents not available, using fallback")

# Import LangGraph multi-agent system
try:
    from graph_architecture.main_graph import execute_multi_agent_system
    from graph_architecture.schemas import SharedState

    GRAPH_ARCHITECTURE_AVAILABLE = True
    print("✅ Graph architecture loaded successfully")
except ImportError as e:
    GRAPH_ARCHITECTURE_AVAILABLE = False
    print(f"⚠️ Graph architecture not available: {e}")

from agents.specialized_agents import AgentFactory
from agents.agent_guard_rails import (
    AgentGuardRail,
    AgentDomain,
    create_execution_summary,
)
from services.artifact_service import artifact_service

# Import utilities
try:
    from utils.logger import get_logger, app_logger, api_logger
    from utils.validators import (
        validate_company_info,
        validate_agent_request,
        sanitize_input,
        sanitize_dict,
        validate_chat_message,
        scan_payload_for_threats,
        validate_payload_allowlist,
        validate_company_info_allowlist,
    )

    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
    print("⚠️ Warning: Utils modules not available, using basic logging")

app = Flask(__name__)
# SECRET_KEY is loaded and validated at import time in config.py
try:
    from config import SECRET_KEY as _APP_SECRET_KEY
except Exception:
    _APP_SECRET_KEY = os.getenv("SECRET_KEY", "")
app.config["SECRET_KEY"] = _APP_SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB max request size
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Global state for admin dashboard
pending_approvals = []
system_settings = {
    "system_mode": "training",
    "auto_approve_api": True,
    "email_notifications": False,
    "total_budget": 50000,
    "cfo_api_limit": 100,
    "cfo_legal_limit": 500,
}

# Initialize logger
if UTILS_AVAILABLE:
    logger = get_logger("app", "logs/app.log")
else:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("app")

# Store active sessions and agent states
active_sessions = {}


shared_state_lock = threading.Lock()
SCENARIO_SCHEMA_VERSION = 1
DEV_SCENARIO_DEFAULTS_VERSION = "2026-02-15-dev-v1"
PROD_SCENARIO_DEFAULTS_VERSION = "2026-02-15-prod-v1"

DEFAULT_DEV_OBJECTIVES = [
    "Launch AR platform showroom",
    "Relaunch the company brand as SurfaceCraft Studio",
    "Create a brand kit to be use across platforms",
    "Create and maintain social media accounts and content creation",
    "Possition the company in the highend exclusive market",
    "Create all necessary agent to execute and manage customer caption and retention",
    "Create sales agent to target residential and commercial contracts",
    "Register as a minority business with the city of Cincinnati",
    "Automate most processes that deals with outside sales",
]

DEFAULT_DEV_SCENARIO = {
    "company_name": "Amazon Granite LLC",
    "dba_name": "SurfaceCraft Studio",
    "industry": "Construction, Custom Countertops",
    "location": "Cincinnati, OH",
    "budget": 1000.0,
    "timeline": 30,
    "objectives": DEFAULT_DEV_OBJECTIVES,
}

LEGACY_OBJECTIVE_MARKERS = {
    "Launch SaaS platform",
    "Build enterprise sales team",
    "Establish market presence",
    "Scale to $1M ARR",
}


def _is_production_environment() -> bool:
    return os.getenv("ENVIRONMENT", "development").lower() == "production"


def _scenario_defaults_version() -> str:
    return (
        PROD_SCENARIO_DEFAULTS_VERSION
        if _is_production_environment()
        else DEV_SCENARIO_DEFAULTS_VERSION
    )


def _get_default_scenario_for_environment() -> Dict[str, Any]:
    if _is_production_environment():
        return {
            "company_name": "",
            "dba_name": "",
            "industry": "",
            "location": "",
            "budget": 0.0,
            "timeline": 0,
            "objectives": [],
        }

    return {
        "company_name": DEFAULT_DEV_SCENARIO["company_name"],
        "dba_name": DEFAULT_DEV_SCENARIO["dba_name"],
        "industry": DEFAULT_DEV_SCENARIO["industry"],
        "location": DEFAULT_DEV_SCENARIO["location"],
        "budget": DEFAULT_DEV_SCENARIO["budget"],
        "timeline": DEFAULT_DEV_SCENARIO["timeline"],
        "objectives": list(DEFAULT_DEV_OBJECTIVES),
    }


def _attach_scenario_metadata(
    scenario: Dict[str, Any],
    source: str,
    user_modified: bool = False,
    migrated: bool = False,
    existing_meta: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    scenario_with_meta = copy.deepcopy(scenario)
    previous_meta = existing_meta if isinstance(existing_meta, dict) else {}

    scenario_with_meta["meta"] = {
        "schema_version": SCENARIO_SCHEMA_VERSION,
        "defaults_version": _scenario_defaults_version(),
        "environment": "production" if _is_production_environment() else "development",
        "source": source,
        "user_modified": bool(previous_meta.get("user_modified", False) or user_modified),
        "migrated": bool(migrated),
        "meta_updated_at": datetime.now().isoformat(),
    }
    return scenario_with_meta


def _has_stale_or_missing_metadata(meta: Dict[str, Any] | None) -> bool:
    if not isinstance(meta, dict):
        return True

    return (
        meta.get("schema_version") != SCENARIO_SCHEMA_VERSION
        or meta.get("defaults_version") != _scenario_defaults_version()
    )


def _looks_like_legacy_default_scenario(scenario: Dict[str, Any]) -> bool:
    marker_score = 0

    industry = str(scenario.get("industry") or "").strip()
    location = str(scenario.get("location") or "").strip()

    try:
        budget = float(scenario.get("budget"))
    except (TypeError, ValueError):
        budget = None

    try:
        timeline = int(scenario.get("timeline"))
    except (TypeError, ValueError):
        timeline = None

    objectives = scenario.get("objectives")
    objective_set = (
        {str(item).strip() for item in objectives if isinstance(item, str)}
        if isinstance(objectives, list)
        else set()
    )

    if industry in {
        "Software & Technology",
        "AI Technology",
        "Granite & Countertops",
        "General Business",
    }:
        marker_score += 1

    if location in {"San Francisco, CA", "United States", "Cincinnati, Ohio"}:
        marker_score += 1

    if budget in {5000.0, 100000.0}:
        marker_score += 1

    if timeline in {90}:
        marker_score += 1

    if objective_set.intersection(LEGACY_OBJECTIVE_MARKERS):
        marker_score += 1

    return marker_score >= 2


def _migrate_scenario_context_if_needed(
    scenario: Dict[str, Any] | None,
) -> tuple[Dict[str, Any], bool]:
    default_scenario = _get_default_scenario_for_environment()

    if not isinstance(scenario, dict):
        normalized_defaults = _normalize_scenario_context(
            default_scenario,
            default_scenario.get("objectives"),
        )
        migrated = _attach_scenario_metadata(
            normalized_defaults,
            source="migration_bootstrap",
            user_modified=False,
            migrated=True,
        )
        return migrated, True

    existing_meta = scenario.get("meta") if isinstance(scenario.get("meta"), dict) else {}
    is_stale = _has_stale_or_missing_metadata(existing_meta)
    user_modified = bool(existing_meta.get("user_modified", False))

    should_reset_to_defaults = False
    if is_stale:
        if _is_production_environment():
            should_reset_to_defaults = not user_modified
        else:
            should_reset_to_defaults = (not user_modified) and _looks_like_legacy_default_scenario(
                scenario
            )

    if should_reset_to_defaults:
        normalized = _normalize_scenario_context(
            default_scenario,
            default_scenario.get("objectives"),
        )
    else:
        normalized = _normalize_scenario_context(scenario, scenario.get("objectives"))

    migrated_scenario = _attach_scenario_metadata(
        normalized,
        source="migration" if is_stale else existing_meta.get("source", "system"),
        user_modified=(user_modified and not should_reset_to_defaults),
        migrated=is_stale,
        existing_meta=existing_meta,
    )

    return migrated_scenario, migrated_scenario != scenario


shared_runtime_state = {
    "scenario": {
        **_attach_scenario_metadata(
            {
                **_get_default_scenario_for_environment(),
                "updated_at": datetime.now().isoformat(),
            },
            source="startup_defaults",
            user_modified=False,
            migrated=False,
        ),
    },
    "last_orchestration_report": None,
}


def _normalize_scenario_context(
    company_info: Dict[str, Any] | None = None,
    objectives: list[str] | None = None,
) -> Dict[str, Any]:
    company_info = company_info or {}
    default_scenario = _get_default_scenario_for_environment()

    company_name = (
        company_info.get("company_name")
        or company_info.get("name")
        or default_scenario["company_name"]
    )
    dba_name = company_info.get("dba_name") or company_name
    industry = company_info.get("industry") or default_scenario["industry"]
    location = company_info.get("location") or default_scenario["location"]

    try:
        budget = float(company_info.get("budget", default_scenario["budget"]))
    except (TypeError, ValueError):
        budget = float(default_scenario["budget"])

    try:
        timeline = int(company_info.get("timeline", default_scenario["timeline"]))
    except (TypeError, ValueError):
        timeline = int(default_scenario["timeline"])

    safe_objectives = (
        objectives
        if isinstance(objectives, list) and objectives
        else list(default_scenario["objectives"])
    )

    return {
        "company_name": company_name,
        "dba_name": dba_name,
        "industry": industry,
        "location": location,
        "budget": budget,
        "timeline": timeline,
        "objectives": safe_objectives,
        "updated_at": datetime.now().isoformat(),
    }


def _update_shared_scenario_context(
    scenario: Dict[str, Any],
    source: str = "unknown",
    broadcast: bool = True,
    user_modified: bool = False,
) -> None:
    prepared_scenario = _attach_scenario_metadata(
        scenario,
        source=source,
        user_modified=user_modified,
        migrated=False,
        existing_meta=scenario.get("meta") if isinstance(scenario.get("meta"), dict) else None,
    )

    with shared_state_lock:
        shared_runtime_state["scenario"] = copy.deepcopy(prepared_scenario)

    if broadcast:
        socketio.emit(
            "scenario_updated",
            {
                "scenario": prepared_scenario,
                "source": source,
                "timestamp": datetime.now().isoformat(),
            },
            to=None,
        )


def _get_shared_scenario_context() -> Dict[str, Any]:
    with shared_state_lock:
        current_scenario = copy.deepcopy(shared_runtime_state["scenario"])

    migrated_scenario, changed = _migrate_scenario_context_if_needed(current_scenario)
    if changed:
        with shared_state_lock:
            shared_runtime_state["scenario"] = copy.deepcopy(migrated_scenario)

    return migrated_scenario


def _security_violation_response(findings: list[str], source: str):
    """Standard response for blocked malicious input."""
    if UTILS_AVAILABLE:
        logger.warning(f"Blocked malicious {source} payload", extra={"findings": findings})

    return (
        jsonify(
            {
                "success": False,
                "error": "Potentially malicious content detected",
                "details": findings,
            }
        ),
        400,
    )


def _allowlist_violation_response(errors: list[str], source: str):
    """Standard response for strict field allowlist violations."""
    if UTILS_AVAILABLE:
        logger.warning(f"Blocked invalid {source} payload", extra={"errors": errors})

    return (
        jsonify(
            {
                "success": False,
                "error": "Invalid request payload",
                "details": errors,
            }
        ),
        400,
    )


@app.before_request
def enforce_request_security():
    """Reject malicious web content/prompt injection and sanitize safe JSON."""
    if not UTILS_AVAILABLE:
        return None

    args_payload = request.args.to_dict(flat=False)
    args_scan = scan_payload_for_threats(args_payload, path="query")
    if not args_scan.valid:
        return _security_violation_response(args_scan.errors, "query")

    form_payload = request.form.to_dict(flat=False)
    form_scan = scan_payload_for_threats(form_payload, path="form")
    if not form_scan.valid:
        return _security_violation_response(form_scan.errors, "form")

    if request.method in {"POST", "PUT", "PATCH"}:
        content_type = request.content_type or ""
        if "application/json" in content_type:
            payload = request.get_json(silent=True)
            if payload is not None:
                payload_scan = scan_payload_for_threats(payload, path="json")
                if not payload_scan.valid:
                    return _security_violation_response(payload_scan.errors, "json")

                g.sanitized_json = sanitize_dict(payload)

    return None


# Security Headers Middleware
@app.after_request
def set_security_headers(response):
    """Add security headers to all responses"""
    is_production = os.getenv("ENVIRONMENT") == "production"

    # Content Security Policy
    frame_ancestors = "'none'" if is_production else "'self' vscode-webview:"
    csp = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.socket.io 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' ws: wss:; "
        f"frame-ancestors {frame_ancestors}; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers["Content-Security-Policy"] = csp

    # Additional security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    if is_production:
        response.headers["X-Frame-Options"] = "DENY"
    else:
        response.headers.pop("X-Frame-Options", None)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # HTTPS enforcement (in production)
    if is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


# Request size error handler
@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle requests that are too large"""
    return jsonify({"error": "Request too large", "max_size": "10MB"}), 413


# Error handler decorator
def handle_errors(f):
    """Decorator for consistent error handling"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            duration = (time.time() - start_time) * 1000

            if UTILS_AVAILABLE:
                api_logger.api_request(request.method, request.path, 200, duration)

            return result
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_msg = str(e)
            trace = traceback.format_exc()

            if UTILS_AVAILABLE:
                logger.error(f"Error in {f.__name__}: {error_msg}", exc_info=True)
                api_logger.api_request(request.method, request.path, 500, duration)
            else:
                print(f"❌ Error in {f.__name__}: {error_msg}")
                print(trace)

            return (
                jsonify(
                    {
                        "success": False,
                        "error": error_msg,
                        "message": "An error occurred processing your request",
                    }
                ),
                500,
            )

    return decorated_function


def _get_graph_template_defaults() -> Dict[str, Any]:
    default_scenario = _get_default_scenario_for_environment()
    if _is_production_environment():
        return {
            "company_name": "",
            "dba_name": "",
            "industry": "",
            "industry_other": "",
            "location": "",
            "budget": "",
            "timeline": "",
            "objectives_text": "",
            "scenario_schema_version": SCENARIO_SCHEMA_VERSION,
            "scenario_defaults_version": _scenario_defaults_version(),
        }

    return {
        "company_name": default_scenario["company_name"],
        "dba_name": default_scenario["dba_name"],
        "industry": default_scenario["industry"],
        "industry_other": "",
        "location": default_scenario["location"],
        "budget": default_scenario["budget"],
        "timeline": default_scenario["timeline"],
        "objectives": list(default_scenario["objectives"]),
        "objectives_text": "\n".join(default_scenario["objectives"]),
        "scenario_schema_version": SCENARIO_SCHEMA_VERSION,
        "scenario_defaults_version": _scenario_defaults_version(),
    }


@app.route("/")
@app.route("/graph")
@app.route("/admin")
@app.route("/reports")
@app.route("/admin/reports")
def index():
    """
    v0.4 — Single unified entry point for all dashboard routes.

    Legacy aliases (/graph, /admin, /reports, /admin/reports) all resolve
    here so bookmarks and external links continue to work.

    The active tab can be pre-selected via ?tab=<name>
    (live | agents | reports | tasks | log).
    """
    from flask import request as _req

    tab = _req.args.get("tab", "")
    if UTILS_AVAILABLE:
        logger.info(f"v0.4 dashboard accessed — path={_req.path} tab={tab or 'default'}")
    return render_template(
        "index.html",
        is_production=_is_production_environment(),
        scenario_defaults=_get_graph_template_defaults(),
        initial_tab=tab,
    )


@app.route("/debug")
def debug():
    """Debug console page"""
    return render_template("debug.html")


@app.route("/docs")
def documentation():
    """Documentation page"""
    if UTILS_AVAILABLE:
        logger.info("Documentation page accessed")
    return render_template("docs.html")


@app.route("/logs")
def logs_viewer():
    """Logs viewer page"""
    if UTILS_AVAILABLE:
        logger.info("Logs viewer page accessed")
    return render_template("logs.html")


@app.route("/api/agents/available")
def get_available_agents():
    """Get list of all available agents (executive + specialized)."""
    factory = AgentFactory()
    agents = [
        {
            "type": "ceo",
            "name": "CEO Agent",
            "capabilities": [
                "Executive strategic planning",
                "Multi-agent orchestration",
                "Risk-aware decision governance",
            ],
            "budget": system_settings["total_budget"],
            "status": "available",
        },
        {
            "type": "cfo",
            "name": "CFO Agent",
            "capabilities": [
                "Financial monitoring",
                "Budget oversight",
                "Payment recommendation analysis",
            ],
            "budget": system_settings["cfo_api_limit"] + system_settings["cfo_legal_limit"],
            "status": "available",
        },
    ]

    for agent_type in factory.get_available_agents():
        try:
            agent = factory.create_agent(agent_type)
            guard_rail = AgentGuardRail(AgentDomain[agent_type.upper()])

            agents.append(
                {
                    "type": agent_type,
                    "name": agent.name,
                    "capabilities": agent.capabilities,
                    "budget": guard_rail.budget_constraint.max_budget
                    if guard_rail.budget_constraint
                    else 0,
                    "status": "available",
                }
            )
        except Exception as e:
            print(f"Error loading agent {agent_type}: {e}")

    return jsonify({"agents": agents})


@app.route("/api/scenario/current", methods=["GET", "POST"])
def scenario_current():
    """Get or update shared scenario context used by dashboard/admin/reports."""
    try:
        if request.method == "GET":
            return jsonify({"success": True, "scenario": _get_shared_scenario_context()})

        payload = getattr(g, "sanitized_json", request.json or {})
        if UTILS_AVAILABLE:
            allowlist_validation = validate_payload_allowlist(
                payload,
                allowed_fields={
                    "company_name",
                    "name",
                    "dba_name",
                    "industry",
                    "location",
                    "budget",
                    "timeline",
                    "objectives",
                    "updated_at",
                },
                required_fields=set(),
                payload_name="scenario",
            )
            if not allowlist_validation.valid:
                return _allowlist_violation_response(allowlist_validation.errors, "scenario")

        scenario = _normalize_scenario_context(payload, payload.get("objectives"))
        _update_shared_scenario_context(
            scenario,
            source="api_scenario_update",
            broadcast=True,
            user_modified=True,
        )
        return jsonify({"success": True, "scenario": _get_shared_scenario_context()})
    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f"Error handling scenario_current: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/ceo/analyze", methods=["POST"])
@app.route("/api/cfo/analyze", methods=["POST"])  # Backward compatibility
def analyze_objectives():
    """Analyze strategic objectives with CEO/CFO agent"""
    try:
        # Validate content type
        if request.content_type and "application/json" not in request.content_type:
            return (
                jsonify(
                    {
                        "error": "Unsupported Media Type",
                        "message": "Content-Type must be application/json",
                    }
                ),
                415,
            )

        data = getattr(g, "sanitized_json", request.json or {})

        # Debug: log received keys before validation
        print(
            f"📊 CEO/analyze — received keys: {sorted(data.keys()) if isinstance(data, dict) else type(data)}"
        )

        if UTILS_AVAILABLE:
            allowlist_validation = validate_payload_allowlist(
                data,
                allowed_fields={
                    "company_name",
                    "dba_name",
                    "industry",
                    "location",
                    "objectives",
                    "budget",
                    "timeline",
                    "updated_at",
                },
                required_fields={"company_name", "industry", "location"},
                payload_name="analyze",
            )
            if not allowlist_validation.valid:
                print(f"❌ CEO/analyze allowlist rejected: {allowlist_validation.errors}")
                return _allowlist_violation_response(allowlist_validation.errors, "analyze")

        print(f"📊 CEO Analysis request received: {data}")
        print(f"📊 Data type: {type(data)}")
        print(f"📊 Data keys: {data.keys() if data else 'None'}")

        if not CEO_AGENT_AVAILABLE:
            return jsonify({"success": False, "error": "CEO agent not available"}), 503

        normalized_scenario = _normalize_scenario_context(
            {
                "company_name": data.get("company_name"),
                "name": data.get("company_name"),
                "dba_name": data.get("dba_name") or data.get("company_name"),
                "industry": data.get("industry"),
                "location": data.get("location"),
                "budget": data.get("budget", 5000),
                "timeline": data.get("timeline", 90),
            },
            data.get("objectives"),
        )
        _update_shared_scenario_context(
            normalized_scenario,
            source="api_analyze",
            broadcast=True,
            user_modified=True,
        )

        # Create initial state matching CEOAgentState schema
        state = {
            # Company context
            "company_name": normalized_scenario["company_name"],
            "industry": normalized_scenario["industry"],
            "location": normalized_scenario["location"],
            "business_goals": [],
            # Strategic objectives
            "strategic_objectives": normalized_scenario["objectives"]
            or data.get(
                "objectives",
                [
                    f"Launch {normalized_scenario['company_name']} with digital presence",
                    "Build brand identity and market positioning",
                ],
            ),
            # Budget management
            "total_budget": float(normalized_scenario["budget"]),
            "budget_allocated": {},
            "budget_reserved_for_fees": 0,
            "pending_approvals": [],
            "approved_actions": [],
            "rejected_actions": [],
            "pending_payments": [],
            # Timeline
            "target_completion_days": int(normalized_scenario["timeline"]),
            "current_day": 0,
            "milestones": [],
            # Multi-agent orchestration
            "active_agents": [],
            "agent_outputs": [],
            "agent_status": {},
            "delegated_tasks": {},
            # Task breakdown
            "identified_tasks": [],
            "assigned_tasks": {},
            "completed_tasks": [],
            "blocked_tasks": [],
            # Risk management
            "risks": [],
            "risk_mitigation_plans": {},
            "opportunities": [],
            "opportunity_analysis": [],
            # Deliverables
            "deliverables": [],
            "status_reports": [],
            "final_executive_summary": "",
            # Governance
            "guard_rail_violations": [],
            "liability_warnings": [],
            "compliance_status": {},
            "executive_decisions": [],
            # Workflow
            "current_phase": "initialization",
            "completed_phases": [],
        }

        print("🔄 Running CEO strategic analysis...")

        # Run strategic analysis
        result = ceo_analyze(state)

        print(f"✅ Analysis complete. Tasks: {len(result.get('identified_tasks', []))}")

        identified_tasks_raw = result.get("identified_tasks", [])
        identified_tasks = [task for task in identified_tasks_raw if isinstance(task, dict)]
        critical_tasks = [
            task for task in identified_tasks if str(task.get("priority", "")).upper() == "CRITICAL"
        ]
        high_tasks = [
            task for task in identified_tasks if str(task.get("priority", "")).upper() == "HIGH"
        ]

        top_priorities = []
        for task in critical_tasks[:2] + high_tasks[:2]:
            top_priorities.append(
                f"{task.get('task_id', 'TASK')}: {task.get('task_name', 'Priority task')}"
            )

        pending_approval_items = result.get("pending_approvals", [])
        immediate_actions = [
            f"Start: {task.get('task_name', task.get('description', 'Task'))}"
            for task in identified_tasks
            if not task.get("requires_payment")
        ][:5]

        approval_actions = [
            f"Approval needed: {item.get('task_name', item.get('task_id', 'Task'))} (${item.get('amount', 0)})"
            for item in pending_approval_items
        ][:5]

        risk_items = result.get("risks", [])
        risk_lines = [
            risk.get("description", "Risk identified") if isinstance(risk, dict) else str(risk)
            for risk in risk_items
        ]

        executive_summary = (
            f"CEO identified {len(identified_tasks)} strategic tasks for "
            f"{normalized_scenario['company_name']} with "
            f"{len(pending_approval_items)} payment approvals pending."
        )

        response_payload = {
            "success": True,
            "tasks": identified_tasks,
            "budget_allocation": result.get("budget_allocated", {}),
            "risks": risk_items,
            "timeline": result.get("target_completion_days", 90),
            "pending_approvals": pending_approval_items,
            "top_priorities": top_priorities,
            "immediate_actions": immediate_actions,
            "approval_actions": approval_actions,
            "executive_summary": executive_summary,
            "risk_summary": risk_lines[:5],
            "executive_report_markdown": result.get("final_executive_summary", ""),
            "execution_mode": "AI_PERFORMED",
        }

        try:
            artifact_bundle = artifact_service.persist_agent_execution(
                agent_type="ceo",
                agent_name="CEO Agent",
                task="Analyze strategic objectives and execution plan",
                company_info={
                    "name": normalized_scenario.get("company_name"),
                    "dba_name": normalized_scenario.get("dba_name"),
                    "industry": normalized_scenario.get("industry"),
                    "location": normalized_scenario.get("location"),
                },
                result={
                    "status": "analysis_complete",
                    "deliverables": response_payload.get("tasks", []),
                    "risks": response_payload.get("risks", []),
                    "budget_allocation": response_payload.get("budget_allocation", {}),
                    "timeline_days": response_payload.get("timeline"),
                    "summary": response_payload.get("executive_summary"),
                    "recommendations": response_payload.get("approval_actions", []),
                },
            )
            response_payload["artifacts"] = artifact_bundle.get("artifacts", [])
            response_payload["artifact_run_id"] = artifact_bundle.get("run_id")
            response_payload["artifact_directory"] = artifact_bundle.get("directory")
        except Exception as artifact_error:
            if UTILS_AVAILABLE:
                logger.warning(f"CEO artifact persistence failed: {artifact_error}")

        return jsonify(response_payload)
    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/graph/execute", methods=["POST"])
def execute_graph():
    """Execute the LangGraph multi-agent system"""
    if not GRAPH_ARCHITECTURE_AVAILABLE:
        return (
            jsonify({"success": False, "error": "Graph architecture not available"}),
            503,
        )

    try:
        data = getattr(g, "sanitized_json", request.json or {})
        if UTILS_AVAILABLE:
            allowlist_validation = validate_payload_allowlist(
                data,
                allowed_fields={
                    "company_name",
                    "dba_name",
                    "industry",
                    "location",
                    "total_budget",
                    "target_days",
                    "objectives",
                    "thread_id",
                    "use_checkpointing",
                },
                required_fields={"company_name", "industry", "location", "objectives"},
                payload_name="graph_execute",
            )
            if not allowlist_validation.valid:
                return _allowlist_violation_response(allowlist_validation.errors, "graph_execute")

        logger.info(f"Graph execution request: {data}")

        # Extract and validate parameters
        company_name = data.get("company_name", "")
        industry = data.get("industry", "")
        location = data.get("location", "")
        total_budget = data.get("total_budget", 0)
        target_days = data.get("target_days", 90)
        objectives = data.get("objectives", [])
        thread_id = data.get("thread_id") or str(uuid.uuid4())
        use_checkpointing = data.get("use_checkpointing", True)

        # Validation
        if not company_name or not industry or not location:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Missing required fields: company_name, industry, location",
                    }
                ),
                400,
            )

        if not objectives or len(objectives) == 0:
            return (
                jsonify({"success": False, "error": "At least one objective is required"}),
                400,
            )

        normalized_scenario = _normalize_scenario_context(
            {
                "company_name": company_name,
                "name": company_name,
                "dba_name": data.get("dba_name") or company_name,
                "industry": industry,
                "location": location,
                "budget": total_budget,
                "timeline": target_days,
            },
            objectives,
        )
        _update_shared_scenario_context(
            normalized_scenario,
            source="api_graph_execute",
            broadcast=True,
            user_modified=True,
        )

        # Emit start event
        socketio.emit(
            "execution_started",
            {
                "thread_id": thread_id,
                "company_name": company_name,
                "industry": industry,
                "total_budget": total_budget,
                "target_days": target_days,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Execute in background thread
        def run_graph_execution():
            try:
                logger.info(f"Starting graph execution: {company_name} - {industry}")

                # Update phase
                socketio.emit(
                    "phase_update",
                    {
                        "phase": "Initializing",
                        "progress": 0,
                        "message": "Starting CEO orchestrator...",
                    },
                )

                socketio.emit(
                    "agent_update",
                    {
                        "agent": "ceo",
                        "status": "active",
                        "message": "CEO orchestrator initializing",
                        "phase": "initialization",
                    },
                )

                # Execute the graph with correct parameters
                result = execute_multi_agent_system(
                    company_name=company_name,
                    industry=industry,
                    location=location,
                    total_budget=total_budget,
                    target_days=target_days,
                    objectives=objectives,
                    use_checkpointing=use_checkpointing,
                    thread_id=thread_id,
                )

                logger.info(
                    f"Graph execution completed: {len(result.get('agent_outputs', []))} agent outputs"
                )

                # Update agents based on result
                agent_outputs = result.get("agent_outputs", [])
                unique_agents = set()
                for output in agent_outputs:
                    agent = output.get("agent", "").lower()
                    if agent and agent not in unique_agents:
                        unique_agents.add(agent)
                        socketio.emit(
                            "agent_update",
                            {
                                "agent": agent,
                                "status": "success",
                                "message": f"{agent.upper()} completed successfully",
                                "phase": "completed",
                            },
                        )

                socketio.emit(
                    "phase_update",
                    {
                        "phase": "Complete",
                        "progress": 100,
                        "message": "All agents completed successfully",
                    },
                )

                # Emit completion
                socketio.emit(
                    "execution_complete",
                    {
                        "thread_id": thread_id,
                        "result": result,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            except Exception as e:
                logger.error(f"Graph execution error: {e}", exc_info=True)
                socketio.emit(
                    "execution_error",
                    {
                        "thread_id": thread_id,
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                        "timestamp": datetime.now().isoformat(),
                    },
                )

        # Start background execution
        thread = threading.Thread(target=run_graph_execution)
        thread.daemon = True
        thread.start()

        return jsonify({"success": True, "thread_id": thread_id, "message": "Execution started"})

    except Exception as e:
        logger.error(f"Graph execution setup error: {e}", exc_info=True)
        return (
            jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}),
            500,
        )


@app.route("/api/agent/execute/<agent_type>", methods=["POST"])
def execute_agent(agent_type):
    """Execute a specific specialized agent"""
    normalized_agent_type = "branding" if agent_type.lower() == "designer" else agent_type
    data = getattr(g, "sanitized_json", request.json or {})
    if UTILS_AVAILABLE:
        allowlist_validation = validate_payload_allowlist(
            data,
            allowed_fields={"task", "company_info", "requirements"},
            required_fields={"task", "company_info"},
            payload_name="agent_execute",
        )
        if not allowlist_validation.valid:
            return _allowlist_violation_response(allowlist_validation.errors, "agent_execute")

        company_info_validation = validate_company_info_allowlist(data.get("company_info", {}))
        if not company_info_validation.valid:
            return _allowlist_violation_response(company_info_validation.errors, "agent_execute")

    try:
        result = _execute_specialized_agent(normalized_agent_type, data)
        return jsonify({"success": True, "result": result})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def _execute_executive_agent(agent_type: str, data: dict) -> dict:
    """Execute CEO or CFO executive agents which are not in AgentFactory."""
    company_info = dict(data.get("company_info", {}) or {})
    company_name = company_info.get("company_name") or company_info.get("name", "Company")
    industry = company_info.get("industry", "General Business")
    location = company_info.get("location", "United States")
    task = data.get("task", f"Execute {agent_type.upper()} tasks")
    agent_name = "CEO Executive Agent" if agent_type == "ceo" else "CFO Financial Agent"

    result = {
        "agent_type": agent_type,
        "agent_name": agent_name,
        "status": "executed",
        "timestamp": datetime.now().isoformat(),
        "execution_mode": "AI_PERFORMED",
        "budget_used": 0,
        "deliverables": [],
    }

    if agent_type == "ceo" and CEO_AGENT_AVAILABLE:
        try:
            state = {
                "company_name": company_name,
                "industry": industry,
                "location": location,
                "business_goals": [],
                "strategic_objectives": [task],
                "agent_status": {},
                "delegated_tasks": {},
                "identified_tasks": [],
                "assigned_tasks": {},
                "completed_tasks": [],
                "blocked_tasks": [],
                "risks": [],
                "risk_mitigation_plans": {},
                "opportunities": [],
                "opportunity_analysis": [],
                "deliverables": [],
                "status_reports": [],
                "final_executive_summary": "",
                "guard_rail_violations": [],
                "liability_warnings": [],
                "compliance_status": {},
                "executive_decisions": [],
                "current_phase": "initialization",
                "completed_phases": [],
            }
            ceo_result = ceo_analyze(state)
            identified_tasks = [
                t for t in ceo_result.get("identified_tasks", []) if isinstance(t, dict)
            ]
            result["deliverables"] = [
                f"✅ {t.get('task_name', t.get('task_id', 'Task'))}: {t.get('description', '')}"
                for t in identified_tasks[:5]
            ] or [f"✅ CEO strategic analysis complete for {company_name}"]
            result["tasks"] = identified_tasks
            result["risks"] = ceo_result.get("risks", [])
            result["executive_summary"] = ceo_result.get("final_executive_summary", "")
        except Exception as exc:
            result["deliverables"] = [f"⚠️ CEO analysis error: {str(exc)[:200]}"]
            result["status"] = "partial"
    else:
        # Fallback (CEO unavailable or CFO type)
        result["deliverables"] = [
            f"✅ {agent_name} activated for {company_name}",
            f"📋 Task: {task}",
            f"🏢 Industry: {industry} | Location: {location}",
        ]

    return result


def _execute_specialized_agent(agent_type: str, data: dict) -> dict:
    """Execute a specialized agent and normalize result payload."""
    agent_type = "branding" if str(agent_type).lower() == "designer" else agent_type

    # Executive agents are not in AgentFactory — route to dedicated handler
    if agent_type.lower() in ("ceo", "cfo"):
        return _execute_executive_agent(agent_type.lower(), data)

    factory = AgentFactory()
    agent = factory.create_agent(agent_type)

    company_info = dict(data.get("company_info", {}) or {})
    if not company_info.get("name"):
        company_info["name"] = company_info.get("company_name", "Company")
    if not company_info.get("dba_name"):
        company_info["dba_name"] = company_info.get("name", "Company")
    if not company_info.get("industry"):
        company_info["industry"] = "General Business"
    if not company_info.get("location"):
        company_info["location"] = "United States"

    result = {
        "agent_type": agent_type,
        "agent_name": agent.name,
        "status": "executed",
        "timestamp": datetime.now().isoformat(),
        "execution_mode": "AI_PERFORMED",
    }

    if agent_type == "branding" and hasattr(agent, "design_concepts"):
        state = {
            "task_description": data.get("task", "Design brand identity"),
            "company_info": company_info,
            "research_findings": [],
            "design_concepts": [],
            "recommendations": [],
            "deliverables": [],
            "status": "initializing",
            "budget_used": 0,
            "timeline_days": 30,
        }
        concepts_result = agent.design_concepts(state)
        result["status"] = concepts_result.get("status", result["status"])
        result["timeline_days"] = concepts_result.get("timeline_days", 0)
        result["deliverables"] = concepts_result.get("deliverables", [])
        result["design_concepts"] = concepts_result.get("design_concepts", [])
        result["brand_kit_reference"] = concepts_result.get("brand_kit_reference", {})
        result["recommendations"] = concepts_result.get(
            "best_practices", concepts_result.get("recommendations", [])
        )
        result["best_practices"] = concepts_result.get("best_practices", [])
        result["action_plan_30_60_90"] = concepts_result.get("action_plan_30_60_90", {})
        result["codex_tooling"] = concepts_result.get("codex_tooling", {})
        result["budget_used"] = concepts_result.get("budget_used", 0)

    elif agent_type == "web_development" and hasattr(agent, "analyze_requirements"):
        state = {
            "task_description": data.get("task", "Build website with AR"),
            "requirements": data.get("requirements", company_info),
            "tech_stack": [],
            "architecture_design": "",
            "ar_features": [],
            "development_phases": [],
            "testing_results": [],
            "deliverables": [],
            "status": "initializing",
            "budget_used": 0,
            "timeline_days": 60,
        }
        web_result = agent.analyze_requirements(state)
        result["tech_stack"] = web_result.get("tech_stack", [])
        result["deliverables"] = web_result.get(
            "deliverables", web_result.get("development_phases", [])
        )
        result["timeline"] = web_result.get("development_phases", [])
        result["action_plan_30_60_90"] = web_result.get("action_plan_30_60_90", {})
        result["recommendations"] = web_result.get("best_practices", [])
        result["best_practices"] = web_result.get("best_practices", [])
        result["budget_used"] = web_result.get("budget_used", 0)

    elif agent_type == "martech" and hasattr(agent, "configure_stack"):
        state = {
            "task_description": data.get("task", "Configure marketing tech stack"),
            "current_systems": [],
            "recommended_stack": [],
            "integrations": [],
            "automation_workflows": [],
            "implementation_plan": "",
            "status": "initializing",
            "budget_used": 0,
            "timeline_days": 30,
        }
        martech_result = agent.configure_stack(state)
        result["tech_stack"] = martech_result.get("recommended_stack", [])
        result["deliverables"] = martech_result.get(
            "deliverables",
            [
                f"✅ {tool.get('tool', 'Tool')}: {tool.get('ai_configures', 'Configured')}"
                for tool in martech_result.get("recommended_stack", [])
            ],
        )
        result["action_plan_30_60_90"] = martech_result.get("action_plan_30_60_90", {})
        result["recommendations"] = martech_result.get("best_practices", [])
        result["budget_used"] = martech_result.get("budget_used", 0)

    elif agent_type == "content" and hasattr(agent, "produce_content"):
        state = {
            "task_description": data.get("task", "Create marketing content"),
            "content_types": [],
            "production_schedule": [],
            "assets_created": [],
            "distribution_plan": "",
            "seo_strategy": "",
            "status": "initializing",
            "budget_used": 0,
            "timeline_days": 30,
        }
        content_result = agent.produce_content(state)
        result["deliverables"] = content_result.get(
            "deliverables", content_result.get("assets_created", [])
        )
        result["action_plan_30_60_90"] = content_result.get("action_plan_30_60_90", {})
        result["recommendations"] = content_result.get("best_practices", [])
        result["budget_used"] = content_result.get("budget_used", 0)

    elif agent_type == "campaigns" and hasattr(agent, "launch_campaigns"):
        state = {
            "task_description": data.get("task", "Launch advertising campaigns"),
            "channels": [],
            "audience_targeting": [],
            "creative_assets": [],
            "budget_allocation": [],
            "performance_metrics": [],
            "status": "initializing",
            "budget_used": 0,
            "timeline_days": 30,
        }
        campaign_result = agent.launch_campaigns(state)
        result["timeline"] = campaign_result.get("creative_concepts", [])
        result["deliverables"] = campaign_result.get(
            "deliverables",
            [
                concept.get("ai_creates", "Campaign created")
                for concept in campaign_result.get("creative_concepts", [])
            ],
        )
        result["action_plan_30_60_90"] = campaign_result.get("action_plan_30_60_90", {})
        result["recommendations"] = campaign_result.get("best_practices", [])
        result["best_practices"] = campaign_result.get("best_practices", [])
        result["budget_used"] = campaign_result.get("budget_used", 0)

    elif agent_type == "legal" and hasattr(agent, "dba_registration_process"):
        state = {
            "task_description": data.get("task", "Legal compliance and filing"),
            "jurisdiction": company_info.get("location", "United States"),
            "filings_required": [],
            "compliance_checklist": [],
            "documents_prepared": [],
            "risks_identified": [],
            "status": "initializing",
            "budget_used": 0,
            "timeline_days": 14,
        }
        legal_result = agent.dba_registration_process(state)
        result["deliverables"] = legal_result.get(
            "deliverables", legal_result.get("documents_prepared", [])
        )
        result["filings_required"] = legal_result.get("filings_required", [])
        result["compliance_checklist"] = legal_result.get("compliance_checklist", [])
        result["risks_identified"] = legal_result.get("risks_identified", [])
        result["action_plan_30_60_90"] = legal_result.get("action_plan_30_60_90", {})
        result["recommendations"] = legal_result.get(
            "recommendations", legal_result.get("best_practices", [])
        )
        result["best_practices"] = legal_result.get("best_practices", [])
        result["budget_used"] = legal_result.get("budget_used", 0)

    elif agent_type == "social_media" and hasattr(agent, "execute_social_strategy"):
        state = {
            "task_description": data.get(
                "task", "Build social media presence and content strategy"
            ),
            "platforms": [],
            "content_calendar": [],
            "posting_workflows": [],
            "campaign_ideas": [],
            "community_playbook": "",
            "status": "initializing",
            "budget_used": 0,
            "timeline_days": 30,
        }
        social_result = agent.execute_social_strategy(state)
        result["platforms"] = social_result.get("platforms", [])
        result["deliverables"] = social_result.get(
            "deliverables", social_result.get("posting_workflows", [])
        )
        result["timeline"] = social_result.get("content_calendar", [])
        result["campaign_ideas"] = social_result.get("campaign_ideas", [])
        result["community_playbook"] = social_result.get("community_playbook", "")
        result["action_plan_30_60_90"] = social_result.get("action_plan_30_60_90", {})
        result["recommendations"] = social_result.get("best_practices", [])
        result["best_practices"] = social_result.get("best_practices", [])
        result["budget_used"] = social_result.get("budget_used", 0)

    elif agent_type == "security":
        result["deliverables"] = [
            "✅ Security audit framework configured for all agent operations",
            "✅ Blockchain transaction logging layer initialized",
            "✅ Threat monitoring and anomaly detection protocols established",
            "✅ Compliance reporting templates generated (SOC2, GDPR baseline)",
            "✅ Access control policies documented and enforced",
            "✅ Penetration testing report and vulnerability registry created",
            "✅ Incident response runbook and escalation matrix drafted",
            "✅ Zero-trust architecture assessment and roadmap delivered",
        ]
        result["budget_used"] = 0
        result["action_plan_30_60_90"] = {
            "day_0_to_30": {
                "theme": "ASSESS — Security Audit & Threat Modeling",
                "priority": "CRITICAL",
                "objectives": [
                    "Conduct full OWASP Top-10 vulnerability assessment",
                    "Perform threat modeling (STRIDE) for all agent operations",
                    "Audit API key rotation and secrets management practices",
                    "Map all data flows and classify PII/sensitive assets",
                    "Establish security baseline metrics and SLA benchmarks",
                    "Deploy SIEM and centralized logging infrastructure",
                ],
                "deliverables": [
                    "Vulnerability assessment report with CVSS scores",
                    "Threat model diagram and attack surface map",
                    "Secrets management audit findings",
                    "Data classification matrix",
                ],
                "tools": ["OWASP ZAP", "Burp Suite", "HashiCorp Vault", "Splunk/ELK", "Trivy"],
                "kpis": ["0 critical vulnerabilities unpatched > 48h", "100% secrets in vault"],
                "budget_allocation": "$0 (internal tooling)",
            },
            "day_31_to_60": {
                "theme": "HARDEN — Implement Controls & SDLC Integration",
                "priority": "HIGH",
                "objectives": [
                    "Implement zero-trust network architecture principles",
                    "Integrate SAST/DAST into CI/CD pipeline",
                    "Deploy WAF, IDS/IPS, and rate-limiting protections",
                    "Enforce MFA and RBAC across all agent access points",
                    "Complete SOC 2 Type I readiness gap analysis",
                    "Run red team exercise against agent API endpoints",
                ],
                "deliverables": [
                    "Zero-trust implementation guide",
                    "CI/CD security gates configuration",
                    "SOC 2 gap analysis report",
                    "Red team findings and remediation plan",
                ],
                "tools": ["Snyk", "SonarQube", "Cloudflare WAF", "Okta", "AWS GuardDuty"],
                "kpis": ["SAST/DAST coverage > 90%", "MFA adoption 100%", "MTTR < 4h"],
                "budget_allocation": "$0 (OSS tooling)",
            },
            "day_61_to_90": {
                "theme": "MONITOR — Ongoing Detection & Incident Readiness",
                "priority": "HIGH",
                "objectives": [
                    "Activate 24/7 automated threat detection and alerting",
                    "Conduct tabletop incident response simulation",
                    "Establish quarterly penetration testing cadence",
                    "Publish security runbook and escalation matrix",
                    "Achieve SOC 2 Type II audit readiness",
                    "Implement blockchain-based audit trail for all transactions",
                ],
                "deliverables": [
                    "Incident response playbook (v1.0)",
                    "Penetration test results and remediation tracker",
                    "SOC 2 Type II readiness checklist",
                    "Blockchain audit trail implementation report",
                ],
                "tools": ["PagerDuty", "Datadog Security", "CrowdStrike Falcon", "Hyperledger"],
                "kpis": [
                    "MTTD < 15min",
                    "0 unresolved highs after 7 days",
                    "100% audit log coverage",
                ],
                "budget_allocation": "$0 (existing infra)",
            },
        }
        result["best_practices"] = [
            "Shift-left security: integrate SAST/DAST scans into every PR pipeline",
            "Zero-trust architecture: never trust, always verify — enforce mTLS between all agent services",
            "Secrets management: all API keys and credentials stored in HashiCorp Vault, rotated every 90 days",
            "Principle of least privilege: every agent role granted minimum required permissions only",
            "Defense in depth: WAF → IDS/IPS → SAST/DAST → runtime protection layered approach",
            "Immutable audit trails: blockchain-backed transaction logs for all financial agent operations",
            "Incident response readiness: documented runbook, tested annually via tabletop simulation",
            "Compliance-as-code: automated SOC 2, GDPR, and CCPA controls validated on every deployment",
        ]
        result["recommendations"] = result["best_practices"]

    if "deliverables" not in result or not result.get("deliverables"):
        result["deliverables"] = [
            f"✅ {agent.name} execution completed",
            f"📋 Task: {data.get('task', 'Agent task execution')}",
            f"🏢 Company: {company_info.get('company_name', company_info.get('name', 'N/A'))}",
        ]
    if "budget_used" not in result:
        result["budget_used"] = agent.budget if hasattr(agent, "budget") else 0

    try:
        artifact_bundle = artifact_service.persist_agent_execution(
            agent_type=agent_type,
            agent_name=agent.name,
            task=data.get("task", "Agent task execution"),
            company_info=company_info,
            result=result,
        )
        result["artifacts"] = artifact_bundle.get("artifacts", [])
        result["artifact_run_id"] = artifact_bundle.get("run_id")
        result["artifact_directory"] = artifact_bundle.get("directory")
    except Exception as artifact_error:
        if UTILS_AVAILABLE:
            logger.warning(f"Artifact persistence failed for {agent_type}: {artifact_error}")

    return result


@app.route("/api/guard-rails/<agent_type>")
def get_guard_rails(agent_type):
    """Get guard rail information for an agent"""
    try:
        print(f"🛡️ Guard rails request for: {agent_type}")

        normalized_agent_type = "branding" if agent_type.lower() == "designer" else agent_type

        # Executive agents — return bespoke guard rail info directly
        if normalized_agent_type.lower() in ("ceo", "cfo"):
            exec_info = {
                "ceo": {
                    "summary": "CEO Executive Agent — strategic orchestration and multi-agent governance",
                    "max_budget": system_settings.get("total_budget", 10000),
                    "allowed_categories": [
                        "Strategic Planning",
                        "Agent Orchestration",
                        "Risk Management",
                    ],
                    "forbidden_categories": ["Contractor Payments", "Personal Expenses"],
                    "permitted_tasks": [
                        "Analyze and set strategic objectives",
                        "Orchestrate all specialized agents",
                        "Risk assessment and opportunity analysis",
                        "Executive budget governance and approvals",
                        "Final executive reporting and summaries",
                    ],
                    "quality_standards": {
                        "strategic_alignment": "required",
                        "risk_flagging": "required",
                    },
                },
                "cfo": {
                    "summary": "CFO Financial Agent — financial oversight and payment governance",
                    "max_budget": system_settings.get("cfo_api_limit", 100)
                    + system_settings.get("cfo_legal_limit", 500),
                    "allowed_categories": ["API Fees", "Legal Filings", "Software Subscriptions"],
                    "forbidden_categories": [
                        "Advertising Spend",
                        "Contractor Payments",
                        "Hardware",
                    ],
                    "permitted_tasks": [
                        "Financial analysis and reporting",
                        "Budget allocation and optimization",
                        "Payment approval workflow management",
                        "Compliance and audit reporting",
                    ],
                    "quality_standards": {
                        "budget_accuracy": "required",
                        "fiduciary_compliance": "required",
                    },
                },
            }
            return jsonify(
                {"success": True, "guard_rail": exec_info[normalized_agent_type.lower()]}
            )

        # Map agent_type to AgentDomain enum
        domain_map = {
            "branding": "BRANDING",
            "web_development": "WEB_DEVELOPMENT",
            "legal": "LEGAL",
            "martech": "MARTECH",
            "content": "CONTENT",
            "campaigns": "CAMPAIGNS",
            "social_media": "SOCIAL_MEDIA",
            "security": "SECURITY",
        }

        domain_name = domain_map.get(normalized_agent_type.lower(), normalized_agent_type.upper())
        domain = AgentDomain[domain_name]

        summary = create_execution_summary(domain)
        guard_rail = AgentGuardRail(domain)

        print(f"✅ Guard rails loaded for {normalized_agent_type}")

        return jsonify(
            {
                "success": True,
                "guard_rail": {
                    "summary": summary,
                    "max_budget": guard_rail.budget_constraint.max_budget
                    if guard_rail.budget_constraint
                    else 0,
                    "allowed_categories": guard_rail.budget_constraint.allowed_categories
                    if guard_rail.budget_constraint
                    else [],
                    "forbidden_categories": guard_rail.budget_constraint.forbidden_categories
                    if guard_rail.budget_constraint
                    else [],
                    "permitted_tasks": guard_rail.scope_constraint.permitted_tasks
                    if guard_rail.scope_constraint
                    else [],
                    "quality_standards": guard_rail.quality_standard.metrics
                    if guard_rail.quality_standard
                    else {},
                },
            }
        )
    except Exception as e:
        print(f"❌ Guard rails error for {agent_type}: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# CEO AGENT ADMIN API ENDPOINTS
# ============================================================================


@app.route("/api/approvals/pending", methods=["GET"])
def get_pending_approvals():
    """Get all pending payment approvals"""
    return jsonify(
        {
            "success": True,
            "approvals": pending_approvals,
            "count": len(pending_approvals),
        }
    )


@app.route("/api/approval/<approval_id>/approve", methods=["POST"])
def approve_payment(approval_id):
    """Approve a payment request"""
    global pending_approvals

    approval = next((a for a in pending_approvals if a["id"] == approval_id), None)
    if not approval:
        return jsonify({"success": False, "error": "Approval not found"}), 404

    # Remove from pending
    pending_approvals = [a for a in pending_approvals if a["id"] != approval_id]

    # Emit update via SocketIO
    socketio.emit(
        "approval_approved",
        {
            "id": approval_id,
            "approval": approval,
            "timestamp": datetime.now().isoformat(),
        },
    )

    if UTILS_AVAILABLE:
        logger.info(f'Payment approved: {approval_id} - ${approval.get("amount", 0)}')

    return jsonify({"success": True, "message": "Payment approved", "approval": approval})


@app.route("/api/approval/<approval_id>/reject", methods=["POST"])
def reject_payment(approval_id):
    """Reject a payment request"""
    global pending_approvals

    approval = next((a for a in pending_approvals if a["id"] == approval_id), None)
    if not approval:
        return jsonify({"success": False, "error": "Approval not found"}), 404

    # Remove from pending
    pending_approvals = [a for a in pending_approvals if a["id"] != approval_id]

    # Emit update via SocketIO
    socketio.emit(
        "approval_rejected",
        {
            "id": approval_id,
            "approval": approval,
            "timestamp": datetime.now().isoformat(),
        },
    )

    if UTILS_AVAILABLE:
        logger.info(f'Payment rejected: {approval_id} - ${approval.get("amount", 0)}')

    return jsonify({"success": True, "message": "Payment rejected", "approval": approval})


@app.route("/api/reports/strategic", methods=["POST"])
def generate_strategic_report():
    """Generate comprehensive strategic report with 30/60/90 day plans"""
    try:
        from services.report_service import report_service

        company_info = getattr(g, "sanitized_json", request.json or {})
        if UTILS_AVAILABLE:
            allowlist_validation = validate_company_info_allowlist(company_info)
            if not allowlist_validation.valid:
                return _allowlist_violation_response(
                    allowlist_validation.errors, "strategic_report"
                )

        scenario_defaults = _get_shared_scenario_context()
        merged_company_info = {
            "company_name": company_info.get("company_name")
            or company_info.get("name")
            or scenario_defaults.get("company_name"),
            "name": company_info.get("name")
            or company_info.get("company_name")
            or scenario_defaults.get("company_name"),
            "dba_name": company_info.get("dba_name") or scenario_defaults.get("dba_name"),
            "industry": company_info.get("industry") or scenario_defaults.get("industry"),
            "location": company_info.get("location") or scenario_defaults.get("location"),
            "budget": company_info.get("budget", scenario_defaults.get("budget", 5000)),
            "timeline": company_info.get("timeline", scenario_defaults.get("timeline", 90)),
        }

        merged_scenario = _normalize_scenario_context(
            merged_company_info,
            scenario_defaults.get("objectives", []),
        )
        _update_shared_scenario_context(
            merged_scenario,
            source="report_strategic",
            broadcast=True,
            user_modified=True,
        )

        report = report_service.generate_strategic_report(merged_company_info)

        # Emit update via SocketIO
        socketio.emit(
            "report_generated",
            {
                "report_id": report["report_id"],
                "report_type": "strategic",
                "timestamp": datetime.now().isoformat(),
            },
        )

        if UTILS_AVAILABLE:
            logger.info(f'Strategic report generated: {report["report_id"]}')

        return jsonify({"success": True, "report": report})

    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f"Error generating strategic report: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reports/financial", methods=["POST"])
def generate_financial_report_endpoint():
    """Generate comprehensive financial report with projections"""
    try:
        from services.report_service import report_service

        company_info = getattr(g, "sanitized_json", request.json or {})
        if UTILS_AVAILABLE:
            allowlist_validation = validate_company_info_allowlist(company_info)
            if not allowlist_validation.valid:
                return _allowlist_violation_response(
                    allowlist_validation.errors, "financial_report"
                )

        scenario_defaults = _get_shared_scenario_context()
        merged_company_info = {
            "company_name": company_info.get("company_name")
            or company_info.get("name")
            or scenario_defaults.get("company_name"),
            "name": company_info.get("name")
            or company_info.get("company_name")
            or scenario_defaults.get("company_name"),
            "dba_name": company_info.get("dba_name") or scenario_defaults.get("dba_name"),
            "industry": company_info.get("industry") or scenario_defaults.get("industry"),
            "location": company_info.get("location") or scenario_defaults.get("location"),
            "budget": company_info.get("budget", scenario_defaults.get("budget", 5000)),
            "timeline": company_info.get("timeline", scenario_defaults.get("timeline", 90)),
        }

        merged_scenario = _normalize_scenario_context(
            merged_company_info,
            scenario_defaults.get("objectives", []),
        )
        _update_shared_scenario_context(
            merged_scenario,
            source="report_financial",
            broadcast=True,
            user_modified=True,
        )

        report = report_service.generate_financial_report(merged_company_info)

        # Emit update via SocketIO
        socketio.emit(
            "report_generated",
            {
                "report_id": report["report_id"],
                "report_type": "financial",
                "timestamp": datetime.now().isoformat(),
            },
        )

        if UTILS_AVAILABLE:
            logger.info(f'Financial report generated: {report["report_id"]}')

        return jsonify({"success": True, "report": report})

    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f"Error generating financial report: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reports/training", methods=["GET"])
def generate_training_report_endpoint():
    """Generate training progress report"""
    try:
        from services.report_service import report_service

        report = report_service.generate_training_report()

        # Emit update via SocketIO
        socketio.emit(
            "report_generated",
            {
                "report_id": report["report_id"],
                "report_type": "training",
                "timestamp": datetime.now().isoformat(),
            },
        )

        if UTILS_AVAILABLE:
            logger.info(f'Training report generated: {report["report_id"]}')

        return jsonify({"success": True, "report": report})

    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f"Error generating training report: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reports/research", methods=["GET"])
def generate_research_report_endpoint():
    """Generate research findings report"""
    try:
        from services.report_service import report_service

        report = report_service.generate_research_report()

        # Emit update via SocketIO
        socketio.emit(
            "report_generated",
            {
                "report_id": report["report_id"],
                "report_type": "research",
                "timestamp": datetime.now().isoformat(),
            },
        )

        if UTILS_AVAILABLE:
            logger.info(f'Research report generated: {report["report_id"]}')

        return jsonify({"success": True, "report": report})

    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f"Error generating research report: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reports/history", methods=["GET"])
def get_report_history():
    """Get all historical reports"""
    try:
        from services.report_service import report_service

        history = report_service.get_report_history()

        return jsonify({"success": True, "reports": history, "count": len(history)})

    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f"Error retrieving report history: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reports/<report_id>", methods=["GET"])
def get_report_by_id(report_id):
    """Get specific report by ID"""
    try:
        from services.report_service import report_service

        report = report_service.get_report_by_id(report_id)

        if report is None:
            return jsonify({"success": False, "error": "Report not found"}), 404

        return jsonify({"success": True, "report": report})

    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f"Error retrieving report: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/cfo/report", methods=["GET"])
def get_cfo_report():
    """Get CFO financial report"""
    try:
        if CEO_AGENT_AVAILABLE:
            # Use new CFO agent
            state = {
                "company_name": "CEO Agent Platform",
                "industry": "AI Technology",
                "total_budget": system_settings["total_budget"],
                "allocated_to_api_fees": system_settings["cfo_api_limit"],
                "api_costs_incurred": [],
                "legal_filing_costs": [],
                "daily_api_spend": {},
                "monthly_projections": {},
                "budget_alerts": [],
                "pending_payment_requests": [
                    {
                        "request_id": item.get("id", f"REQ_{index}"),
                        "amount": item.get("amount", 0),
                        "purpose": item.get("payment_type", item.get("title", "Payment request")),
                        "requested_by": item.get("requested_by", "system"),
                    }
                    for index, item in enumerate(pending_approvals)
                ],
                "cfo_recommendations": [],
                "approved_payments": [],
                "rejected_payments": [],
                "spending_violations": [],
                "financial_risks": [],
                "compliance_checks": {},
                "financial_reports": [],
                "audit_trail": [],
            }
            report = generate_financial_report(state)
            response_payload = {"success": True, "report": report}
            try:
                artifact_bundle = artifact_service.persist_agent_execution(
                    agent_type="cfo",
                    agent_name="CFO Agent",
                    task="Generate financial report",
                    company_info={
                        "name": "CEO Agent Platform",
                        "industry": "AI Technology",
                        "location": "United States",
                    },
                    result={
                        "status": "report_generated",
                        "report": report,
                        "deliverables": report.get("cfo_recommendations", []),
                    },
                )
                response_payload["artifacts"] = artifact_bundle.get("artifacts", [])
                response_payload["artifact_run_id"] = artifact_bundle.get("run_id")
                response_payload["artifact_directory"] = artifact_bundle.get("directory")
            except Exception as artifact_error:
                if UTILS_AVAILABLE:
                    logger.warning(f"CFO artifact persistence failed: {artifact_error}")
            return jsonify(response_payload)
        else:
            # Fallback report
            fallback_report = {
                "total_budget": system_settings["total_budget"],
                "cfo_managed": system_settings["cfo_api_limit"]
                + system_settings["cfo_legal_limit"],
                "user_approval_required": system_settings["total_budget"]
                - (system_settings["cfo_api_limit"] + system_settings["cfo_legal_limit"]),
                "pending_approvals": len(pending_approvals),
            }
            response_payload = {"success": True, "report": fallback_report}
            try:
                artifact_bundle = artifact_service.persist_agent_execution(
                    agent_type="cfo",
                    agent_name="CFO Agent",
                    task="Generate fallback financial report",
                    company_info={"name": "CEO Agent Platform"},
                    result={"status": "report_generated", "report": fallback_report},
                )
                response_payload["artifacts"] = artifact_bundle.get("artifacts", [])
                response_payload["artifact_run_id"] = artifact_bundle.get("run_id")
                response_payload["artifact_directory"] = artifact_bundle.get("directory")
            except Exception as artifact_error:
                if UTILS_AVAILABLE:
                    logger.warning(f"CFO fallback artifact persistence failed: {artifact_error}")
            return jsonify(response_payload)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/artifacts/runs", methods=["GET"])
@app.route("/api/artifacts/runs/<agent_type>", methods=["GET"])
def list_artifact_runs(agent_type=None):
    """List generated artifact runs for dashboard review."""
    try:
        limit = request.args.get("limit", default=20, type=int)
        runs = artifact_service.list_artifact_runs(agent_type=agent_type, limit=limit)
        return jsonify({"success": True, "runs": runs, "count": len(runs)})
    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f"Error listing artifact runs: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/settings/update", methods=["POST"])
def update_settings():
    """Update system settings"""
    global system_settings

    try:
        data = getattr(g, "sanitized_json", request.json or {})
        if UTILS_AVAILABLE:
            allowlist_validation = validate_payload_allowlist(
                data,
                allowed_fields={
                    "systemMode",
                    "autoApproveAPI",
                    "emailNotifications",
                    "totalBudget",
                    "cfoAPILimit",
                    "cfoLegalLimit",
                },
                payload_name="settings",
            )
            if not allowlist_validation.valid:
                return _allowlist_violation_response(allowlist_validation.errors, "settings")

        # Update settings
        if "systemMode" in data:
            system_settings["system_mode"] = data["systemMode"]
        if "autoApproveAPI" in data:
            system_settings["auto_approve_api"] = data["autoApproveAPI"]
        if "emailNotifications" in data:
            system_settings["email_notifications"] = data["emailNotifications"]
        if "totalBudget" in data:
            system_settings["total_budget"] = float(data["totalBudget"])
        if "cfoAPILimit" in data:
            system_settings["cfo_api_limit"] = float(data["cfoAPILimit"])
        if "cfoLegalLimit" in data:
            system_settings["cfo_legal_limit"] = float(data["cfoLegalLimit"])

        if UTILS_AVAILABLE:
            logger.info(f"Settings updated: {system_settings}")

        return jsonify({"success": True, "settings": system_settings})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/research/start", methods=["POST"])
def start_research():
    """Start research session"""
    data = getattr(g, "sanitized_json", request.json or {})

    if UTILS_AVAILABLE:
        allowlist_validation = validate_payload_allowlist(
            data,
            allowed_fields={"topic", "sources", "priority"},
            payload_name="research",
        )
        if not allowlist_validation.valid:
            return _allowlist_violation_response(allowlist_validation.errors, "research")

    # Simulate research findings
    socketio.emit(
        "research_update",
        {
            "title": "AI Tool Discovery",
            "description": "Found new cost-effective API alternatives",
            "tags": ["API", "Cost Optimization"],
            "timestamp": datetime.now().isoformat(),
        },
    )

    return jsonify({"success": True, "message": "Research started"})


@app.route("/api/logs", methods=["GET"])
def get_logs():
    """Get system logs"""
    try:
        log_files = []
        logs_dir = "logs"

        if os.path.exists(logs_dir):
            for filename in os.listdir(logs_dir):
                if filename.endswith(".log"):
                    filepath = os.path.join(logs_dir, filename)
                    with open(filepath, "r") as f:
                        # Get last 100 lines
                        lines = f.readlines()
                        log_files.append(
                            {
                                "filename": filename,
                                "lines": lines[-100:] if len(lines) > 100 else lines,
                                "size": os.path.getsize(filepath),
                            }
                        )

        return jsonify({"success": True, "logs": log_files})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# WEBSOCKET HANDLERS - Chat & Real-time Updates
# ============================================================================


@socketio.on("connect")
def handle_connect():
    """Handle WebSocket connection"""
    if UTILS_AVAILABLE:
        logger.info(f"Client connected: {request.sid}")
    emit(
        "connected",
        {
            "message": "Connected to CEO Agent Executive AI System",
            "timestamp": datetime.now().isoformat(),
            "session_id": request.sid,
            "mode": system_settings["system_mode"],
        },
    )


@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnection"""
    if UTILS_AVAILABLE:
        logger.info(f"Client disconnected: {request.sid}")


@socketio.on("chat_message")
def handle_chat_message(data):
    """Handle incoming chat messages"""
    try:
        if UTILS_AVAILABLE:
            allowlist_validation = validate_payload_allowlist(
                data,
                allowed_fields={"message", "sender"},
                required_fields={"message"},
                payload_name="chat_message",
            )
            if not allowlist_validation.valid:
                emit(
                    "chat_error",
                    {
                        "errors": allowlist_validation.errors,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                return

        message = data.get("message", "").strip()
        sender = data.get("sender", "user")

        if UTILS_AVAILABLE:
            logger.info(f"Chat message from {sender}: {message[:100]}...")

            # Validate message
            validation = validate_chat_message(data)
            if not validation.valid:
                emit(
                    "chat_error",
                    {
                        "errors": validation.errors,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                return

        # Sanitize input
        if UTILS_AVAILABLE:
            message = sanitize_input(message, max_length=5000)

        # Echo message back to all clients
        emit(
            "chat_message",
            {
                "message": message,
                "sender": sender,
                "timestamp": datetime.now().isoformat(),
            },
            broadcast=True,
        )

        # Process commands if from user
        if sender == "user":
            response = process_chat_command(message)
            if response:
                socketio.emit(
                    "chat_message",
                    {
                        "message": response,
                        "sender": "assistant",
                        "timestamp": datetime.now().isoformat(),
                    },
                    broadcast=True,
                )

    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f"Error handling chat message: {str(e)}", exc_info=True)
        emit("chat_error", {"error": str(e), "timestamp": datetime.now().isoformat()})


# ============================================================================
# LLM-BACKED AGENT CHAT  (v0.4)
# Per-session, per-agent conversational memory powered by LangChain ChatOpenAI
# ============================================================================

# In-memory conversation history: {(flask_request_sid, agent_role): [messages]}
_CHAT_SESSIONS: dict = {}

_AGENT_PERSONAS: dict = {
    "ceo": (
        "You are the CEO Agent for {company_name}, a {industry} company in {location}.\n"
        "You are the top-level strategic orchestrator. You set company direction, coordinate "
        "agents, allocate budget, and make executive decisions.\n"
        "Current context: Total budget ${budget}, Timeline: {timeline} days.\n"
        "Speak with executive authority. Tie every decision back to business objectives. "
        "When challenged, defend your position with business reasoning. Keep responses to "
        "2-4 paragraphs."
    ),
    "cfo": (
        "You are the CFO Agent for {company_name}, a {industry} company in {location}.\n"
        "You own financial oversight: budget management, ROI analysis, cost structures, "
        "and financial risk. You speak in numbers and financial metrics.\n"
        "Current context: Total budget ${budget}, Timeline: {timeline} days.\n"
        "Be skeptical of overspending. Always demand financial justification for proposals. "
        "Keep responses concise with clear financial framing."
    ),
    "cto": (
        "You are the CTO Agent for {company_name}, a {industry} company in {location}.\n"
        "You own all technical architecture decisions. You reviewed the Web Development "
        "agent's artifact recommending Next.js 15 App Router + React Three Fiber + "
        "8th Wall WebAR + Sanity CMS for the SurfaceCraft Studio countertop visualizer.\n"
        "Current context: Total budget ${budget}, Timeline: {timeline} days.\n"
        "Speak about tech stacks, scalability, engineering timelines, and technical risk. "
        "Be pragmatic about budget constraints. Defend sound technical choices with reasoning. "
        "Keep responses to 2-4 paragraphs."
    ),
    "legal": (
        "You are the Legal Agent for {company_name}, a {industry} company in {location}.\n"
        "You specialise in Ohio commercial law, business compliance, contracts, IP, "
        "and regulatory requirements for the {industry} sector.\n"
        "Current context: Budget ${budget}.\n"
        "Speak precisely and always flag risks. Frame everything as considerations to "
        "discuss with licensed counsel — never give definitive legal advice. "
        "Keep responses clear and structured."
    ),
}

_DEBATE_SUFFIX = (
    "\n\nIMPORTANT: The user has activated STRATEGIC DEBATE MODE. They will challenge your "
    "recommendations. You MUST defend your position with specific data, analogies, and "
    "industry evidence. Do not capitulate easily — push back constructively and ask "
    "clarifying questions to expose flaws in the user's argument."
)


def _get_llm_for_chat(temperature: float = 0.5):
    """Return a ChatOpenAI instance for conversational use."""
    try:
        from config import OPENAI_API_KEY, OPENAI_MODEL
        from langchain_openai import ChatOpenAI

        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set")
        return ChatOpenAI(
            model=OPENAI_MODEL,
            temperature=temperature,
            max_tokens=600,
            api_key=OPENAI_API_KEY,
        )
    except Exception as exc:
        if UTILS_AVAILABLE:
            logger.warning(f"Chat LLM factory failed: {exc}")
        return None


def _build_chat_system_prompt(agent: str, scenario: dict, debate_mode: bool = False) -> str:
    """Build a per-agent system prompt with current scenario context."""
    template = _AGENT_PERSONAS.get(agent, _AGENT_PERSONAS["ceo"])
    prompt = template.format(
        company_name=scenario.get("company_name", "your company"),
        industry=scenario.get("industry", "general business"),
        location=scenario.get("location", "the US"),
        budget=f'{scenario.get("budget", 5000):,.0f}',
        timeline=scenario.get("timeline", 30),
    )
    if debate_mode:
        prompt += _DEBATE_SUFFIX
    return prompt


def llm_chat_response(
    session_key: tuple,
    agent: str,
    user_message: str,
    scenario: dict,
    debate_mode: bool = False,
) -> str:
    """
    Call the LLM with per-session memory and return the agent's response.
    Falls back to process_chat_command if LLM is unavailable.
    """
    llm = _get_llm_for_chat()
    if llm is None:
        fallback = process_chat_command(user_message)
        return (
            fallback
            or f"[{agent.upper()} Agent] {user_message} — (LLM unavailable, key not configured)"
        )

    history = _CHAT_SESSIONS.setdefault(session_key, [])

    # Trim history to last 20 exchanges to stay within context window
    if len(history) > 40:
        history[:] = history[-40:]

    history.append({"role": "user", "content": user_message})

    try:
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

        system_prompt = _build_chat_system_prompt(agent, scenario, debate_mode)
        lc_messages = [SystemMessage(content=system_prompt)]
        for msg in history[:-1]:  # exclude the message we just appended
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            else:
                lc_messages.append(AIMessage(content=msg["content"]))
        lc_messages.append(HumanMessage(content=user_message))

        response = llm.invoke(lc_messages)
        assistant_text: str = response.content.strip()
        history.append({"role": "assistant", "content": assistant_text})
        return assistant_text

    except Exception as exc:
        if UTILS_AVAILABLE:
            logger.error(f"LLM chat error: {exc}", exc_info=True)
        fallback = process_chat_command(user_message)
        return fallback or f"[{agent.upper()} Agent] I'm temporarily unavailable. Please try again."


@socketio.on("ai_chat_request")
def handle_ai_chat_request(data):
    """
    v0.4 LLM-backed agent chat via SocketIO.
    Client emits: {message, agent, debate_mode, scenario}
    Server emits: ai_chat_response {message, agent, timestamp}
    """
    try:
        message = str(data.get("message", "")).strip()[:2000]  # cap at 2000 chars
        agent = str(data.get("agent", "ceo")).lower()
        debate_mode = bool(data.get("debate_mode", False))
        scenario = data.get("scenario", {}) or {}

        if not message:
            return

        if agent not in _AGENT_PERSONAS:
            agent = "ceo"

        # Use request.sid as session identifier
        try:
            from flask import request as flask_request

            sid = flask_request.sid
        except Exception:
            sid = "anon"

        session_key = (sid, agent)
        response_text = llm_chat_response(session_key, agent, message, scenario, debate_mode)

        emit(
            "ai_chat_response",
            {
                "message": response_text,
                "agent": agent,
                "timestamp": datetime.now().isoformat(),
                "debate_mode": debate_mode,
            },
        )
    except Exception as exc:
        if UTILS_AVAILABLE:
            logger.error(f"ai_chat_request error: {exc}", exc_info=True)
        # Always emit ai_chat_response so the client gets feedback
        _fallback = "I'm temporarily unable to process that request. Please try again in a moment."
        emit(
            "ai_chat_response",
            {
                "message": _fallback,
                "agent": "system",
                "timestamp": datetime.now().isoformat(),
                "debate_mode": False,
                "error": True,
            },
        )


@app.route("/api/chat/message", methods=["POST"])
def api_chat_message():
    """
    REST endpoint for LLM-backed agent chat (alternative to SocketIO).
    Body: {message, agent, debate_mode, scenario, session_id}
    Returns: {response, agent, timestamp}
    """
    try:
        body = request.get_json(silent=True) or {}
        message = str(body.get("message", "")).strip()[:2000]  # cap at 2000 chars
        agent = str(body.get("agent", "ceo")).lower()
        debate_mode = bool(body.get("debate_mode", False))
        scenario = body.get("scenario", {}) or {}
        session_id = str(body.get("session_id", session.get("_id", "anon")))[
            :128
        ]  # cap session_id length

        if not message:
            return jsonify({"error": "message is required"}), 400

        if agent not in _AGENT_PERSONAS:
            agent = "ceo"

        session_key = (session_id, agent)
        response_text = llm_chat_response(session_key, agent, message, scenario, debate_mode)

        return jsonify(
            {
                "response": response_text,
                "agent": agent,
                "timestamp": datetime.now().isoformat(),
                "debate_mode": debate_mode,
            }
        )
    except Exception as exc:
        if UTILS_AVAILABLE:
            logger.error(f"api_chat_message error: {exc}", exc_info=True)
        return jsonify({"error": str(exc)}), 500


@app.route("/api/chat/clear", methods=["POST"])
def api_chat_clear():
    """Clear conversation history for a session+agent pair."""
    body = request.get_json(silent=True) or {}
    agent = str(body.get("agent", "ceo")).lower()
    session_id = str(body.get("session_id", session.get("_id", "anon")))
    session_key = (session_id, agent)
    _CHAT_SESSIONS.pop(session_key, None)
    return jsonify({"cleared": True, "agent": agent})


def process_chat_command(message: str) -> str:
    """Process chat commands and return response (legacy keyword fallback)"""
    lower_msg = message.lower()

    # Status query
    if "status" in lower_msg:
        return "System is operational. All agents are ready for execution."

    # Budget query
    if "budget" in lower_msg:
        return "Total budget: $5,000. Use the dashboard to track spending."

    # Agent list
    if "agent" in lower_msg and ("list" in lower_msg or "available" in lower_msg):
        return "Available agents: Branding, Web Development, Legal, MarTech, Content, Campaigns"

    return None


@socketio.on("agent_status_update")
def handle_agent_status(data):
    """Handle agent status updates"""
    try:
        if UTILS_AVAILABLE:
            allowlist_validation = validate_payload_allowlist(
                data,
                allowed_fields={"agent_type", "status"},
                required_fields={"agent_type", "status"},
                payload_name="agent_status_update",
            )
            if not allowlist_validation.valid:
                return

        agent_type = data.get("agent_type")
        status = data.get("status")

        if UTILS_AVAILABLE:
            logger.info(f"Agent status update: {agent_type} - {status}")

        emit(
            "agent_status_update",
            {
                "agent_type": agent_type,
                "status": status,
                "timestamp": datetime.now().isoformat(),
            },
            broadcast=True,
        )

    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f"Error handling agent status: {str(e)}", exc_info=True)


@socketio.on("execute_full_orchestration")
def handle_full_orchestration(data):
    """Execute full CFO orchestration in background"""
    if UTILS_AVAILABLE:
        allowlist_validation = validate_payload_allowlist(
            data,
            allowed_fields={"company_info", "objectives"},
            required_fields={"company_info", "objectives"},
            payload_name="full_orchestration",
        )
        if not allowlist_validation.valid:
            socketio.emit(
                "orchestration_error",
                {"error": "; ".join(allowlist_validation.errors)},
                to=None,
            )
            return

        company_info_validation = validate_company_info_allowlist(data.get("company_info", {}))
        if not company_info_validation.valid:
            socketio.emit(
                "orchestration_error",
                {"error": "; ".join(company_info_validation.errors)},
                to=None,
            )
            return

    if UTILS_AVAILABLE:
        logger.info(f"Full orchestration request received: {data}")
    else:
        print(f"🚀 Full orchestration request received: {data}")

    incoming_company_info = data.get("company_info", {})
    incoming_objectives = data.get("objectives", [])
    normalized_scenario = _normalize_scenario_context(
        incoming_company_info,
        incoming_objectives,
    )
    _update_shared_scenario_context(
        normalized_scenario,
        source="socket_orchestration",
        broadcast=True,
        user_modified=True,
    )

    def run_orchestration():
        try:
            print("📡 Emitting orchestration_started")
            socketio.emit(
                "orchestration_started",
                {"timestamp": datetime.now().isoformat()},
                to=None,
            )

            if not CEO_AGENT_AVAILABLE:
                raise RuntimeError("CEO agent is not available")

            # Create state matching CEOAgentState schema
            company_info = {
                "company_name": normalized_scenario["company_name"],
                "name": normalized_scenario["company_name"],
                "dba_name": normalized_scenario["dba_name"],
                "industry": normalized_scenario["industry"],
                "location": normalized_scenario["location"],
                "budget": normalized_scenario["budget"],
                "timeline": normalized_scenario["timeline"],
            }
            state = {
                # Company context
                "company_name": normalized_scenario["company_name"],
                "industry": normalized_scenario["industry"],
                "location": normalized_scenario["location"],
                "business_goals": [],
                # Strategic objectives
                "strategic_objectives": normalized_scenario["objectives"],
                # Budget management
                "total_budget": float(normalized_scenario["budget"]),
                "budget_allocated": {},
                "budget_reserved_for_fees": 0,
                "pending_approvals": [],
                "approved_actions": [],
                "rejected_actions": [],
                "pending_payments": [],
                # Timeline
                "target_completion_days": int(normalized_scenario["timeline"]),
                "current_day": 0,
                "milestones": [],
                # Multi-agent orchestration
                "active_agents": [],
                "agent_outputs": [],
                "agent_status": {},
                "delegated_tasks": {},
                # Task breakdown
                "identified_tasks": [],
                "assigned_tasks": {},
                "completed_tasks": [],
                "blocked_tasks": [],
                # Risk management
                "risks": [],
                "risk_mitigation_plans": {},
                "opportunities": [],
                "opportunity_analysis": [],
                # Deliverables
                "deliverables": [],
                "status_reports": [],
                "final_executive_summary": "",
                # Governance
                "guard_rail_violations": [],
                "liability_warnings": [],
                "compliance_status": {},
                "executive_decisions": [],
                # Workflow
                "current_phase": "initialization",
                "completed_phases": [],
            }

            print("🔄 Running strategic analysis phase...")
            # Analyze objectives
            socketio.emit("phase", {"name": "Strategic Analysis", "status": "running"}, to=None)
            state = ceo_analyze(state)
            socketio.emit(
                "phase",
                {
                    "name": "Strategic Analysis",
                    "status": "complete",
                    "tasks": state.get("identified_tasks", []),
                },
                to=None,
            )
            print(f"✅ Strategic analysis complete. Tasks: {len(state.get('identified_tasks', []))}")

            # Deploy agents - dynamically include current and future available agents
            print("🤖 Deploying agents...")
            socketio.emit("phase", {"name": "Agent Deployment", "status": "running"}, to=None)

            factory = AgentFactory()
            available_agents = list(factory.get_available_agents())
            task_map = {
                task.get("required_expertise", "").lower(): task
                for task in state.get("identified_tasks", [])
                if task.get("required_expertise")
            }

            execution_order = []
            for task in state.get("identified_tasks", []):
                agent_type = task.get("required_expertise", "").lower()
                if (
                    agent_type
                    and agent_type in available_agents
                    and agent_type not in execution_order
                ):
                    execution_order.append(agent_type)

            # Ensure any newly available agents are still orchestrated
            for agent_type in available_agents:
                if agent_type not in execution_order:
                    execution_order.append(agent_type)

            total_budget_used = 0
            for agent_type in execution_order:
                task = task_map.get(agent_type, {})
                task_id = task.get("task_id", f"AUTO_{agent_type.upper()}")

                print(f"  - Deploying {agent_type} agent")
                socketio.emit("agent_deploying", {"agent": agent_type, "task": task_id}, to=None)

                payload = {
                    "task": task.get("description", f"Execute {agent_type} workstream"),
                    "company_info": company_info,
                    "requirements": {
                        "objectives": normalized_scenario.get("objectives", []),
                        "task": task,
                    },
                }

                try:
                    agent_result = _execute_specialized_agent(agent_type, payload)
                    budget_used = float(agent_result.get("budget_used", 0) or 0)
                    total_budget_used += budget_used

                    state.setdefault("agent_outputs", []).append(
                        {
                            "agent": agent_type,
                            "agent_name": agent_result.get("agent_name", agent_type),
                            "summary": f"{agent_result.get('status', 'executed')} - {len(agent_result.get('deliverables', []))} deliverables",
                            "result": agent_result,
                        }
                    )
                    state.setdefault("deliverables", []).extend(
                        agent_result.get("deliverables", [])
                    )
                    state.setdefault("completed_tasks", []).append(task_id)
                    state.setdefault("agent_status", {})[agent_type] = "success"

                    socketio.emit(
                        "agent_deployed",
                        {"agent": agent_type, "status": "success"},
                        to=None,
                    )
                except Exception as agent_error:
                    state.setdefault("agent_status", {})[agent_type] = "failed"
                    state.setdefault("risks", []).append(
                        {
                            "category": "agent_execution",
                            "description": f"{agent_type} execution failed: {agent_error}",
                            "mitigation": "Review logs and retry agent execution",
                        }
                    )
                    socketio.emit(
                        "agent_deployed",
                        {"agent": agent_type, "status": "failed"},
                        to=None,
                    )

            print("✅ Orchestration complete")

            # Prepare comprehensive orchestration report
            orchestration_report = {
                "status": "success",
                "company_name": state.get("company_name", "Company"),
                "industry": state.get("industry", "N/A"),
                "location": state.get("location", "N/A"),
                "budget_used": total_budget_used,
                "budget_remaining": state.get("total_budget", 0) - total_budget_used,
                "total_budget": state.get("total_budget", 5000),
                "tasks": state.get("identified_tasks", []),
                "completed_tasks": len(state.get("completed_tasks", [])),
                "total_tasks": len(execution_order),
                "budget_allocation": state.get("budget_allocated", {}),
                "risks": state.get("risks", []),
                "opportunities": state.get("opportunities", []),
                "deliverables": state.get("deliverables", []),
                "agent_outputs": state.get("agent_outputs", []),
                "current_phase": state.get("current_phase", "complete"),
                "timeline": state.get("target_completion_days", 90),
                "timestamp": datetime.now().isoformat(),
            }

            with shared_state_lock:
                shared_runtime_state["last_orchestration_report"] = copy.deepcopy(
                    orchestration_report
                )

            socketio.emit("orchestration_complete", orchestration_report, to=None)

        except Exception as e:
            print(f"❌ Orchestration error: {str(e)}")
            import traceback

            traceback.print_exc()
            socketio.emit("orchestration_error", {"error": str(e)}, to=None)

    thread = threading.Thread(target=run_orchestration)
    thread.start()
    print("🔄 Orchestration thread started")


if __name__ == "__main__":
    # Create templates directory if it doesn't exist
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static/css", exist_ok=True)
    os.makedirs("static/js", exist_ok=True)

    print("\n" + "=" * 80)
    print("👔 CEO EXECUTIVE AGENT - AI ORCHESTRATION SYSTEM")
    print("=" * 80)

    print("\n🌐 SERVER ENDPOINTS:")
    print("   Main Dashboard:   http://localhost:5001")
    print("   Admin Dashboard:  http://localhost:5001/admin")
    print("   Alternative:      http://127.0.0.1:5001/admin")

    print("\n💡 FEATURES:")
    print("   ✅ CEO Executive Orchestration")
    print("   ✅ Multi-Agent Strategy Engine (6 Specialized Agents)")
    print("   ✅ Financial Guard Rails & Budget Tracking")
    print("   ✅ Real-time SocketIO Communication")
    print("   ✅ Payment Approval Workflow")
    print("   ✅ Agent Training Interface")

    print("\n🔒 SECURITY STATUS:")
    print("   ✅ XSS Protection (HTML Escaping)")
    print("   ✅ Input Sanitization (Regex Filters)")
    print("   ✅ Content Security Policy (CSP)")
    print("   ✅ Security Headers (X-Frame-Options, X-Content-Type-Options, etc.)")
    print("   ✅ Request Size Limits (10MB)")
    print("   ✅ CORS Protection")
    print("   ✅ Structured Logging with Rotation")
    print("   ⚠️  Authentication: NOT CONFIGURED")
    print("   ⚠️  Rate Limiting: NOT CONFIGURED")
    print("   ⚠️  HTTPS/TLS: NOT CONFIGURED (development mode)")

    print("\n📚 DOCUMENTATION:")
    print("   • README.md - Project overview & setup")
    print("   • SECURITY_AUDIT_2026.md - Comprehensive security audit (B+ rating)")
    print("   • SECURITY_PATCH_FEB_2026.md - XSS vulnerability fixes")
    print("   • docs/archive/CODE_REVIEW_SENIOR_CONSULTANT.md - Engineering recommendations")
    print("   • tests/README.md - Testing guide & best practices")

    print("\n⚙️  ENVIRONMENT:")
    print(f"   Mode: {os.getenv('ENVIRONMENT', 'development').upper()}")
    print(f"   Debug: {os.getenv('DEBUG', 'False')}")
    print(f"   System Mode: TRAINING")
    print("   🎓 Agents in development - train before production")

    print("\n⚠️  DEVELOPMENT SERVER ACTIVE")
    print("   For production deployment, use:")
    print("   gunicorn -w 4 -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker app:app")

    print("\n🚀 NEXT STEPS:")
    print("   1. Run tests: pytest tests/ -v --cov=.")
    print("   2. Implement authentication (see SECURITY_AUDIT_2026.md)")
    print("   3. Add rate limiting (Flask-Limiter)")
    print("   4. Configure production environment")

    print("\n🛑 Press CTRL+C to stop")
    print("=" * 80 + "\n")

    socketio.run(app, debug=False, host="0.0.0.0", port=5001, allow_unsafe_werkzeug=True)
