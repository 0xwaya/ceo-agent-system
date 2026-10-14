"""Deterministic governance review of dispatch decisions and execution evidence."""

import hashlib
import logging
import math
from decimal import Decimal
from typing import Any, Dict

from graph_architecture.approval_nodes import create_risk_escalation_request
from graph_architecture.schemas import CEOState, RiskLevel
from graph_architecture.llm_nodes import TIER2_NODE_MAP

logger = logging.getLogger(__name__)


def _amount(value: Any, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite non-negative number")
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{label} must be a finite non-negative number")
    return Decimal(str(value))


def cfo_skepticism_review(state: CEOState) -> Dict[str, Any]:
    """Review structured evidence only; never infer execution from planning prose."""
    flags = []
    approvals = []
    existing = {flag["flag_id"] for flag in state.get("cfo_flags", [])}
    approved = set(state.get("approved_actions", []))

    def flag(code, subject, severity, message, cost=0.0):
        identifier = hashlib.sha256(f"{code}:{subject}".encode()).hexdigest()[:16]
        flag_id = f"cfo-{identifier}"
        if flag_id in existing:
            return
        existing.add(flag_id)
        request = create_risk_escalation_request(
            action=f"CFO review: {code} ({subject})",
            risk_level=RiskLevel(severity),
            rationale=message,
            estimated_cost=cost,
        )
        request.request_id = f"risk-{flag_id}"
        flags.append(
            {
                "flag_id": flag_id,
                "code": code,
                "subject": subject,
                "severity": severity,
                "message": message,
                "approval_request_id": request.request_id,
            }
        )
        if request.request_id not in approved:
            approvals.append(request)
        logger.warning("CFO skepticism [%s] %s: %s", severity, subject, message)

    for role in state.get("dispatch_plan", []):
        if role not in TIER2_NODE_MAP:
            flag("unknown_dispatch_role", str(role), "critical", f"Unrecognized role: {role}")

    decisions = state.get("executive_decisions", [])
    routing = state.get("llm_routing_decision", {})
    if routing and not str(routing.get("rationale") or "").strip():
        flag("missing_ceo_rationale", "dispatch_plan", "medium", "CEO dispatch has no rationale.")
    for index, decision in enumerate(decisions):
        if not str(decision.get("rationale") or "").strip():
            flag(
                "missing_ceo_rationale",
                decision.get("decision_id") or f"decision-{index}",
                "medium",
                "CEO decision has no rationale.",
            )

    spent = {
        role: _amount(value, f"budget_spent[{role}]")
        for role, value in state.get("budget_spent", {}).items()
    }
    approved_budget = None
    external_evidence = False
    output_spend = {}
    outputs = state.get("agent_outputs", [])
    for index, output in enumerate(outputs):
        role = output.get("agent", "unknown")
        summary = output.get("summary", {})
        if not isinstance(summary, dict):
            raise ValueError(f"Output {index} summary must be an object")
        if role == "cfo":
            approved_budget = None
            if summary.get("recommendation") == "approve":
                numbers = summary.get("key_numbers") or {}
                if "total_budget" in numbers:
                    approved_budget = _amount(numbers["total_budget"], "CFO approved budget")

        actions = summary.get("actions", [])
        if not isinstance(actions, list) or any(not isinstance(a, dict) for a in actions):
            raise ValueError(f"Output {index} actions must be a list of objects")
        output_cost = _amount(summary.get("budget_used", 0), f"{role} budget_used")
        action_cost = Decimal(0)
        for action_index, action in enumerate(actions):
            subject = f"{index}:{role}:{action.get('action_id') or action_index}"
            cost = _amount(action.get("cost", 0), f"{subject} cost")
            action_cost += cost
            if action.get("irreversible") is True:
                if action.get("approval_request_id") not in approved:
                    flag(
                        "unapproved_irreversible_action",
                        subject,
                        "critical",
                        "Irreversible action has no matching approval on file.",
                        cost,
                    )
            if action.get("external_side_effect") is True:
                external_evidence = True
                if cost == 0:
                    flag(
                        "untracked_external_cost",
                        subject,
                        "high",
                        "External side effect has zero tracked cost.",
                    )
        if summary.get("external_actions_executed") is True:
            external_evidence = True
            if max(output_cost, action_cost, spent.get(role, 0)) == 0:
                flag(
                    "untracked_external_cost",
                    f"{index}:{role}",
                    "high",
                    "Agent reports external execution with zero tracked cost.",
                )
        # A ledger entry and output costs can describe the same spend.
        output_spend[role] = output_spend.get(role, 0) + max(output_cost, action_cost)

    for role, cost in output_spend.items():
        spent[role] = max(spent.get(role, 0), cost)

    total_spent = sum(spent.values(), Decimal(0))
    if not math.isfinite(float(total_spent)):
        raise ValueError("Total tracked spend exceeds the supported finite range")
    if total_spent > 0 and (approved_budget is None or total_spent > approved_budget):
        flag(
            "spend_overrun",
            "budget",
            "high",
            (
                f"Tracked spend ${total_spent:,.2f} exceeds CFO approval "
                f"${approved_budget:,.2f}."
                if approved_budget is not None
                else f"Tracked spend ${total_spent:,.2f} has no unconditional CFO approval."
            ),
            total_spent,
        )

    all_flags = [*state.get("cfo_flags", []), *flags]
    pending_ids = {
        request.request_id if hasattr(request, "request_id") else request["request_id"]
        for request in state.get("pending_approvals", [])
    } | {request.request_id for request in approvals}
    requires_approval = any(
        item["severity"] in {"high", "critical"}
        and item["approval_request_id"] in pending_ids
        and item["approval_request_id"] not in approved
        for item in all_flags
    )
    return {
        "cfo_flags": flags,
        "pending_approvals": approvals,
        "cfo_skepticism_report": {
            "flags": all_flags,
            "outputs_reviewed": len(outputs),
            "tracked_spend": float(total_spent),
            "cfo_approved_budget": float(approved_budget) if approved_budget is not None else None,
            "external_actions_reported": external_evidence,
            "requires_approval": requires_approval,
        },
        "current_phase": "awaiting_approval" if requires_approval else "cfo_review_complete",
    }


def route_after_skepticism(state: CEOState) -> str:
    return (
        "approval"
        if state.get("cfo_skepticism_report", {}).get("requires_approval")
        else "consolidate"
    )
