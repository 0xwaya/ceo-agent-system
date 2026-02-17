"""
Martech Subgraph — Tier-2 Domain Director

Internal structure  (sequential, LangGraph 0.0.20-compatible)
--------------------------------------------------------------
START → entry_guard → martech_strategy
      → branding (if needed, else pass-through)
      → content  (if needed, else pass-through)
      → campaign (if needed, else pass-through)
      → social_media (if needed, else pass-through)
      → exit_summary → END

Each Tier-3 node checks its own hint flag and skips if not required,
keeping routing simple and fully compatible with the conditional-edge API.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from langgraph.graph import END, START, StateGraph

from graph_architecture.schemas import SharedState
from graph_architecture.llm_nodes import (
    martech_llm_strategy_node,
    branding_llm_node,
    content_llm_node,
    campaign_llm_node,
    social_media_llm_node,
)

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER — read hint flag from state
# ============================================================================


def _hint(state: SharedState, flag: str) -> bool:
    expert = state.get("prompt_expert_output") or {}
    return bool(expert.get(flag, False))


# ============================================================================
# SUBGRAPH NODES
# ============================================================================


def _martech_entry_guard(state: SharedState) -> Dict[str, Any]:
    logger.info("📣 Martech Subgraph: entry guard passed")
    return {"active_agents": ["martech"]}


def _martech_strategy_node(state: SharedState) -> Dict[str, Any]:
    """Run Martech Director LLM — builds overall strategy."""
    logger.info("📣 Martech: running strategy analysis...")
    result = martech_llm_strategy_node(state)
    logger.info("✅ Martech strategy complete")
    return result


def _branding_node(state: SharedState) -> Dict[str, Any]:
    if not _hint(state, "needs_branding"):
        return {}
    logger.info("🎨 Martech → Branding specialist")
    return branding_llm_node(state)


def _content_node(state: SharedState) -> Dict[str, Any]:
    if not _hint(state, "needs_content"):
        return {}
    logger.info("✍️  Martech → Content specialist")
    return content_llm_node(state)


def _campaign_node(state: SharedState) -> Dict[str, Any]:
    if not _hint(state, "needs_campaign"):
        return {}
    logger.info("📊 Martech → Campaign specialist")
    return campaign_llm_node(state)


def _social_media_node(state: SharedState) -> Dict[str, Any]:
    if not _hint(state, "needs_social_media"):
        return {}
    logger.info("📱 Martech → Social Media specialist")
    return social_media_llm_node(state)


def _martech_exit_summary(state: SharedState) -> Dict[str, Any]:
    agent_outputs = state.get("agent_outputs", [])
    martech_outputs = [o for o in agent_outputs if o.get("domain") == "marketing"]
    logger.info(f"📣 Martech exit: {len(martech_outputs)} marketing outputs collected")
    return {"current_phase": "martech_complete"}


# ============================================================================
# GRAPH BUILDER
# ============================================================================


def build_martech_subgraph() -> StateGraph:
    """Build and compile the Martech Tier-2 subgraph with sequential Tier-3 nodes."""
    graph = StateGraph(SharedState)

    graph.add_node("entry_guard", _martech_entry_guard)
    graph.add_node("martech_strategy", _martech_strategy_node)
    graph.add_node("branding", _branding_node)
    graph.add_node("content", _content_node)
    graph.add_node("campaign", _campaign_node)
    graph.add_node("social_media", _social_media_node)
    graph.add_node("exit_summary", _martech_exit_summary)

    graph.add_edge(START, "entry_guard")
    graph.add_edge("entry_guard", "martech_strategy")
    graph.add_edge("martech_strategy", "branding")
    graph.add_edge("branding", "content")
    graph.add_edge("content", "campaign")
    graph.add_edge("campaign", "social_media")
    graph.add_edge("social_media", "exit_summary")
    graph.add_edge("exit_summary", END)

    return graph.compile()
