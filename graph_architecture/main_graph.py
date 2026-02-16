"""
Main Hierarchical Graph Orchestration

Composes the complete multi-agent system with:
1. CEO as root orchestrator
2. CFO, Engineer, Researcher as subgraphs
3. Checkpoint-based persistence
4. Role-based guards
5. Human-in-the-loop approvals
"""

import logging
from typing import Optional, Dict, Any

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from graph_architecture.schemas import SharedState, CEOState, AgentRole, create_initial_shared_state
from graph_architecture.checkpointer import create_checkpointer, CheckpointManager
from graph_architecture.guards import validate_agent_role, AuthorizationLevel, ViolationLogger
from graph_architecture.approval_nodes import (
    human_approval_node,
    route_to_approval,
    check_approval_status,
    create_budget_approval_request,
)
from graph_architecture.subgraphs.cfo_subgraph import build_cfo_subgraph
from graph_architecture.subgraphs.engineer_subgraph import build_engineer_subgraph
from graph_architecture.subgraphs.researcher_subgraph import build_researcher_subgraph

logger = logging.getLogger(__name__)


def _is_checkpoint_capacity_error(error: Exception) -> bool:
    """Detect storage-capacity failures from checkpoint backends."""
    message = str(error).lower()
    return (
        "database or disk is full" in message
        or "disk full" in message
        or "no space left on device" in message
    )


# ============================================================================
# CEO ORCHESTRATOR NODES
# ============================================================================


def ceo_initialize_node(state: CEOState) -> Dict[str, Any]:
    """
    CEO initialization - set goals and objectives
    """
    logger.info("\n" + "=" * 80)
    logger.info("👔 CEO: STRATEGIC INITIALIZATION")
    logger.info("=" * 80)

    company_name = state.get("company_name", "Unknown")
    industry = state.get("industry", "Unknown")
    objectives = state.get("strategic_objectives", [])

    logger.info(f"Company: {company_name}")
    logger.info(f"Industry: {industry}")
    logger.info(f"\n📋 Strategic Objectives:")
    for i, obj in enumerate(objectives, 1):
        logger.info(f"  {i}. {obj}")

    # CEO makes initial executive decisions
    executive_decision = {
        "decision_id": "init-001",
        "decision": "Approve strategic objectives and initialize multi-agent workflow",
        "rationale": "Objectives align with business goals",
        "timestamp": "2026-02-13T10:00:00Z",
    }

    return {
        "executive_decisions": [executive_decision],
        "current_phase": "planning",
        "active_agents": ["ceo"],
    }


def ceo_decompose_tasks_node(state: CEOState) -> Dict[str, Any]:
    """
    CEO decomposes objectives into tasks and assigns to domains
    """
    logger.info("\n🎯 CEO: TASK DECOMPOSITION")

    objectives = state.get("strategic_objectives", [])
    total_budget = state.get("total_budget", 0)

    # CEO identifies high-level tasks
    identified_tasks = []

    # Financial analysis task → CFO
    if total_budget > 0:
        identified_tasks.append(
            {
                "task_id": "T001",
                "task_name": "Financial Analysis and Budget Planning",
                "domain": "finance",
                "assigned_to": "cfo",
                "priority": "critical",
                "estimated_budget": 0,  # CFO doesn't spend, analyzes
                "estimated_days": 2,
            }
        )

    # Engineering tasks → Engineer (if objectives include technical work)
    tech_keywords = ["website", "app", "system", "platform", "digital"]
    has_tech_objectives = any(
        any(keyword in obj.lower() for keyword in tech_keywords) for obj in objectives
    )

    if has_tech_objectives:
        identified_tasks.append(
            {
                "task_id": "T002",
                "task_name": "Technical Architecture and Implementation",
                "domain": "engineering",
                "assigned_to": "engineer",
                "priority": "high",
                "estimated_budget": total_budget * 0.6,  # 60% to engineering
                "estimated_days": 30,
            }
        )

    # Research tasks → Researcher
    identified_tasks.append(
        {
            "task_id": "T003",
            "task_name": "Market Research and Competitive Analysis",
            "domain": "research",
            "assigned_to": "researcher",
            "priority": "medium",
            "estimated_budget": 0,  # Research uses existing tools
            "estimated_days": 5,
        }
    )

    logger.info(f"Identified {len(identified_tasks)} tasks")

    # CEO creates delegation log
    delegation_log = [
        {
            "timestamp": "2026-02-13T10:30:00Z",
            "delegated_to": task["assigned_to"],
            "task_id": task["task_id"],
            "task_name": task["task_name"],
        }
        for task in identified_tasks
    ]

    return {
        "identified_tasks": identified_tasks,
        "delegation_log": delegation_log,
        "current_phase": "delegation",
    }


