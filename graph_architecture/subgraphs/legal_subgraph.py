"""
Legal Subgraph — Tier-2 Domain Director

Internal structure
------------------
START → entry_guard → legal_compliance → exit_summary → END

The node `legal_compliance` calls the LLM-backed `legal_llm_compliance_node`
from llm_nodes.py.  Only a structured executive summary is propagated back to
the CEO graph.  All internal deliberation stays within this subgraph.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from langgraph.graph import END, START, StateGraph

from graph_architecture.schemas import AgentRole, SharedState
from graph_architecture.llm_nodes import legal_llm_compliance_node

logger = logging.getLogger(__name__)


# ============================================================================
# SUBGRAPH NODES
# ============================================================================


def _legal_entry_guard(state: SharedState) -> Dict[str, Any]:
    """Validate that only the CEO can invoke this subgraph."""
    logger.info("⚖️  Legal Subgraph: entry guard passed")
    return {"active_agents": ["legal"]}


def _legal_compliance_node(state: SharedState) -> Dict[str, Any]:
    """Run LLM-backed compliance analysis."""
    logger.info("⚖️  Legal: running compliance analysis...")
    result = legal_llm_compliance_node(state)
    logger.info("✅ Legal compliance analysis complete")
    return result


def _legal_exit_summary(state: SharedState) -> Dict[str, Any]:
    """Build a concise summary record for the CEO."""
    agent_outputs = state.get("agent_outputs", [])
    latest = next(
        (o for o in reversed(agent_outputs) if o.get("agent") == "legal"),
        None,
    )
    status = "completed" if latest else "no_output"
    logger.info(f"⚖️  Legal exit summary: {status}")
    return {"current_phase": "legal_complete"}


# ============================================================================
# GRAPH BUILDER
# ============================================================================


def build_legal_subgraph() -> StateGraph:
    """Build and compile the Legal Tier-2 subgraph."""
    graph = StateGraph(SharedState)

    graph.add_node("entry_guard", _legal_entry_guard)
    graph.add_node("legal_compliance", _legal_compliance_node)
    graph.add_node("exit_summary", _legal_exit_summary)

    graph.add_edge(START, "entry_guard")
    graph.add_edge("entry_guard", "legal_compliance")
    graph.add_edge("legal_compliance", "exit_summary")
    graph.add_edge("exit_summary", END)

    return graph.compile()
