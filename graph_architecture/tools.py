"""
Tool Registry — Graph-Wired Domain Tools

Design rules:
  • Tools are PURE FUNCTIONS dispatched by the GRAPH, not by the model.
  • Each tool accepts typed inputs and returns typed dict outputs.
  • Tools never modify global state directly.
  • Sensitive tools (finance, code execution) are guarded by role check.
  • Tool outputs remain INSIDE their subgraph until summarised by LLM node.

Tool catalogue:
  FINANCE    — query_budget, run_cost_model, audit_policy_check
  ENGINEERING — generate_tech_spec, run_dependency_check, validate_architecture
  RESEARCH   — web_search_summary, competitive_analysis, benchmarking
  COMMON     — log_audit_entry, persist_output
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# TOOL RESULT WRAPPER
# ─────────────────────────────────────────────────────────────────────────────


def _ok(tool_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "tool": tool_name,
        "status": "success",
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "trace_id": uuid.uuid4().hex[:8],
    }


def _err(tool_name: str, message: str, data: Optional[Dict] = None) -> Dict[str, Any]:
    return {
        "tool": tool_name,
        "status": "error",
        "error": message,
        "data": data or {},
        "timestamp": datetime.now().isoformat(),
        "trace_id": uuid.uuid4().hex[:8],
    }


# ─────────────────────────────────────────────────────────────────────────────
# FINANCE TOOLS  (CFO subgraph only)
# ─────────────────────────────────────────────────────────────────────────────


def query_budget(
    total_budget: float,
    allocated: Dict[str, float],
    spent: Dict[str, float],
    current_day: int = 1,
    target_days: int = 90,
) -> Dict[str, Any]:
    """
    Compute budget health metrics from raw budget state.
    Pure calculation — no external calls.
    """
    tool = "query_budget"
    try:
        total_allocated = sum(allocated.values())
        total_spent = sum(spent.values())
        remaining = total_budget - total_allocated
        utilisation_pct = (total_allocated / total_budget * 100) if total_budget > 0 else 0.0
        burn_rate = total_spent / max(current_day, 1)
        days_remaining = target_days - current_day
        projected_total = total_spent + (burn_rate * days_remaining)
        projected_overrun = max(projected_total - total_budget, 0.0)
        health_score = max(0, min(100, int(100 - utilisation_pct)))

        return _ok(
            tool,
            {
                "total_budget": total_budget,
                "total_allocated": round(total_allocated, 2),
                "total_spent": round(total_spent, 2),
                "remaining": round(remaining, 2),
                "utilisation_pct": round(utilisation_pct, 1),
                "burn_rate_per_day": round(burn_rate, 2),
                "projected_total_spend": round(projected_total, 2),
                "projected_overrun": round(projected_overrun, 2),
                "health_score": health_score,
                "allocation_by_agent": allocated,
                "spend_by_agent": spent,
            },
        )
    except Exception as exc:
        return _err(tool, str(exc))


def run_cost_model(
    tasks: List[Dict[str, Any]],
    contingency_pct: float = 0.15,
) -> Dict[str, Any]:
    """
    Build cost breakdown from identified tasks with contingency.
    """
    tool = "run_cost_model"
    try:
        base_cost = sum(t.get("estimated_budget", 0) for t in tasks)
        contingency = base_cost * contingency_pct
        total = base_cost + contingency

        by_domain: Dict[str, float] = {}
        for t in tasks:
            domain = t.get("domain", "unknown")
            by_domain.setdefault(domain, 0.0)
            by_domain[domain] += t.get("estimated_budget", 0)

        critical_items = [
            t["task_name"] for t in tasks if t.get("priority") in ("critical", "CRITICAL")
        ]

        return _ok(
            tool,
            {
                "base_cost": round(base_cost, 2),
                "contingency_pct": contingency_pct,
                "contingency_amount": round(contingency, 2),
                "total_estimated_cost": round(total, 2),
                "cost_by_domain": {k: round(v, 2) for k, v in by_domain.items()},
                "critical_cost_items": critical_items,
                "task_count": len(tasks),
            },
        )
    except Exception as exc:
        return _err(tool, str(exc))


def audit_policy_check(
    tasks: List[Dict[str, Any]],
    total_budget: float,
    risk_threshold: str = "medium",
) -> Dict[str, Any]:
    """
    Check tasks against financial policy rules.
    Returns violations and a pass/fail verdict.
    """
    tool = "audit_policy_check"
    risk_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    threshold_level = risk_order.get(risk_threshold, 1)

    violations: List[str] = []
    warnings: List[str] = []

    for t in tasks:
        task_budget = t.get("estimated_budget", 0)
        task_risk = risk_order.get(str(t.get("risk_level", "low")).lower(), 0)

        # Rule 1: No single task >40% of total budget
        if total_budget > 0 and task_budget > total_budget * 0.4:
            violations.append(
                f"Task '{t.get('task_name')}' exceeds 40% of total budget "
                f"(${task_budget:,.0f} / ${total_budget:,.0f})"
            )

        # Rule 2: High-risk tasks need explicit approval
        if task_risk > threshold_level:
            warnings.append(
                f"Task '{t.get('task_name')}' risk level '{t.get('risk_level')}' "
                f"exceeds threshold '{risk_threshold}' — approval recommended"
            )

    passed = len(violations) == 0

    return _ok(
        tool,
        {
            "passed": passed,
            "violations": violations,
            "warnings": warnings,
            "violation_count": len(violations),
            "warning_count": len(warnings),
            "policy_threshold": risk_threshold,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# ENGINEERING TOOLS  (Engineer subgraph only)
# ─────────────────────────────────────────────────────────────────────────────


def validate_architecture(
    tech_stack: List[str],
    estimated_days: int,
    budget_ceiling: float,
    team_size: int = 3,
) -> Dict[str, Any]:
    """
    Validate architecture feasibility against constraints.
    Static heuristics — no LLM.
    """
    tool = "validate_architecture"

    issues: List[str] = []
    recommendations: List[str] = []

    # Heuristic: rough cost per dev-day
    dev_day_cost = 500  # $500/dev/day
    cost_estimate = estimated_days * team_size * dev_day_cost

    if budget_ceiling > 0 and cost_estimate > budget_ceiling:
        issues.append(
            f"Estimated engineering cost (${cost_estimate:,.0f}) exceeds budget "
            f"ceiling (${budget_ceiling:,.0f})"
        )
        recommendations.append("Reduce scope or increase budget ceiling before proceeding")

    if estimated_days > 180:
        issues.append("Timeline >180 days — consider phased delivery")
        recommendations.append("Break into 90-day phases with MVP first")

    if "monolith" in " ".join(tech_stack).lower() and estimated_days > 90:
        recommendations.append(
            "Consider microservices for long-running projects to enable independent deployment"
        )

    feasible = len(issues) == 0

    return _ok(
        tool,
        {
            "feasible": feasible,
            "estimated_cost": round(cost_estimate, 2),
            "estimated_days": estimated_days,
            "team_size": team_size,
            "issues": issues,
            "recommendations": recommendations,
            "tech_stack_validated": tech_stack,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# RESEARCH TOOLS  (Researcher subgraph only)
# ─────────────────────────────────────────────────────────────────────────────


def competitive_analysis_stub(
    industry: str,
    company_name: str,
    objectives: List[str],
) -> Dict[str, Any]:
    """
    Placeholder competitive analysis tool.
    In production, replace this with a real web search + scraping pipeline.
    Returns a structured stub that the Researcher LLM node can reason over.
    """
    tool = "competitive_analysis"
    logger.warning(
        "competitive_analysis_stub: returning placeholder data. "
        "Replace with real web search integration."
    )
    return _ok(
        tool,
        {
            "industry": industry,
            "note": "STUB — replace with real competitive intelligence API",
            "data_points": [
                {
                    "category": "Market size",
                    "value": "Requires real API call",
                    "confidence": "unavailable",
                },
                {
                    "category": "Top competitors",
                    "value": "Requires real API call",
                    "confidence": "unavailable",
                },
                {
                    "category": "Growth rate",
                    "value": "Requires real API call",
                    "confidence": "unavailable",
                },
            ],
            "objectives_analysed": objectives,
            "company": company_name,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# COMMON TOOLS  (Any agent)
# ─────────────────────────────────────────────────────────────────────────────


def log_audit_entry(
    agent_role: str,
    node_name: str,
    action: str,
    outcome: str,
    metadata: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Append a tamper-evident audit entry.
    SHA-256 hash of content provides basic integrity proof.
    """
    tool = "log_audit_entry"
    entry = {
        "agent_role": agent_role,
        "node_name": node_name,
        "action": action,
        "outcome": outcome,
        "metadata": metadata or {},
        "timestamp": datetime.now().isoformat(),
    }
    content_str = json.dumps(entry, sort_keys=True)
    entry["sha256"] = hashlib.sha256(content_str.encode()).hexdigest()

    logger.info(f"AUDIT [{agent_role}:{node_name}] {action} → {outcome}")
    return _ok(tool, {"audit_entry": entry})