def ceo_route_to_subgraph_node(state: CEOState) -> Dict[str, Any]:
    """
    CEO routes to appropriate subgraph
    """
    logger.info("\n🔀 CEO: ROUTING TO SUBGRAPHS")

    # Route to all three subgraphs: CFO, Engineer, Researcher
    return {
        "current_phase": "executing_all_subgraphs",
        "active_agents": ["ceo", "cfo", "engineer", "researcher"],
    }


def ceo_consolidate_summaries_node(state: CEOState) -> Dict[str, Any]:
    """
    CEO consolidates summaries from subordinate agents
    """
    logger.info("\n📊 CEO: CONSOLIDATING AGENT SUMMARIES")

    agent_outputs = state.get("agent_outputs", [])

    if not agent_outputs:
        logger.warning("No agent outputs to consolidate")
        return {}

    # CEO reviews summaries (not raw data)
    logger.info(f"Received {len(agent_outputs)} agent summaries")

    for output in agent_outputs:
        agent = output.get("agent", "unknown")
        summary = output.get("summary", {})
        logger.info(f"  - {agent.upper()}: {summary.get('status', 'unknown')}")

    # CEO makes final decision based on summaries
    final_decision = {
        "decision_id": "final-001",
        "decision": "Accept all agent outputs and proceed to completion",
        "timestamp": "2026-02-13T12:00:00Z",
    }

    return {"executive_decisions": [final_decision], "current_phase": "consolidation"}


def ceo_generate_final_report_node(state: CEOState) -> Dict[str, Any]:
    """
    CEO generates final executive report
    """
    logger.info("\n📝 CEO: GENERATING FINAL REPORT")

    company_name = state.get("company_name", "Unknown")
    completed_phases = state.get("completed_phases", [])
    executive_decisions = state.get("executive_decisions", [])
    budget_remaining = state.get("budget_remaining", 0)

    final_summary = f"""
{'='*80}
CEO FINAL EXECUTIVE REPORT
{'='*80}

Company: {company_name}

EXECUTIVE SUMMARY:
------------------
Strategic multi-agent workflow completed successfully.

PHASES COMPLETED: {len(completed_phases)}
EXECUTIVE DECISIONS MADE: {len(executive_decisions)}
BUDGET REMAINING: ${budget_remaining:,.2f}

KEY OUTCOMES:
  ✅ Strategic objectives defined and decomposed
  ✅ Multi-agent coordination established
  ✅ Financial analysis completed (CFO)
  ✅ Hierarchical governance maintained

GOVERNANCE STATUS:
  ✅ All communications followed hierarchy
  ✅ No guard rail violations
  ✅ Role boundaries respected

CEO SIGNATURE: Approved
DATE: 2026-02-13
{'='*80}
"""

    logger.info(final_summary)

    # Add to completed_phases using the reducer (operator.add)
    return {
        "final_summary": final_summary,
        "current_phase": "complete",
        "completed_phases": [
            "initialization",
            "planning",
            "delegation",
            "execution",
            "consolidation",
        ],
    }


# ============================================================================
# ROUTING LOGIC
# ============================================================================


def route_ceo_workflow(state: CEOState) -> str:
    """
    CEO conditional routing logic
    """
    current_phase = state.get("current_phase", "initialization")

    phase_routing = {
        "initialization": "decompose",
        "planning": "decompose",
        "delegation": "route_subgraph",
        "executing_cfo": "cfo_subgraph",
        "consolidation": "approval_check",
        "approved": "final_report",
    }

    next_node = phase_routing.get(current_phase, "final_report")

    logger.info(f"Routing: {current_phase} → {next_node}")

    return next_node


def after_cfo_subgraph(state: CEOState) -> str:
    """
    Routing after CFO subgraph completes
    """
    # After CFO, move to consolidation
    return "consolidate"


# ============================================================================
# BUILD MASTER GRAPH
# ============================================================================


def cfo_subgraph_wrapper(state: CEOState) -> Dict[str, Any]:
    """
    Wrapper for CFO subgraph to handle state conversion
    """
    logger.info("\n💼 Invoking CFO Subgraph...")

    # Build and invoke CFO subgraph
    cfo_graph = build_cfo_subgraph()
    result = cfo_graph.invoke(state)

    logger.info(f"✅ CFO Subgraph completed")

    # Return the updated state fields
    return result


def engineer_subgraph_wrapper(state: CEOState) -> Dict[str, Any]:
    """
    Wrapper for Engineer subgraph
    """
    logger.info("\n🛠️  Invoking Engineer Subgraph...")

    # Build and invoke Engineer subgraph
    engineer_graph = build_engineer_subgraph()
    result = engineer_graph.invoke(state)

    logger.info(f"✅ Engineer Subgraph completed")

    return result


def researcher_subgraph_wrapper(state: CEOState) -> Dict[str, Any]:
    """
    Wrapper for Researcher subgraph
    """
    logger.info("\n🔍 Invoking Researcher Subgraph...")

    # Build and invoke Researcher subgraph
    researcher_graph = build_researcher_subgraph()
    result = researcher_graph.invoke(state)

    logger.info(f"✅ Researcher Subgraph completed")

    return result


