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
  • If the LLM is unavailable, a deterministic fallback runs instead.
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
    TaskDomain,
    TaskPriority,
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
# DETERMINISTIC FALLBACK (no LLM)
# ─────────────────────────────────────────────────────────────────────────────

_FINANCE_KEYWORDS = {
    "budget",
    "financial",
    "finance",
    "cost",
    "revenue",
    "profit",
    "loss",
    "cash",
    "investment",
    "roi",
    "spend",
    "expense",
    "forecast",
    "audit",
    "accounting",
    "p&l",
    "balance sheet",
    "funding",
    "valuation",
}
_ENGINEERING_KEYWORDS = {
    "build",
    "develop",
    "code",
    "software",
    "app",
    "application",
    "system",
    "platform",
    "api",
    "database",
    "architecture",
    "infrastructure",
    "deploy",
    "website",
    "mobile",
    "backend",
    "frontend",
    "microservice",
    "devops",
    "cloud",
    "aws",
    "azure",
    "gcp",
    "kubernetes",
}
_RESEARCH_KEYWORDS = {
    "research",
    "analyse",
    "analyze",
    "market",
    "competitor",
    "trend",
    "study",
    "survey",
    "data",
    "insight",
    "report",
    "benchmark",
    "review",
    "investigation",
    "discovery",
    "exploration",
}
_LEGAL_KEYWORDS = {
    "legal",
    "compliance",
    "law",
    "regulation",
    "contract",
    "trademark",
    "patent",
    "liability",
    "gdpr",
    "privacy",
    "terms",
    "licensing",
    "dba",
    "incorporation",
    "regulatory",
}
_MARKETING_KEYWORDS = {
    "marketing",
    "brand",
    "branding",
    "campaign",
    "social",
    "content",
    "seo",
    "ads",
    "advertising",
    "growth",
    "launch",
    "pr",
    "outreach",
    "audience",
    "engagement",
    "funnel",
    "conversion",
    "influencer",
    "email",
    "newsletter",
    "copywriting",
    "promotion",
}
_SECURITY_KEYWORDS = {
    "security",
    "hack",
    "breach",
    "vulnerability",
    "pentest",
    "audit",
    "blockchain",
    "crypto",
    "encrypt",
    "authentication",
    "authorization",
    "firewall",
    "zero trust",
    "sast",
    "dast",
    "cve",
    "infosec",
    "cyber",
    "threat",
    "compliance",
    "soc2",
    "iso27001",
}
_UX_KEYWORDS = {
    "ux",
    "ui",
    "user experience",
    "user interface",
    "design",
    "wireframe",
    "prototype",
    "figma",
    "accessibility",
    "usability",
}
_WEBDEV_KEYWORDS = {
    "website",
    "web app",
    "frontend",
    "react",
    "nextjs",
    "html",
    "css",
    "landing page",
    "web development",
}
_CONTENT_KEYWORDS = {
    "content",
    "blog",
    "article",
    "copy",
    "writing",
    "editorial",
    "script",
    "podcast",
    "video",
}


def _score_text(text: str, keywords: set) -> int:
    words = set(re.findall(r"\b\w+\b", text.lower()))
    return len(words & keywords)


