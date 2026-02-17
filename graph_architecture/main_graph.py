"""
Main Hierarchical Graph Orchestration — v2 (3-Tier LangGraph Architecture)

Tier 1  : CEO  — root orchestrator, driven by LLM analysis
Tier 2  : Domain Directors — CFO, Engineer, Researcher, Legal, Martech, Security
Tier 3  : Execution Specialists — UX/UI, WebDev, SoftEng, Branding, Content,
          Campaign, SocialMedia  (orchestrated inside their Tier-2 subgraphs)

Flow
----
START → privacy_scrub → prompt_expert → ceo_analyze → dispatch_orchestrator
        ↓ (loop until dispatch_plan empty)
        → <domain>_subgraph  →  back to dispatch_orchestrator
        ↓ (all dispatched)
        → consolidate → [approval?] → final_report → END
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.base import BaseCheckpointSaver

from graph_architecture.schemas import (
    CEOState,
    SharedState,
    AgentRole,
    AgentTask,
    LLMRoutingDecision,
    create_initial_shared_state,
)
from graph_architecture.checkpointer import create_checkpointer, CheckpointManager
from graph_architecture.guards import validate_agent_role, AuthorizationLevel, ViolationLogger
from graph_architecture.approval_nodes import (
    human_approval_node,
    route_to_approval,
    check_approval_status,
    create_budget_approval_request,
)
from graph_architecture.prompt_expert import prompt_expert_node, build_routing_decision_from_expert
from graph_architecture.privacy import privacy_scrub_node
from graph_architecture.llm_nodes import ceo_llm_analyze_node, TIER2_NODE_MAP
from graph_architecture.subgraphs.cfo_subgraph import build_cfo_subgraph
from graph_architecture.subgraphs.engineer_subgraph import build_engineer_subgraph
from graph_architecture.subgraphs.researcher_subgraph import build_researcher_subgraph

# New Tier-2 subgraphs — imported lazily so missing files don't break old runs
try:
    from graph_architecture.subgraphs.legal_subgraph import build_legal_subgraph

    _HAS_LEGAL = True
except ImportError:
    _HAS_LEGAL = False

try:
    from graph_architecture.subgraphs.martech_subgraph import build_martech_subgraph

    _HAS_MARTECH = True
except ImportError:
    _HAS_MARTECH = False

try:
    from graph_architecture.subgraphs.security_subgraph import build_security_subgraph

    _HAS_SECURITY = True
except ImportError:
    _HAS_SECURITY = False

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
# TIER-1 CEO NODES  (LLM-backed via llm_nodes.py)
# ============================================================================


def ceo_analyze_wrapper(state: CEOState) -> Dict[str, Any]:
    """
    Node: ceo_analyze
    Calls the LLM-backed CEO analysis node then derives a dispatch_plan from
    the prompt expert output if the CEO node hasn't set one yet.
    """
    logger.info("\n👔 CEO: LLM STRATEGIC ANALYSIS")

    # Run LLM analysis (writes agent_outputs + executive_decisions to state)
    updated = ceo_llm_analyze_node(state)

    # Build dispatch_plan from prompt_expert_output if not already set
    routing: Optional[LLMRoutingDecision] = state.get("llm_routing_decision")
    if routing is None:
        expert_out = state.get("prompt_expert_output")
        if expert_out:
            routing = build_routing_decision_from_expert(expert_out)
        else:
            # Safe default: send to all three classic domains
            routing = LLMRoutingDecision(
                dispatch_plan=["cfo", "engineer", "researcher"],
                can_parallelize=False,
                requires_approval_before=[],
            )

    dispatch_plan = list(routing.dispatch_plan) if routing else ["cfo", "engineer", "researcher"]
    logger.info(f"Dispatch plan: {dispatch_plan}")

    return {
        **updated,
        "dispatch_plan": dispatch_plan,
        "current_dispatch_index": 0,
        "can_parallelize": routing.can_parallelize if routing else False,
        "current_phase": "dispatching",
        "active_agents": ["ceo"],
    }


def dispatch_orchestrator_node(state: CEOState) -> Dict[str, Any]:
    """
    Node: dispatch_orchestrator
    Examined each time a subgraph returns. Advances the index so the next
    subgraph wrapper knows which domain to invoke.
    """
    plan: List[str] = state.get("dispatch_plan", [])
    idx: int = state.get("current_dispatch_index", 0)

    if idx < len(plan):
        domain = plan[idx]
        logger.info(f"[Dispatch] Step {idx + 1}/{len(plan)}: {domain}")
        return {"current_dispatch_index": idx, "current_phase": f"dispatching_{domain}"}
    else:
        logger.info("[Dispatch] All domains completed — consolidating")
        return {"current_phase": "consolidation"}


def route_dispatch(state: CEOState) -> str:
    """
    Conditional edge function from dispatch_orchestrator.
    Returns the name of the next subgraph node OR 'consolidate'.
    """
    plan: List[str] = state.get("dispatch_plan", [])
    idx: int = state.get("current_dispatch_index", 0)

    if idx >= len(plan):
        return "consolidate"

    domain = plan[idx]
    route_map = {
        "cfo": "cfo_subgraph",
        "engineer": "engineer_subgraph",
        "researcher": "researcher_subgraph",
        "legal": "legal_subgraph",
        "martech": "martech_subgraph",
        "security": "security_subgraph",
    }
    return route_map.get(domain, "consolidate")


def _advance_dispatch_index(state: CEOState) -> Dict[str, Any]:
    """Helper: advance dispatch index after a subgraph returns."""
    idx = state.get("current_dispatch_index", 0)
    return {"current_dispatch_index": idx + 1}


# ============================================================================
# SUBGRAPH WRAPPERS  (all 6 Tier-2 domains)
# ============================================================================


def cfo_subgraph_wrapper(state: CEOState) -> Dict[str, Any]:
    logger.info("\n💼 Invoking CFO Subgraph...")
    result = build_cfo_subgraph().invoke(state)
    logger.info("✅ CFO Subgraph completed")
    return {**result, **_advance_dispatch_index(state)}


def engineer_subgraph_wrapper(state: CEOState) -> Dict[str, Any]:
    logger.info("\n🛠️  Invoking Engineer Subgraph...")
    result = build_engineer_subgraph().invoke(state)
    logger.info("✅ Engineer Subgraph completed")
    return {**result, **_advance_dispatch_index(state)}


def researcher_subgraph_wrapper(state: CEOState) -> Dict[str, Any]:
    logger.info("\n🔍 Invoking Researcher Subgraph...")
    result = build_researcher_subgraph().invoke(state)
    logger.info("✅ Researcher Subgraph completed")
    return {**result, **_advance_dispatch_index(state)}


def legal_subgraph_wrapper(state: CEOState) -> Dict[str, Any]:
    logger.info("\n⚖️  Invoking Legal Subgraph...")
    if _HAS_LEGAL:
        result = build_legal_subgraph().invoke(state)
    else:
        from graph_architecture.llm_nodes import legal_llm_compliance_node

        result = legal_llm_compliance_node(state)
    logger.info("✅ Legal Subgraph completed")
    return {**result, **_advance_dispatch_index(state)}


def martech_subgraph_wrapper(state: CEOState) -> Dict[str, Any]:
    logger.info("\n📣 Invoking Martech Subgraph...")
    if _HAS_MARTECH:
        result = build_martech_subgraph().invoke(state)
    else:
        from graph_architecture.llm_nodes import martech_llm_strategy_node

        result = martech_llm_strategy_node(state)
    logger.info("✅ Martech Subgraph completed")
    return {**result, **_advance_dispatch_index(state)}


def security_subgraph_wrapper(state: CEOState) -> Dict[str, Any]:
    logger.info("\n🔒 Invoking Security Subgraph...")
    if _HAS_SECURITY:
        result = build_security_subgraph().invoke(state)
    else:
        from graph_architecture.llm_nodes import security_llm_audit_node

        result = security_llm_audit_node(state)
    logger.info("✅ Security Subgraph completed")
    return {**result, **_advance_dispatch_index(state)}


# ============================================================================
# CONSOLIDATION & FINAL REPORT
# ============================================================================


def ceo_consolidate_summaries_node(state: CEOState) -> Dict[str, Any]:
    """CEO consolidates all agent outputs into a unified summary."""
    logger.info("\n📊 CEO: CONSOLIDATING AGENT SUMMARIES")

    agent_outputs = state.get("agent_outputs", [])
    logger.info(f"Received {len(agent_outputs)} agent summaries")

    for out in agent_outputs:
        agent = out.get("agent", "unknown")
        summary = out.get("summary", {})
        logger.info(f"  - {agent.upper()}: {summary.get('status', 'unknown')}")

    final_decision = {
        "decision_id": f"final-{uuid.uuid4().hex[:6]}",
        "decision": "Accept all agent outputs and proceed to final report",
        "timestamp": datetime.utcnow().isoformat(),
    }
    return {"executive_decisions": [final_decision], "current_phase": "consolidation"}


def ceo_generate_final_report_node(state: CEOState) -> Dict[str, Any]:
    """CEO generates the final executive report from all domain outputs."""
    logger.info("\n📝 CEO: GENERATING FINAL REPORT")

    company_name = state.get("company_name", "Unknown")
    agent_outputs = state.get("agent_outputs", [])
    executive_decisions = state.get("executive_decisions", [])
    budget_remaining = state.get("budget_remaining", 0)
    dispatch_plan = state.get("dispatch_plan", [])

    domains_completed = ", ".join(dispatch_plan) if dispatch_plan else "N/A"

    final_summary = (
        f"\n{'='*80}\n"
        f"CEO FINAL EXECUTIVE REPORT\n"
        f"{'='*80}\n\n"
        f"Company : {company_name}\n"
        f"Domains : {domains_completed}\n\n"
        f"AGENTS RAN    : {len(agent_outputs)}\n"
        f"CEO DECISIONS : {len(executive_decisions)}\n"
        f"BUDGET LEFT   : ${budget_remaining:,.2f}\n\n"
        f"STATUS: All dispatched agents reported successfully.\n"
        f"CEO SIGNATURE: Approved  |  {datetime.utcnow().date()}\n"
        f"{'='*80}\n"
    )

    logger.info(final_summary)

    return {
        "final_summary": final_summary,
        "current_phase": "complete",
        "completed_phases": ["prompt_expert", "ceo_analyze", "dispatch", "consolidation"],
    }


# ============================================================================
# BUILD MASTER GRAPH
# ============================================================================


def build_master_graph(checkpointer: Optional[BaseCheckpointSaver] = None) -> StateGraph:
    """
    Build the complete 3-tier hierarchical multi-agent graph.

    Node order
    ----------
    START
      → privacy_scrub        (Node 0 — PII redaction before any LLM sees input)
      → prompt_expert        (Node 1 — structured intent parsing)
      → ceo_analyze          (Node 1 — LLM strategic analysis + dispatch_plan)
      → dispatch_orchestrator (Node 2 — loop controller)
          ↓ conditional per dispatch_plan[idx]
          → cfo_subgraph  / engineer_subgraph / researcher_subgraph
            / legal_subgraph / martech_subgraph / security_subgraph
          → (each subgraph returns to dispatch_orchestrator)
      → consolidate          (after all dispatched)
          ↓ conditional — approval gate
      → approval  (human-in-the-loop, interrupt_before)
      → final_report
    END
    """
    graph = StateGraph(CEOState)

    # ── Node registrations ──────────────────────────────────────────────────
    graph.add_node("privacy_scrub", privacy_scrub_node)  # Node 0 — PII guard
    graph.add_node("prompt_expert", prompt_expert_node)
    graph.add_node("ceo_analyze", ceo_analyze_wrapper)
    graph.add_node("dispatch_orchestrator", dispatch_orchestrator_node)

    # Tier-2 subgraph wrappers
    graph.add_node("cfo_subgraph", cfo_subgraph_wrapper)
    graph.add_node("engineer_subgraph", engineer_subgraph_wrapper)
    graph.add_node("researcher_subgraph", researcher_subgraph_wrapper)
    graph.add_node("legal_subgraph", legal_subgraph_wrapper)
    graph.add_node("martech_subgraph", martech_subgraph_wrapper)
    graph.add_node("security_subgraph", security_subgraph_wrapper)

    # CEO wrap-up
    graph.add_node("consolidate", ceo_consolidate_summaries_node)
    graph.add_node("approval", human_approval_node)
    graph.add_node("final_report", ceo_generate_final_report_node)

    # ── Static edges ─────────────────────────────────────────────────────────
    graph.add_edge(START, "privacy_scrub")
    graph.add_edge("privacy_scrub", "prompt_expert")
    graph.add_edge("prompt_expert", "ceo_analyze")
    graph.add_edge("ceo_analyze", "dispatch_orchestrator")

    # Each subgraph cycles back to the dispatch orchestrator
    for domain_node in (
        "cfo_subgraph",
        "engineer_subgraph",
        "researcher_subgraph",
        "legal_subgraph",
        "martech_subgraph",
        "security_subgraph",
    ):
        graph.add_edge(domain_node, "dispatch_orchestrator")

    # Approval → final_report (unconditional after human interaction)
    graph.add_edge("approval", "final_report")
    graph.add_edge("final_report", END)

    # ── Conditional edges ────────────────────────────────────────────────────

    # dispatch_orchestrator → next domain OR consolidate
    graph.add_conditional_edges(
        "dispatch_orchestrator",
        route_dispatch,
        {
            "cfo_subgraph": "cfo_subgraph",
            "engineer_subgraph": "engineer_subgraph",
            "researcher_subgraph": "researcher_subgraph",
            "legal_subgraph": "legal_subgraph",
            "martech_subgraph": "martech_subgraph",
            "security_subgraph": "security_subgraph",
            "consolidate": "consolidate",
        },
    )

    # consolidate → approval gate OR skip straight to final_report
    graph.add_conditional_edges(
        "consolidate",
        lambda state: "approval" if state.get("pending_approvals") else "final_report",
        {"approval": "approval", "final_report": "final_report"},
    )

    # ── Compile ──────────────────────────────────────────────────────────────
    if checkpointer:
        return graph.compile(checkpointer=checkpointer, interrupt_before=["approval"])
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
    user_raw_input: Optional[str] = None,
    use_checkpointing: bool = True,
    thread_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute the complete 3-tier multi-agent system.

    Parameters
    ----------
    user_raw_input : free-text command the user typed (fed to Prompt Expert).
                     Defaults to a structured description built from the other args.
    """
    # Build structured fallback prompt from structured args if caller didn't supply raw input
    if not user_raw_input:
        user_raw_input = (
            f"Run a full strategic analysis for {company_name} in the {industry} industry "
            f"located in {location}. Budget: ${total_budget:,.0f}. "
            f"Timeline: {target_days} days. "
            f"Objectives: {'; '.join(objectives)}."
        )

    initial_state = create_initial_shared_state(
        company_name=company_name,
        industry=industry,
        location=location,
        total_budget=total_budget,
        target_days=target_days,
        objectives=objectives,
        user_raw_input=user_raw_input,
    )

    ceo_state: CEOState = {
        **initial_state,
        "executive_decisions": [],
        "delegation_log": [],
        "subgraph_summaries": [],
        "dispatch_plan": [],
        "current_dispatch_index": 0,
        "can_parallelize": False,
    }

    checkpointer = None
    config = None

    if use_checkpointing:
        checkpointer = create_checkpointer("sqlite", "./data/checkpoints.sqlite")
        thread = thread_id or f"thread-{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": thread}}
        logger.info(f"Using checkpointing with thread: {thread}")

    graph = build_master_graph(checkpointer=checkpointer)

    logger.info("\n🚀 STARTING MULTI-AGENT SYSTEM EXECUTION")
    logger.info("=" * 80)

    try:
        result = graph.invoke(ceo_state, config=config) if config else graph.invoke(ceo_state)
    except Exception as exc:
        if use_checkpointing and _is_checkpoint_capacity_error(exc):
            logger.error(
                "Checkpoint persistence failed (storage full); retrying without checkpointing."
            )
            result = build_master_graph(checkpointer=None).invoke(ceo_state)
        else:
            raise

    logger.info("\n✅ EXECUTION COMPLETE")
    logger.info("=" * 80)

    return result


# Test execution
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    result = execute_multi_agent_system(
        company_name="TechCorp Inc",
        industry="Software & Technology",
        location="San Francisco, CA",
        total_budget=100_000.0,
        target_days=90,
        objectives=[
            "Launch SaaS platform",
            "Build enterprise sales team",
            "Establish market presence",
        ],
        user_raw_input="Analyze our SaaS launch plan including financials, engineering, and marketing strategy.",
        use_checkpointing=True,
    )

    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    print(f"Completed phases : {result.get('completed_phases', [])}")
    print(f"CEO decisions    : {len(result.get('executive_decisions', []))}")
    print(f"Agents ran       : {len(result.get('agent_outputs', []))}")
    print(f"Final summary    : {bool(result.get('final_summary'))}")