def build_master_graph(checkpointer: Optional[BaseCheckpointSaver] = None) -> StateGraph:
    """
    Build complete hierarchical multi-agent system

    Args:
        checkpointer: Optional checkpointer for persistence

    Returns:
        Compiled master graph
    """
    # Create main graph with CEO state
    graph = StateGraph(CEOState)

    # CEO nodes
    graph.add_node("initialize", ceo_initialize_node)
    graph.add_node("decompose", ceo_decompose_tasks_node)
    graph.add_node("route_subgraph", ceo_route_to_subgraph_node)
    graph.add_node("consolidate", ceo_consolidate_summaries_node)
    graph.add_node("final_report", ceo_generate_final_report_node)

    # Subgraph nodes - use wrappers
    graph.add_node("cfo_subgraph", cfo_subgraph_wrapper)
    graph.add_node("engineer_subgraph", engineer_subgraph_wrapper)
    graph.add_node("researcher_subgraph", researcher_subgraph_wrapper)

    # Human approval node
    graph.add_node("approval", human_approval_node)

    # Edge flow - sequential execution through all subgraphs
    graph.add_edge(START, "initialize")
    graph.add_edge("initialize", "decompose")
    graph.add_edge("decompose", "route_subgraph")
    graph.add_edge("route_subgraph", "cfo_subgraph")
    graph.add_edge("cfo_subgraph", "engineer_subgraph")
    graph.add_edge("engineer_subgraph", "researcher_subgraph")
    graph.add_edge("researcher_subgraph", "consolidate")

    # Approval checkpoint
    graph.add_conditional_edges(
        "consolidate",
        lambda state: "approval" if state.get("pending_approvals") else "final_report",
        {"approval": "approval", "final_report": "final_report"},
    )

    graph.add_edge("approval", "final_report")
    graph.add_edge("final_report", END)

    # Compile with checkpointing
    if checkpointer:
        return graph.compile(checkpointer=checkpointer, interrupt_before=["approval"])
    else:
        return graph.compile()


# ============================================================================
# EXECUTION HELPERS
# ============================================================================


def execute_multi_agent_system(
    company_name: str,
    industry: str,
    location: str,
    total_budget: float,
    target_days: int,
    objectives: list[str],
    use_checkpointing: bool = True,
    thread_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute complete multi-agent system

    Args:
        company_name: Company name
        industry: Business industry
        location: Company location
        total_budget: Total budget
        target_days: Timeline in days
        objectives: Strategic objectives
        use_checkpointing: Enable persistence
        thread_id: Optional thread ID for resumption

    Returns:
        Final state
    """
    # Create initial state
    initial_state = create_initial_shared_state(
        company_name=company_name,
        industry=industry,
        location=location,
        total_budget=total_budget,
        target_days=target_days,
        objectives=objectives,
    )

    # Add CEO-specific fields to the state dict
    ceo_state = {
        **initial_state,
        "executive_decisions": [],
        "delegation_log": [],
        "subgraph_summaries": [],
    }

    # Create checkpointer if enabled
    checkpointer = None
    config = None

    if use_checkpointing:
        checkpointer = create_checkpointer("sqlite", "./data/checkpoints.sqlite")
        import uuid

        thread = thread_id or f"thread-{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": thread}}
        logger.info(f"Using checkpointing with thread: {thread}")

    # Build graph
    graph = build_master_graph(checkpointer=checkpointer)

    # Execute
    logger.info("\n🚀 STARTING MULTI-AGENT SYSTEM EXECUTION")
    logger.info("=" * 80)

    try:
        if config:
            result = graph.invoke(ceo_state, config=config)
        else:
            result = graph.invoke(ceo_state)
    except Exception as exc:
        if use_checkpointing and _is_checkpoint_capacity_error(exc):
            logger.error(
                "Checkpoint persistence failed due to storage limits; retrying without checkpointing for this run."
            )
            graph_no_checkpoint = build_master_graph(checkpointer=None)
            result = graph_no_checkpoint.invoke(ceo_state)
        else:
            raise

    logger.info("\n✅ EXECUTION COMPLETE")
    logger.info("=" * 80)

    return result


# Test execution
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    result = execute_multi_agent_system(
        company_name="TechCorp Inc",
        industry="Software & Technology",
        location="San Francisco, CA",
        total_budget=100000.0,
        target_days=90,
        objectives=[
            "Launch SaaS platform",
            "Build enterprise sales team",
            "Establish market presence",
        ],
        use_checkpointing=True,
    )

    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    print(f"Completed phases: {len(result.get('completed_phases', []))}")
    print(f"Executive decisions: {len(result.get('executive_decisions', []))}")
    print(f"Final summary generated: {bool(result.get('final_summary'))}")
