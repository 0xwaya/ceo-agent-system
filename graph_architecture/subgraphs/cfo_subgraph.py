"""
CFO Subgraph Implementation

Finance domain subgraph with:
1. Budget analysis
2. Cost modeling and projections
3. Financial compliance checks
4. Risk assessment
5. Executive summary generation

Internal processing stays within subgraph.
Only summaries sent to CEO.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from langgraph.graph import StateGraph, START, END

from graph_architecture.schemas import (
    SharedState,
    CFOSubgraphState,
    AgentRole,
    Message,
    MessageType,
    SummaryMessage,
    TaskStatus,
)
from graph_architecture.guards import create_cfo_entry_guard

logger = logging.getLogger(__name__)


# ============================================================================
# CFO SUBGRAPH NODES
# ============================================================================


def cfo_entry_guard_node(state: SharedState) -> SharedState:
    """
    Entry guard for CFO subgraph
    Validates only CEO can invoke CFO
    """
    guard = create_cfo_entry_guard()
    state = guard.validate_entry(state, requester_role=AgentRole.CEO)

    logger.info("✅ CFO entry guard passed")
    return state


def analyze_budget_node(state: SharedState) -> Dict[str, Any]:
    """
    Analyze budget allocation and constraints

    Internal processing - raw data not exposed to CEO
    """
    logger.info("\n" + "=" * 80)
    logger.info("💰 CFO: BUDGET ANALYSIS")
    logger.info("=" * 80)

    total_budget = state.get("total_budget", 0)
    budget_allocated = state.get("budget_allocated", {})
    budget_spent = state.get("budget_spent", {})

    # Calculate budget remaining
    total_allocated = sum(budget_allocated.values())
    total_spent = sum(budget_spent.values())
    remaining = total_budget - total_allocated

    logger.info(f"Total Budget: ${total_budget:,.2f}")
    logger.info(f"Allocated: ${total_allocated:,.2f}")
    logger.info(f"Spent: ${total_spent:,.2f}")
    logger.info(f"Remaining: ${remaining:,.2f}")

    # Create budget projection (internal, not sent to CEO)
    projection = {
        "current_burn_rate": total_spent / max(state.get("current_day", 1), 1),
        "projected_total_spend": total_spent
        * (state.get("target_completion_days", 90) / max(state.get("current_day", 1), 1)),
        "budget_utilization": (total_allocated / total_budget * 100) if total_budget > 0 else 0,
        "risk_of_overrun": "LOW" if remaining > total_budget * 0.2 else "HIGH",
    }

    # Store projection internally (raw data)
    return {
        "budget_projections": [projection],
        "budget_remaining": remaining,
        "cost_analysis": {
            "total_allocated": total_allocated,
            "total_spent": total_spent,
            "efficiency": (total_spent / total_allocated * 100) if total_allocated > 0 else 0,
        },
    }


def validate_costs_node(state: SharedState) -> Dict[str, Any]:
    """
    Validate proposed costs against budget constraints
    """
    logger.info("\n📊 CFO: COST VALIDATION")

    identified_tasks = state.get("identified_tasks", [])
    remaining_budget = state.get("budget_remaining", 0)

    validated_tasks = []
    total_estimated = 0

    for task in identified_tasks:
        estimated_cost = task.get("estimated_budget", 0)
        total_estimated += estimated_cost

        if estimated_cost <= remaining_budget:
            validated_tasks.append(
                {**task, "cost_validated": True, "validation_status": "approved"}
            )
        else:
            validated_tasks.append(
                {
                    **task,
                    "cost_validated": False,
                    "validation_status": "requires_budget_increase",
                    "shortfall": estimated_cost - remaining_budget,
                }
            )

    logger.info(f"Validated {len(validated_tasks)} tasks")
    logger.info(f"Total estimated cost: ${total_estimated:,.2f}")

    return {
        "identified_tasks": validated_tasks,
        "cost_analysis": {
            **state.get("cost_analysis", {}),
            "total_estimated_cost": total_estimated,
            "budget_sufficient": total_estimated <= remaining_budget,
        },
    }


def compliance_check_node(state: SharedState) -> Dict[str, Any]:
    """
    Run financial compliance checks
    """
    logger.info("\n⚖️  CFO: COMPLIANCE CHECK")

    compliance_checks = []

    # Check 1: Budget allocation doesn't exceed total
    total_allocated = sum(state.get("budget_allocated", {}).values())
    total_budget = state.get("total_budget", 0)

    compliance_checks.append(
        {
            "check": "budget_allocation_limit",
            "passed": total_allocated <= total_budget,
            "details": f"Allocated ${total_allocated:,.2f} of ${total_budget:,.2f}",
        }
    )

    # Check 2: All expenditures have approvals
    approved_actions = state.get("approved_actions", [])
    pending_approvals = state.get("pending_approvals", [])

    compliance_checks.append(
        {
            "check": "approval_compliance",
            "passed": len(pending_approvals) == 0,
            "details": f"{len(approved_actions)} approved, {len(pending_approvals)} pending",
        }
    )

    # Check 3: No guard rail violations
    violations = state.get("guard_rail_violations", [])

    compliance_checks.append(
        {
            "check": "guard_rail_compliance",
            "passed": len(violations) == 0,
            "details": f"{len(violations)} violations detected",
        }
    )

    all_passed = all(check["passed"] for check in compliance_checks)

    logger.info(f"Compliance: {'✅ PASSED' if all_passed else '❌ FAILED'}")

    return {
        "compliance_checks": compliance_checks,
        "audit_trail": [
            {
                "timestamp": datetime.now().isoformat(),
                "checks_run": len(compliance_checks),
                "all_passed": all_passed,
            }
        ],
    }


def generate_cfo_summary_node(state: SharedState) -> Dict[str, Any]:
    """
    Generate executive summary for CEO

    This is the ONLY data sent from CFO to CEO
    Raw financial data stays in CFO subgraph
    """
    logger.info("\n📋 CFO: GENERATING EXECUTIVE SUMMARY")

    # Extract key insights (not raw data)
    budget_remaining = state.get("budget_remaining", 0)
    total_budget = state.get("total_budget", 0)
    utilization = (
        ((total_budget - budget_remaining) / total_budget * 100) if total_budget > 0 else 0
    )

    costs = state.get("cost_analysis", {})
    compliance = state.get("compliance_checks", [])
    projections = state.get("budget_projections", [])

    # Build executive summary (narrative, not tables)
    summary_parts = [
        "=" * 80,
        "CFO EXECUTIVE SUMMARY",
        "=" * 80,
        "",
        f"💰 BUDGET STATUS:",
        f"   Budget Utilization: {utilization:.1f}%",
        f"   Remaining Funds: ${budget_remaining:,.2f}",
        "",
    ]

    # Key findings
    key_findings = []

    if utilization > 80:
        key_findings.append("⚠️  Budget utilization exceeds 80% - monitor spend closely")

    if not all(c.get("passed", False) for c in compliance):
        key_findings.append("❌ Compliance issues detected - review required")

    if budget_remaining < total_budget * 0.1:
        key_findings.append("🚨 Low budget remaining - consider reallocation")

    if projections and projections[0].get("risk_of_overrun") == "HIGH":
        key_findings.append("📈 High risk of budget overrun based on current burn rate")

    if not key_findings:
        key_findings.append("✅ Financial status healthy")

    summary_parts.extend(
        [
            "🔍 KEY FINDINGS:",
            *[f"   {finding}" for finding in key_findings],
            "",
            "💡 RECOMMENDATIONS:",
        ]
    )

    # Recommendations
    recommendations = []

    if utilization > 90:
        recommendations.append("Prioritize critical tasks only")
        recommendations.append("Defer non-essential expenditures")
    elif utilization < 50:
        recommendations.append("Budget underutilized - accelerate strategic initiatives")

    if not recommendations:
        recommendations.append("Continue current budget allocation strategy")

    summary_parts.extend([*[f"   • {rec}" for rec in recommendations], "", "=" * 80])

    executive_summary = "\n".join(summary_parts)

    # Create summary message for CEO
    summary_message = SummaryMessage(
        agent_role=AgentRole.CFO,
        task_id="cfo_financial_analysis",
        status=TaskStatus.COMPLETED,
        key_findings=key_findings,
        risks=[],  # Extract from compliance checks if needed
        recommendations=recommendations,
        budget_used=total_budget - budget_remaining,
        next_steps=["Monitor budget utilization", "Review pending approvals"],
        raw_data_available=True,  # Indicates detailed data exists but not sent
    )

    logger.info(executive_summary)

    return {
        "executive_summary": executive_summary,
        "financial_recommendations": recommendations,
        "agent_outputs": [
            {
                "agent": "cfo",
                "summary": summary_message.model_dump(),
                "timestamp": datetime.now().isoformat(),
            }
        ],
    }


# ============================================================================
# CFO SUBGRAPH ROUTING
# ============================================================================


def route_cfo_workflow(state: SharedState) -> str:
    """
    Route CFO workflow based on current state
    """
    # Check if compliance passed
    compliance_checks = state.get("compliance_checks", [])

    if compliance_checks:
        all_passed = all(check.get("passed", False) for check in compliance_checks)

        if not all_passed:
            logger.warning("Compliance failed - routing to END with warning")
            return END

    return "summary"


# ============================================================================
# BUILD CFO SUBGRAPH
# ============================================================================


def build_cfo_subgraph() -> StateGraph:
    """
    Build CFO finance subgraph

    Returns:
        Compiled CFO subgraph
    """
    # Use SharedState for compatibility with CEO graph
    subgraph = StateGraph(SharedState)

    # Add nodes
    subgraph.add_node("entry_guard", cfo_entry_guard_node)
    subgraph.add_node("analyze_budget", analyze_budget_node)
    subgraph.add_node("validate_costs", validate_costs_node)
    subgraph.add_node("compliance_check", compliance_check_node)
    subgraph.add_node("generate_summary", generate_cfo_summary_node)

    # Define workflow
    subgraph.add_edge(START, "entry_guard")
    subgraph.add_edge("entry_guard", "analyze_budget")
    subgraph.add_edge("analyze_budget", "validate_costs")
    subgraph.add_edge("validate_costs", "compliance_check")
    subgraph.add_edge("compliance_check", "generate_summary")
    subgraph.add_edge("generate_summary", END)

    return subgraph.compile()


# Test the subgraph
if __name__ == "__main__":
    from graph_architecture.schemas import create_initial_shared_state

    # Create test state
    initial_state = create_initial_shared_state(
        company_name="Test Corp",
        industry="Technology",
        location="San Francisco, CA",
        total_budget=50000.0,
        target_days=90,
        objectives=["Launch product", "Build brand"],
    )

    # Build and test subgraph
    cfo_graph = build_cfo_subgraph()
    result = cfo_graph.invoke(initial_state)

    print("\n✅ CFO SUBGRAPH TEST COMPLETE")
    print(f"Executive Summary Generated: {bool(result.get('executive_summary'))}")