def persist_output(
    agent_role: str,
    output_type: str,
    content: Dict[str, Any],
    output_dir: str = "./data/outputs",
) -> Dict[str, Any]:
    """
    Persist an agent output to disk as JSON.
    """
    import os

    tool = "persist_output"
    try:
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{output_dir}/{agent_role}_{output_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(content, f, indent=2, default=str)
        logger.info(f"Output persisted: {filename}")
        return _ok(tool, {"file": filename, "bytes": os.path.getsize(filename)})
    except Exception as exc:
        return _err(tool, str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# TOOL REGISTRY  (for graph-level dispatch)
# ─────────────────────────────────────────────────────────────────────────────

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Finance tools — CFO only
    "query_budget": {"fn": query_budget, "domain": "finance", "roles": ["cfo"]},
    "run_cost_model": {"fn": run_cost_model, "domain": "finance", "roles": ["cfo"]},
    "audit_policy_check": {"fn": audit_policy_check, "domain": "finance", "roles": ["cfo"]},
    # Engineering tools — engineer only
    "validate_architecture": {
        "fn": validate_architecture,
        "domain": "engineering",
        "roles": ["engineer"],
    },
    # Research tools — researcher only
    "competitive_analysis": {
        "fn": competitive_analysis_stub,
        "domain": "research",
        "roles": ["researcher"],
    },
    # Common tools — any role
    "log_audit_entry": {"fn": log_audit_entry, "domain": "common", "roles": ["*"]},
    "persist_output": {"fn": persist_output, "domain": "common", "roles": ["*"]},
}


def dispatch_tool(tool_name: str, agent_role: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Graph-level tool dispatcher.
    Validates role permissions before executing the tool.
    """
    entry = TOOL_REGISTRY.get(tool_name)
    if not entry:
        return _err(tool_name, f"Tool '{tool_name}' not found in registry")

    allowed_roles: List[str] = entry["roles"]
    if "*" not in allowed_roles and agent_role not in allowed_roles:
        return _err(
            tool_name,
            f"Agent '{agent_role}' not authorised to use tool '{tool_name}'. "
            f"Allowed: {allowed_roles}",
        )

    try:
        return entry["fn"](**kwargs)
    except TypeError as exc:
        return _err(tool_name, f"Tool call signature error: {exc}")
    except Exception as exc:
        return _err(tool_name, f"Tool execution error: {exc}")
