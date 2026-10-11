"""
Prompt Expert Agent — Node 0 in the master graph

Responsibility:
  ┌──────────────────────────────────────────────────────────────┐
  │  Raw user input  →  Structured, enriched task specification  │
  │  that drives deterministic routing through the CEO graph.    │
  └──────────────────────────────────────────────────────────────┘

Design rules:
  • This node runs BEFORE the CEO and does NOT make strategic decisions.
  • It only analyses intent, enriches language, and emits routing signals.
  • CEO is responsible for interpreting PromptExpertOutput and building
    the dispatch plan.
  • The Prompt Expert has NO access to tools or external APIs.
  • If the LLM is unavailable, fail explicitly without preset intake data.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict

from graph_architecture.schemas import (
    AgentRole,
    CEOState,
    LLMRoutingDecision,
    PromptExpertOutput,
    RiskLevel,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT (strict, non-creative instructions)
# ─────────────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are the Prompt Expert Agent inside a multi-agent LangGraph system.

Your ONLY job is to analyse the user's raw input and return a JSON object that
matches the PromptExpertOutput schema exactly. Do NOT add commentary outside
the JSON block.

RULES:
1. You NEVER make business decisions. You only parse and enrich.
2. You NEVER invent objectives not implied by the user's input.
3. You MUST set confidence_score honestly (0.0-1.0).
4. You MUST list any ambiguities you detect.
5. Per-agent prompts MUST be concise (≤120 words each) and domain-scoped.
6. Set requires_* flags to true only when the user clearly needs that domain.
7. primary_domain must be ONE of: finance, engineering, research, legal,
   marketing, strategy, unknown.

Return ONLY valid JSON. No markdown fences. No extra keys.

OUTPUT SCHEMA:
{
  "original_input": "<verbatim user input>",
  "intent_summary": "<one sentence>",
  "enriched_prompt": "<full enriched prompt for CEO node>",
  "primary_domain": "<domain>",
  "secondary_domains": ["<domain>", ...],

  // Tier-2 routing flags
  "requires_financial_analysis": true|false,
  "requires_engineering": true|false,
  "requires_research": true|false,
  "requires_legal": true|false,
  "requires_marketing": true|false,
  "requires_security_audit": true|false,

  // Tier-3 hint flags (read by Tier-2 subgraphs when decomposing work)
  "needs_ux_design": true|false,
  "needs_web_development": true|false,
  "needs_software_review": true|false,
  "needs_branding": true|false,
  "needs_content": true|false,
  "needs_campaign": true|false,
  "needs_social_media": true|false,

  "ceo_directive": "<strategic framing for CEO, ≤80 words>",
  "cfo_task_prompt": "<null or constrained CFO prompt, ≤120 words>",
  "engineer_task_prompt": "<null or constrained Engineer prompt, ≤120 words>",
  "researcher_task_prompt": "<null or constrained Researcher prompt, ≤120 words>",
  "legal_task_prompt": "<null or constrained Legal prompt, ≤120 words>",
  "martech_task_prompt": "<null or constrained Martech prompt, ≤120 words>",
  "security_task_prompt": "<null or constrained Security prompt, ≤120 words>",
  "priority": "critical|high|medium|low",
  "confidence_score": 0.0-1.0,
  "ambiguities": ["<string>", ...],
  "recommendations": ["<string>", ...]
}
"""


# ─────────────────────────────────────────────────────────────────────────────
# LLM CALL
# ─────────────────────────────────────────────────────────────────────────────


def _call_llm(user_input: str) -> PromptExpertOutput:
    """Call the configured LLM to parse and enrich user input."""
    try:
        from config import OPENAI_API_KEY, OPENAI_MODEL
        from langchain_openai import ChatOpenAI
        from services.usage_service import usage_callbacks
        from langchain_core.messages import HumanMessage, SystemMessage

        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set")

        llm = ChatOpenAI(
            model=OPENAI_MODEL,
            temperature=0.1,  # Near-deterministic for structured output
            max_tokens=1500,
            api_key=OPENAI_API_KEY,
            timeout=45,
            max_retries=0,
            callbacks=usage_callbacks(),
        )

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f"USER INPUT:\n{user_input}"),
        ]

        response = llm.invoke(messages)
        raw_text = response.content.strip()

        # Strip markdown fences if the model adds them anyway
        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
        raw_text = re.sub(r"\s*```$", "", raw_text, flags=re.MULTILINE)

        data = json.loads(raw_text)
        return PromptExpertOutput(**data)

    except Exception as exc:
        logger.error("Prompt Expert model call failed", exc_info=True)
        from exceptions import model_failure_message

        raise RuntimeError(
            model_failure_message(exc, "Prompt Expert failed; no preset intake was substituted")
        ) from exc


