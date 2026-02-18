"""
CTO Agent — Chief Technology Officer
====================================================
Tier-1 executive peer to the CEO Agent.

Responsibilities
----------------
- Own all technical architecture decisions
- Review and approve/reject tech stacks proposed by Tier-3 Web Dev & Software Eng agents
- Brief the CEO on engineering feasibility BEFORE dispatch decisions are finalised
- Enforce engineering guardrails (budget realism, timeline feasibility, tech-debt risk)
- Provide per-session LLM-backed conversational consultation via the chat panel

Architecture position
---------------------
  Graph:  START → privacy_scrub → prompt_expert → [CEO ‖ CTO] → dispatch_orchestrator
  CTO runs in parallel with the CEO at Tier 1 and writes to:
    - SharedState.cto_architecture_output    (full structured JSON)
    - SharedState.cto_tech_decisions         (list appended via operator.add)
    - SharedState.agent_outputs              (executive summary card)

Chat personas
-------------
  The CTO also powers the right-panel "Talk to CTO" chat in the v0.4 UI.
  See app.py :: _AGENT_PERSONAS["cto"] for the per-agent system prompt.

DEPRECATION NOTE
----------------
  This file is a THIN WRAPPER over the canonical LangGraph node defined in:
      graph_architecture/llm_nodes.py  ::  cto_llm_architecture_node

  Do NOT add business logic here. All LLM calls and state mutation belong in
  the LangGraph node.
"""

from __future__ import annotations

import warnings

# ── Canonical implementation ──────────────────────────────────────────────────
from graph_architecture.llm_nodes import cto_llm_architecture_node  # noqa: F401
from graph_architecture.schemas import AgentRole

# ── Public surface ────────────────────────────────────────────────────────────
CTO_ROLE = AgentRole.CTO

# Chat persona system prompt (also stored in app.py for the Flask backend)
CTO_CHAT_PERSONA = (
    "You are the CTO Agent for {company_name}, a {industry} company in {location}.\n\n"
    "You own all technical architecture decisions. You reviewed the Web Development agent's "
    "artifact recommending: Next.js 15 App Router + React Three Fiber + 8th Wall WebAR + "
    "Sanity CMS for a custom countertop visualizer (SurfaceCraft Studio).\n\n"
    "You speak about tech stacks, scalability, engineering timelines, CI/CD, and technical risk. "
    "You are pragmatic about budget constraints (current budget: ${budget}, timeline: {timeline} days). "
    "You defend sound technical choices with reasoning, but never gold-plate on a tight budget.\n\n"
    "Keep responses focused (2-4 paragraphs). When challenged, push back constructively with data."
)

__all__ = [
    "cto_llm_architecture_node",
    "CTO_ROLE",
    "CTO_CHAT_PERSONA",
]