def _fallback_parse(user_input: str) -> PromptExpertOutput:
    """
    Pure-Python intent parser — no LLM required.
    Used when the LLM call fails or no API key is configured.
    """
    lower_input = user_input.lower()

    finance_score = _score_text(lower_input, _FINANCE_KEYWORDS)
    eng_score = _score_text(lower_input, _ENGINEERING_KEYWORDS)
    research_score = _score_text(lower_input, _RESEARCH_KEYWORDS)
    legal_score = _score_text(lower_input, _LEGAL_KEYWORDS)
    marketing_score = _score_text(lower_input, _MARKETING_KEYWORDS)
    security_score = _score_text(lower_input, _SECURITY_KEYWORDS)

    domain_scores = {
        TaskDomain.FINANCE: finance_score,
        TaskDomain.ENGINEERING: eng_score,
        TaskDomain.RESEARCH: research_score,
        TaskDomain.LEGAL: legal_score,
        TaskDomain.MARKETING: marketing_score,
        TaskDomain.SECURITY: security_score,
    }

    # Pick primary domain
    primary_domain = max(domain_scores, key=lambda d: domain_scores[d])
    if domain_scores[primary_domain] == 0:
        primary_domain = TaskDomain.STRATEGY

    secondary_domains = [d for d, s in domain_scores.items() if s > 0 and d != primary_domain]

    requires_financial = finance_score > 0
    requires_engineering = eng_score > 0
    requires_research = research_score > 0
    requires_legal = legal_score > 0
    requires_marketing = marketing_score > 0
    requires_security = security_score > 0

    # Tier-3 hints
    needs_ux = _score_text(lower_input, _UX_KEYWORDS) > 0
    needs_webdev = _score_text(lower_input, _WEBDEV_KEYWORDS) > 0
    needs_content = _score_text(lower_input, _CONTENT_KEYWORDS) > 0

    # Build per-agent prompts only for required agents
    cfo_prompt = (
        f"Analyse the financial aspects of the following request and return a "
        f"structured CFOOutput with budget health, key numbers, risks, and a "
        f"single recommendation. Request context: {user_input[:400]}"
        if requires_financial
        else None
    )
    eng_prompt = (
        f"Design a technical solution for the following request. Return: "
        f"proposed tech stack, key architectural decisions, timeline estimate, "
        f"and a prioritised feature list. Context: {user_input[:400]}"
        if requires_engineering
        else None
    )
    research_prompt = (
        f"Conduct focused research on the following topic. Return: key findings, "
        f"top-3 recommendations, relevant benchmarks, and confidence level. "
        f"Topic: {user_input[:400]}"
        if requires_research
        else None
    )
    legal_prompt = (
        f"Identify legal risks and compliance requirements for the following request. "
        f"Return: applicable regulations, recommended actions, risk level. "
        f"Context: {user_input[:400]}"
        if requires_legal
        else None
    )
    martech_prompt = (
        f"Build a marketing strategy for the following request. "
        f"Return: target audience, channel mix, messaging, KPIs, and timeline. "
        f"Context: {user_input[:400]}"
        if requires_marketing
        else None
    )
    security_prompt = (
        f"Conduct a security and compliance audit for the following request. "
        f"Return: threat model, key vulnerabilities, recommended controls, compliance gaps. "
        f"Context: {user_input[:400]}"
        if requires_security
        else None
    )

    enriched = (
        f"[Fallback parse — LLM unavailable]\n\n"
        f"User request: {user_input}\n\n"
        f"Detected domains: finance={finance_score}, engineering={eng_score}, "
        f"research={research_score}, legal={legal_score}, "
        f"marketing={marketing_score}, security={security_score}.\n\n"
        f"Please proceed according to detected priorities."
    )

    return PromptExpertOutput(
        original_input=user_input,
        intent_summary="User request parsed via keyword analysis (fallback mode).",
        enriched_prompt=enriched,
        primary_domain=primary_domain,
        secondary_domains=secondary_domains,
        requires_financial_analysis=requires_financial,
        requires_engineering=requires_engineering,
        requires_research=requires_research,
        requires_legal=requires_legal,
        requires_marketing=requires_marketing,
        requires_security_audit=requires_security,
        needs_ux_design=needs_ux,
        needs_web_development=needs_webdev,
        needs_software_review=eng_score > 1,
        needs_branding=marketing_score > 1,
        needs_content=needs_content,
        needs_campaign=marketing_score > 2,
        needs_social_media=_score_text(
            lower_input, {"social", "instagram", "twitter", "linkedin", "tiktok"}
        )
        > 0,
        ceo_directive=(
            f"Process this user request with focus on {primary_domain.value}. "
            f"Involve secondary domains: {[d.value for d in secondary_domains]}."
        ),
        cfo_task_prompt=cfo_prompt,
        engineer_task_prompt=eng_prompt,
        researcher_task_prompt=research_prompt,
        legal_task_prompt=legal_prompt,
        martech_task_prompt=martech_prompt,
        security_task_prompt=security_prompt,
        priority=TaskPriority.MEDIUM,
        confidence_score=0.55,  # Fallback is lower confidence
        ambiguities=["LLM unavailable — intent parsed via keyword matching only"],
        recommendations=[],
    )


# ─────────────────────────────────────────────────────────────────────────────
# LLM CALL
# ─────────────────────────────────────────────────────────────────────────────


def _call_llm(user_input: str) -> PromptExpertOutput:
    """Call the configured LLM to parse and enrich user input."""
    try:
        from config import OPENAI_API_KEY, OPENAI_MODEL
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage

        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set")

        llm = ChatOpenAI(
            model=OPENAI_MODEL,
            temperature=0.1,  # Near-deterministic for structured output
            max_tokens=1500,
            api_key=OPENAI_API_KEY,
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

    except Exception as exc:  # Gracefully degrade to fallback
        logger.warning(
            f"PromptExpert LLM call failed ({type(exc).__name__}: {exc}). "
            f"Using deterministic fallback."
        )
        return _fallback_parse(user_input)


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

    # Parse — try LLM, fall back to keyword analysis
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