# ─────────────────────────────────────────────────────────────────────────────
# LANGGRAPH NODE
# ─────────────────────────────────────────────────────────────────────────────


def prompt_expert_node(state: CEOState) -> Dict[str, Any]:
    """
    LangGraph node — Prompt Expert Agent.

    Position in graph:  START → prompt_expert → initialize → ...

    Reads:
      state["user_raw_input"]           : raw user command
      state["strategic_objectives"]     : fallback if no raw input

    Writes:
      state["prompt_expert_output"]     : serialised PromptExpertOutput
      state["current_phase"]            : "prompt_expert_complete"
    """
    logger.info("\n" + "=" * 80)
    logger.info("🧠 PROMPT EXPERT AGENT — Analysing user intent")
    logger.info("=" * 80)

    raw_input: str = state.get("user_raw_input", "")

    # Build a synthetic input from objectives if no explicit raw input was given
    if not raw_input:
        objectives = state.get("strategic_objectives", [])
        company = state.get("company_name", "the company")
        raw_input = f"As {company}, achieve the following objectives: " + "; ".join(objectives)
        logger.info(f"No raw input — synthesising from {len(objectives)} objectives.")

    logger.info(f"Input (first 200 chars): {raw_input[:200]!r}")

    # Failed model intake must not be replaced with inferred scenario facts.
    result: PromptExpertOutput = _call_llm(raw_input)

    logger.info(f"  Intent:         {result.intent_summary}")
    logger.info(f"  Primary domain: {result.primary_domain.value}")
    logger.info(f"  Priority:       {result.priority.value}")
    logger.info(f"  Confidence:     {result.confidence_score:.2f}")
    tier2_flags = (
        f"finance={result.requires_financial_analysis}, "
        f"engineering={result.requires_engineering}, "
        f"research={result.requires_research}, "
        f"legal={result.requires_legal}, "
        f"marketing={result.requires_marketing}, "
        f"security={result.requires_security_audit}"
    )
    logger.info(f"  Tier-2 flags:   {tier2_flags}")
    tier3_flags = (
        f"ux={result.needs_ux_design}, webdev={result.needs_web_development}, "
        f"software={result.needs_software_review}, branding={result.needs_branding}, "
        f"content={result.needs_content}, campaign={result.needs_campaign}, "
        f"social={result.needs_social_media}"
    )
    logger.info(f"  Tier-3 hints:   {tier3_flags}")
    if result.ambiguities:
        logger.warning(f"  Ambiguities:    {result.ambiguities}")

    return {
        "prompt_expert_output": result.model_dump(),
        "current_phase": "prompt_expert_complete",
        "user_raw_input": raw_input,  # Ensure it's always in state
    }


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC HELPER — build LLMRoutingDecision from PromptExpertOutput
# (used by CEO router node, defined here for cohesion)
# ─────────────────────────────────────────────────────────────────────────────


def build_routing_decision_from_expert(
    expert_output: PromptExpertOutput,
) -> LLMRoutingDecision:
    """
    Build a deterministic LLMRoutingDecision from a PromptExpertOutput.

    The CEO LLM node can override this, but this gives a safe default
    for the CEO to refine rather than starting from scratch.
    """
    dispatch: list[AgentRole] = []
    rationale_parts: list[str] = []

    # CFO always goes first if finance is needed (budget gates other work)
    if expert_output.requires_financial_analysis:
        dispatch.append(AgentRole.CFO)
        rationale_parts.append("CFO first — budget analysis gates scope of other agents")

    if expert_output.requires_research:
        dispatch.append(AgentRole.RESEARCHER)
        rationale_parts.append("Researcher provides market context for execution decisions")

    if expert_output.requires_engineering:
        dispatch.append(AgentRole.ENGINEER)
        rationale_parts.append("Engineer implements after constraints are known")

    if expert_output.requires_legal:
        dispatch.append(AgentRole.LEGAL)
        rationale_parts.append("Legal compliance check required")

    if expert_output.requires_marketing:
        dispatch.append(AgentRole.MARTECH)
        rationale_parts.append("Martech strategy + Tier-3 campaign/content agents")

    if expert_output.requires_security_audit:
        dispatch.append(AgentRole.SECURITY)
        rationale_parts.append("Security audit required")

    # Default: if nothing flagged, route to researcher for strategic context
    if not dispatch:
        dispatch = [AgentRole.RESEARCHER]
        rationale_parts.append("No specific domain detected — defaulting to research")

    # Parallelisation: safe only when CFO is not first (no data dependency)
    can_parallelize = AgentRole.CFO not in dispatch and len(dispatch) > 1

    return LLMRoutingDecision(
        dispatch_plan=dispatch,
        rationale=" | ".join(rationale_parts),
        can_parallelize=can_parallelize,
        risk_assessment=RiskLevel.LOW,
        estimated_total_cost=0.0,
    )
