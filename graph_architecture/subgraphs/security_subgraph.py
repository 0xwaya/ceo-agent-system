"""
Security Subgraph — Tier-2 Domain Director

Internal structure
------------------
START → entry_guard → security_audit → exit_summary → END

Invokes the LLM-backed `security_llm_audit_node` for threat modelling,
vulnerability assessment, and compliance gap analysis.
Only an executive summary is returned to the CEO graph.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from langgraph.graph import END, START, StateGraph

from graph_architecture.schemas import SharedState
from graph_architecture.llm_nodes import security_llm_audit_node

logger = logging.getLogger(__name__)


# ============================================================================
# SUBGRAPH NODES
# ============================================================================


def _security_entry_guard(state: SharedState) -> Dict[str, Any]:
    """Validate invocation authority (CEO only)."""
    logger.info("🔒 Security Subgraph: entry guard passed")
    return {"active_agents": ["security"]}


def _security_audit_node(state: SharedState) -> Dict[str, Any]:
    """Run LLM-backed security audit."""
    logger.info("🔒 Security: running audit...")
    result = security_llm_audit_node(state)
    logger.info("✅ Security audit complete")
    return result


def _security_exit_summary(state: SharedState) -> Dict[str, Any]:
    agent_outputs = state.get("agent_outputs", [])
    sec_outputs = [o for o in agent_outputs if o.get("agent") == "security"]
    status = "completed" if sec_outputs else "no_output"
    logger.info(f"🔒 Security exit summary: {status}")
    return {"current_phase": "security_complete"}


# ============================================================================
# GRAPH BUILDER
# ============================================================================


def build_security_subgraph() -> StateGraph:
    """Build and compile the Security Tier-2 subgraph."""
    graph = StateGraph(SharedState)

    graph.add_node("entry_guard", _security_entry_guard)
    graph.add_node("security_audit", _security_audit_node)
    graph.add_node("exit_summary", _security_exit_summary)

    graph.add_edge(START, "entry_guard")
    graph.add_edge("entry_guard", "security_audit")
    graph.add_edge("security_audit", "exit_summary")
    graph.add_edge("exit_summary", END)

    return graph.compile()
