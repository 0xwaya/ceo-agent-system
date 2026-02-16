"""
Human-in-the-Loop Approval Nodes

Implements interrupt-based approvals for:
1. Budget approvals
2. Risk escalations
3. Critical decisions
4. Payment authorizations
5. Contract signings
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid

from langgraph.graph import END
from langgraph.checkpoint.base import Checkpoint

from graph_architecture.schemas import (
    SharedState,
    ApprovalRequest,
    AgentRole,
    RiskLevel,
    TaskPriority,
    Message,
    MessageType,
)

logger = logging.getLogger(__name__)


# ============================================================================
# APPROVAL NODE
# ============================================================================


def human_approval_node(state: SharedState) -> SharedState:
    """
    Human-in-the-loop approval checkpoint

    This node pauses execution and waits for user input.
    The graph will interrupt here until approval is received.

    Args:
        state: Current shared state

    Returns:
        Updated state (execution pauses here)
    """
    # Check if there are pending approvals
    pending = state.get("pending_approvals", [])

    if not pending:
        logger.info("No pending approvals, continuing execution")
        return state

    # Log approval checkpoint
    logger.info(f"APPROVAL REQUIRED: {len(pending)} pending approvals")

    for approval_request in pending:
        logger.info(
            f"  - {approval_request.action}: ${approval_request.cost} "
            f"(risk: {approval_request.risk_level})"
        )

    # Create checkpoint metadata
    state["current_phase"] = "awaiting_approval"

    # Execution will interrupt here
    # User must call graph.update_state() to provide approval
    return state


def process_approval_response(state: SharedState, approval_response: Dict[str, Any]) -> SharedState:
    """
    Process user's approval response

    Called after user provides approval via graph.update_state()

    Args:
        state: Current state
        approval_response: User's approval decision
            {
                "request_id": str,
                "approved": bool,
                "notes": Optional[str],
                "modified_cost": Optional[float]
            }

    Returns:
        Updated state with approval processed
    """
    request_id = approval_response.get("request_id")
    approved = approval_response.get("approved", False)
    notes = approval_response.get("notes", "")

    # Find the approval request
    pending = state.get("pending_approvals", [])
    request = next((r for r in pending if r.request_id == request_id), None)

    if not request:
        logger.error(f"Approval request {request_id} not found")
        return state

    # Remove from pending
    state["pending_approvals"] = [r for r in pending if r.request_id != request_id]

    if approved:
        # Add to approved actions
        state["approved_actions"].append(request_id)

        logger.info(f"✅ APPROVED: {request.action} (${request.cost}) - {notes}")

        # Update budget if needed
        modified_cost = approval_response.get("modified_cost")
        if modified_cost and modified_cost != request.cost:
            logger.info(f"Budget adjusted: ${request.cost} → ${modified_cost}")
            # Update state with modified cost
            # (Implementation depends on specific use case)
    else:
        # Add to rejected actions
        state["rejected_actions"].append(request_id)

        logger.warning(f"❌ REJECTED: {request.action} (${request.cost}) - {notes}")

        # Mark dependent tasks as blocked
        state["blocked_tasks"].append(
            {
                "reason": f"Approval rejected: {request.action}",
                "timestamp": datetime.now().isoformat(),
                "notes": notes,
            }
        )

    return state


# ============================================================================
# APPROVAL REQUEST BUILDERS
# ============================================================================


def create_budget_approval_request(
    action: str,
    cost: float,
    rationale: str,
    risk_level: RiskLevel = RiskLevel.MEDIUM,
    auto_decline_hours: Optional[int] = None,
) -> ApprovalRequest:
    """
    Create budget approval request

    Args:
        action: Description of action requiring approval
        cost: Cost in dollars
        rationale: Why this is needed
        risk_level: Risk assessment
        auto_decline_hours: Auto-decline after X hours

    Returns:
        ApprovalRequest instance
    """
    request_id = f"approval-{uuid.uuid4().hex[:8]}"

    auto_decline_after = None
    if auto_decline_hours:
        auto_decline_after = (datetime.now() + timedelta(hours=auto_decline_hours)).isoformat()

    return ApprovalRequest(
        request_id=request_id,
        action=action,
        rationale=rationale,
        cost=cost,
        risk_level=risk_level,
        consequences_if_declined=(f"Task cannot proceed. Budget of ${cost} will not be allocated."),
        auto_decline_after=auto_decline_after,
    )


def create_risk_escalation_request(
    action: str, risk_level: RiskLevel, rationale: str, estimated_cost: float = 0.0
) -> ApprovalRequest:
    """
    Create risk escalation approval request

    Args:
        action: High-risk action
        risk_level: Risk assessment
        rationale: Explanation of risks
        estimated_cost: Associated cost

    Returns:
        ApprovalRequest instance
    """
    request_id = f"risk-{uuid.uuid4().hex[:8]}"

    consequences = {
        RiskLevel.CRITICAL: "System may fail or incur significant liability",
        RiskLevel.HIGH: "Potential for business disruption or data loss",
        RiskLevel.MEDIUM: "Moderate impact to operations",
        RiskLevel.LOW: "Minimal impact",
    }

    return ApprovalRequest(
        request_id=request_id,
        action=action,
        rationale=rationale,
        cost=estimated_cost,
        risk_level=risk_level,
        consequences_if_declined=consequences.get(risk_level, "Unknown consequences"),
    )


# ============================================================================
# APPROVAL ROUTING
# ============================================================================


def route_to_approval(state: SharedState) -> str:
    """
    Conditional edge routing to approval node

    Args:
        state: Current state

    Returns:
        "approval" if approvals pending, else "continue"
    """
    pending = state.get("pending_approvals", [])

    if pending:
        logger.info(f"Routing to approval node ({len(pending)} pending)")
        return "approval"
    else:
        return "continue"


def check_approval_status(state: SharedState) -> str:
    """
    Check if all approvals are processed

    Args:
        state: Current state

    Returns:
        "complete" if no pending approvals, else "wait"
    """
    pending = state.get("pending_approvals", [])

    if not pending:
        return "complete"
    else:
        return "wait"


# ============================================================================
# AUTO-DECLINE MECHANISM
# ============================================================================


def check_auto_decline(state: SharedState) -> SharedState:
    """
    Check and process auto-declined approval requests

    Args:
        state: Current state

    Returns:
        Updated state with auto-declines processed
    """
    current_time = datetime.now()
    pending = state.get("pending_approvals", [])

    still_pending = []
    auto_declined = []

    for request in pending:
        if request.auto_decline_after:
            decline_time = datetime.fromisoformat(request.auto_decline_after)

            if current_time > decline_time:
                # Auto-decline
                auto_declined.append(request)
                logger.warning(
                    f"AUTO-DECLINED: {request.action} "
                    f"(timeout after {request.auto_decline_after})"
                )
            else:
                still_pending.append(request)
        else:
            still_pending.append(request)

    # Update state
    state["pending_approvals"] = still_pending

    for request in auto_declined:
        state["rejected_actions"].append(request.request_id)
        state["blocked_tasks"].append(
            {"reason": f"Auto-declined: {request.action}", "timestamp": current_time.isoformat()}
        )

    return state


# ============================================================================
# BATCH APPROVAL HANDLING
# ============================================================================


def create_batch_approval_summary(state: SharedState) -> Dict[str, Any]:
    """
    Create summary of all pending approvals for user

    Args:
        state: Current state

    Returns:
        Summary dictionary
    """
    pending = state.get("pending_approvals", [])

    summary = {
        "total_pending": len(pending),
        "total_cost": sum(r.cost for r in pending),
        "by_risk_level": {},
        "by_priority": {},
        "requests": [],
    }

    # Group by risk level
    for risk_level in RiskLevel:
        count = sum(1 for r in pending if r.risk_level == risk_level)
        if count > 0:
            summary["by_risk_level"][risk_level.value] = count

    # Add individual requests
    for request in pending:
        summary["requests"].append(
            {
                "request_id": request.request_id,
                "action": request.action,
                "cost": request.cost,
                "risk_level": request.risk_level.value,
                "rationale": request.rationale,
                "auto_decline_after": request.auto_decline_after,
            }
        )

    return summary


def process_batch_approval(state: SharedState, batch_response: Dict[str, Any]) -> SharedState:
    """
    Process multiple approvals at once

    Args:
        state: Current state
        batch_response: Batch approval response
            {
                "approve_all": bool,
                "individual_approvals": [
                    {"request_id": str, "approved": bool, "notes": str},
                    ...
                ]
            }

    Returns:
        Updated state
    """
    if batch_response.get("approve_all"):
        # Approve all pending
        pending = state.get("pending_approvals", [])
        for request in pending:
            state["approved_actions"].append(request.request_id)
            logger.info(f"✅ BATCH APPROVED: {request.action}")

        state["pending_approvals"] = []
    else:
        # Process individual approvals
        for approval in batch_response.get("individual_approvals", []):
            state = process_approval_response(state, approval)

    return state


# ============================================================================
# APPROVAL NOTIFICATIONS
# ============================================================================


def send_approval_notification(
    state: SharedState, approval_request: ApprovalRequest, notification_channel: str = "email"
) -> None:
    """
    Send notification to user about pending approval

    Args:
        state: Current state
        approval_request: The approval request
        notification_channel: How to notify (email, sms, webhook)
    """
    # In real implementation, this would send email/SMS/webhook
    logger.info(
        f"NOTIFICATION [{notification_channel}]: "
        f"Approval required for {approval_request.action}"
    )

    # Could integrate with:
    # - SendGrid for email
    # - Twilio for SMS
    # - Slack/Discord webhooks
    # - Mobile push notifications


# ============================================================================
# CONDITIONAL APPROVAL LOGIC
# ============================================================================


class ConditionalApprovalRules:
    """
    Define rules for when approval is required
    """

    # Budget thresholds
    AUTO_APPROVE_THRESHOLD = 100.0  # Auto-approve under $100
    CRITICAL_APPROVAL_THRESHOLD = 10000.0  # Critical approval over $10k

    @classmethod
    def requires_approval(cls, cost: float, risk_level: RiskLevel, agent_role: AgentRole) -> bool:
        """
        Determine if approval is required

        Args:
            cost: Action cost
            risk_level: Risk assessment
            agent_role: Agent requesting action

        Returns:
            True if user approval required
        """
        # CEO can auto-approve up to threshold
        if agent_role == AgentRole.CEO and cost < cls.AUTO_APPROVE_THRESHOLD:
            return False

        # Critical risk always requires approval
        if risk_level == RiskLevel.CRITICAL:
            return True

        # High cost requires approval
        if cost > cls.CRITICAL_APPROVAL_THRESHOLD:
            return True

        # High risk with cost requires approval
        if risk_level == RiskLevel.HIGH and cost > 0:
            return True

        # Default: require approval for any cost
        return cost > 0


# ============================================================================
# INTERRUPT HELPERS
# ============================================================================


def create_interrupt_checkpoint(
    state: SharedState, interrupt_reason: str, required_action: str
) -> SharedState:
    """
    Create checkpoint that interrupts execution

    Args:
        state: Current state
        interrupt_reason: Why execution is paused
        required_action: What user must do

    Returns:
        Updated state with interrupt metadata
    """
    state["current_phase"] = "interrupted"

    # Add to status reports
    state["status_reports"].append(
        f"⏸️  EXECUTION PAUSED: {interrupt_reason}\n"
        f"Required action: {required_action}\n"
        f"Time: {datetime.now().isoformat()}"
    )

    logger.warning(f"EXECUTION INTERRUPTED: {interrupt_reason}")

    return state


def resume_from_interrupt(state: SharedState) -> SharedState:
    """
    Resume execution after interrupt

    Args:
        state: State with interrupt resolved

    Returns:
        Updated state ready to continue
    """
    state["current_phase"] = "execution"

    state["status_reports"].append(f"▶️  EXECUTION RESUMED\n" f"Time: {datetime.now().isoformat()}")

    logger.info("EXECUTION RESUMED after interrupt")

    return state
