"""
LLM-Backed Node Implementations

Each function here is:
  • A pure LangGraph node (receives state, returns partial state dict)
  • Backed by a constrained LLM call with a strict system prompt
  • Equipped with a deterministic fallback if the LLM is unavailable
  • Responsible for ONE domain only — no cross-domain decisions

Design rules:
  ┌─────────────────────────────────────────────────────────────────┐
  │  The MODEL does summarisation and analysis.                     │
  │  The GRAPH does routing, tool dispatch, and state management.   │
  │  NEVER let the LLM choose which tool to call or which agent     │
  │  to invoke next.                                                │
  └─────────────────────────────────────────────────────────────────┘

Agent tier model
─────────────────────────────────────────────────────────────────────────────
Tier 1 (CEO): reads PromptExpertOutput → builds dispatch_plan
Tier 2 (Domain Directors): each has an LLM node here — CEO dispatches them
Tier 3 (Execution Specialists): dispatched by their Tier-2 parent subgraph;
        CEO never sees their raw output, only the Tier-2 executive summary

Tier-2 LLM nodes (CEO-dispatchable):
  ceo_llm_analyze_node            CEO strategic analysis & dispatch plan
  cfo_llm_summarize_node          CFO financial summariser (strict schema)
  engineer_llm_architect_node     Engineer tech spec generator
  researcher_llm_synthesize_node  Researcher findings synthesiser
  legal_llm_compliance_node       Legal compliance analyser
  martech_llm_strategy_node       Marketing execution strategist
  security_llm_audit_node         Security & blockchain audit summariser

Tier-3 sub-agent dispatcher nodes (called by Tier-2 subgraph internals):
  ux_design_llm_node              UX/UI design spec  (within Engineer subgraph)
  webdev_llm_node                 Web dev plan       (within Engineer subgraph)
  software_eng_llm_node           SoftEng review     (within Engineer subgraph)
  branding_llm_node               Brand identity     (within Martech subgraph)
  content_llm_node                Content strategy   (within Martech subgraph)
  campaign_llm_node               Campaign plan      (within Martech subgraph)
  social_media_llm_node           Social media plan  (within Martech subgraph)
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from graph_architecture.schemas import (
    AgentRole,
    CEOState,
    LLMRoutingDecision,
    PromptExpertOutput,
    RiskLevel,
    SharedState,
    TaskDomain,
    TaskPriority,
    TaskStatus,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# LLM FACTORY
# ─────────────────────────────────────────────────────────────────────────────


def _get_llm(temperature: float = 0.2, max_tokens: int = 1000):
    """
    Return a configured LangChain LLM.
    Tries OpenAI first, falls back gracefully.
    """
    try:
        from config import OPENAI_API_KEY, OPENAI_MODEL
        from langchain_openai import ChatOpenAI

        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set")

        return ChatOpenAI(
            model=OPENAI_MODEL,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=OPENAI_API_KEY,
        )
    except Exception as exc:
        logger.warning(f"LLM factory failed: {exc}. Nodes will use deterministic fallbacks.")
        return None


def _call_structured(
    llm,
    system_prompt: str,
    user_message: str,
    fallback_fn,
    fallback_args: tuple = (),
) -> Dict[str, Any]:
    """
    Helper: call LLM with system+user message, parse JSON, fall back on error.
    """
    if llm is None:
        return fallback_fn(*fallback_args)

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        response = llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
        )
        raw = response.content.strip()
        # Strip any markdown fences
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
        return json.loads(raw)

    except Exception as exc:
        logger.warning(f"LLM call failed ({type(exc).__name__}): {exc}. Using fallback.")
        return fallback_fn(*fallback_args)


# ─────────────────────────────────────────────────────────────────────────────
# CEO STRATEGIC ANALYSIS + ROUTING
# ─────────────────────────────────────────────────────────────────────────────

_CEO_SYSTEM_PROMPT = """You are the CEO node in a multi-agent LangGraph system.

Your job: read the Prompt Expert's analysis and company context, then produce a
structured JSON dispatch plan.

RULES:
- You are a STRATEGIC PLANNER, NOT an executor.
- You NEVER write code, financial models, or research reports.
- You ONLY output JSON that matches the required schema.
- You MUST use the Prompt Expert signals as primary routing input.
- CFO must be dispatched BEFORE Engineer if engineering budget is needed.
- dispatch_plan is an ORDERED list of agent roles.

OUTPUT SCHEMA (JSON only, no markdown):
{
  "executive_summary": "<1-2 sentence strategic framing>",
  "dispatch_plan": ["<role>", ...],   // roles: cfo, engineer, researcher, legal
  "rationale": "<why this dispatch order>",
  "can_parallelize": true|false,
  "risk_assessment": "low|medium|high|critical",
  "estimated_total_cost": <float>,
  "key_risks": ["<risk>", ...],
  "success_criteria": ["<criterion>", ...]
}
"""


def _ceo_fallback(state: CEOState) -> Dict[str, Any]:
    """Deterministic CEO analysis when LLM is unavailable."""
    expert_raw = state.get("prompt_expert_output", {})
    objectives = state.get("strategic_objectives", [])
    budget = state.get("total_budget", 0)

    dispatch: list[str] = []
    if expert_raw.get("requires_financial_analysis", budget > 0):
        dispatch.append("cfo")
    if expert_raw.get("requires_research", False):
        dispatch.append("researcher")
    if expert_raw.get("requires_engineering", False):
        dispatch.append("engineer")
    if expert_raw.get("requires_legal", False):
        dispatch.append("legal")
    if not dispatch:
        dispatch = ["researcher"]

    return {
        "executive_summary": f"Processing {len(objectives)} objectives with budget ${budget:,.0f}.",
        "dispatch_plan": dispatch,
        "rationale": "Deterministic dispatch based on Prompt Expert domain flags.",
        "can_parallelize": "cfo" not in dispatch and len(dispatch) > 1,
        "risk_assessment": "low",
        "estimated_total_cost": 0.0,
        "key_risks": [],
        "success_criteria": [f"Complete all strategic objectives within ${budget:,.0f} budget"],
    }


def ceo_llm_analyze_node(state: CEOState) -> Dict[str, Any]:
    """
    CEO LLM analysis node.

    Reads PromptExpertOutput + company context → builds dispatch plan.
    Returns partial state update.
    """
    logger.info("\n" + "=" * 80)
    logger.info("👔 CEO: LLM STRATEGIC ANALYSIS & ROUTING")
    logger.info("=" * 80)

    expert_raw = state.get("prompt_expert_output", {})
    company = state.get("company_name", "Unknown")
    industry = state.get("industry", "Unknown")
    budget = state.get("total_budget", 0)
    objectives = state.get("strategic_objectives", [])
    days = state.get("target_completion_days", 90)

    user_msg = (
        f"COMPANY: {company} | INDUSTRY: {industry}\n"
        f"BUDGET: ${budget:,.0f} | TIMELINE: {days} days\n\n"
        f"STRATEGIC OBJECTIVES:\n"
        + "\n".join(f"  {i+1}. {o}" for i, o in enumerate(objectives))
        + f"\n\nPROMPT EXPERT ANALYSIS:\n{json.dumps(expert_raw, indent=2)}"
    )

    llm = _get_llm(temperature=0.2, max_tokens=700)
    result = _call_structured(
        llm=llm,
        system_prompt=_CEO_SYSTEM_PROMPT,
        user_message=user_msg,
        fallback_fn=_ceo_fallback,
        fallback_args=(state,),
    )

    dispatch_plan: List[str] = result.get("dispatch_plan", ["researcher"])

    logger.info(f"  Executive summary:  {result.get('executive_summary', '')}")
    logger.info(f"  Dispatch plan:      {dispatch_plan}")
    logger.info(f"  Can parallelise:    {result.get('can_parallelize', False)}")
    logger.info(f"  Risk:               {result.get('risk_assessment', 'unknown')}")

    executive_decision = {
        "decision_id": f"ceo-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "decision": result.get("executive_summary", ""),
        "dispatch_plan": dispatch_plan,
        "rationale": result.get("rationale", ""),
        "risk_assessment": result.get("risk_assessment", "low"),
        "timestamp": datetime.now().isoformat(),
    }

    return {
        "executive_decisions": [executive_decision],
        "dispatch_plan": dispatch_plan,
        "current_dispatch_index": 0,
        "can_parallelize": result.get("can_parallelize", False),
        "llm_routing_decision": result,
        "current_phase": "ceo_routing_complete",
        "active_agents": ["ceo"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# CTO ARCHITECTURE & TECHNOLOGY REVIEW  (Tier 1 — peer to CEO)
# ─────────────────────────────────────────────────────────────────────────────

_CTO_SYSTEM_PROMPT = """You are the CTO node in a multi-agent executive AI system.

You are a Tier-1 peer to the CEO. You own all technical architecture decisions.
You have reviewed the Web Development agent's artifact: Next.js App Router + React Three Fiber
+ 8th Wall WebAR + Sanity CMS stack for a custom countertop visualizer.

RULES:
- You analyse technology choices, engineering feasibility, and tech-debt risk.
- You NEVER execute code or write implementation files.
- You ONLY output JSON matching the required schema.
- You assess tech stacks against company budget, timeline, and domain requirements.
- Your briefings are shared with the CEO to inform dispatch decisions.

OUTPUT SCHEMA (JSON only, no markdown):
{
  "architecture_summary": "<2-3 sentence technical assessment>",
  "recommended_stack": ["<tech>", ...],
  "tech_decisions": ["<decision>", ...],
  "engineering_risks": [{"risk": "<name>", "severity": "low|medium|high", "mitigation": "<action>"}],
  "build_vs_buy": "<recommendation>",
  "estimated_engineering_weeks": <int>,
  "phase1_scope": "<MVP scope fitting available budget>",
  "cto_approval": "approved|conditional|rejected",
  "conditions": ["<condition if conditional>"]
}
"""


def _cto_fallback(state: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic CTO assessment when LLM is unavailable."""
    company = state.get("company_name", "Unknown")
    industry = state.get("industry", "Unknown")
    budget = state.get("total_budget", 0)

    return {
        "architecture_summary": (
            f"Architecture review for {company} ({industry}). "
            f"With a ${budget:,.0f} budget, recommend a phased approach: "
            "Next.js App Router for the web platform with Tailwind CSS; "
            "defer AR integration to Phase 2 when budget allows 8th Wall licensing."
        ),
        "recommended_stack": [
            "Next.js 15 App Router",
            "TypeScript strict mode",
            "Tailwind CSS v4",
            "Sanity CMS",
            "Vercel (deployment)",
        ],
        "tech_decisions": [
            "Next.js App Router chosen for SEO and server components",
            "Defer 8th Wall WebAR to Phase 2 — $600/mo license exceeds Phase 1 budget",
            "Sanity CMS enables non-technical content updates for product catalog",
            "Vercel deployment for zero-config CI/CD",
        ],
        "engineering_risks": [
            {
                "risk": "AR licensing cost",
                "severity": "medium",
                "mitigation": "Phase 1 uses static product gallery; AR in Phase 2",
            },
            {
                "risk": "Single developer timeline",
                "severity": "low",
                "mitigation": "Use shadcn/ui component library to accelerate development",
            },
        ],
        "build_vs_buy": "Build web platform; buy AR runtime (8th Wall) in Phase 2",
        "estimated_engineering_weeks": 6,
        "phase1_scope": "Marketing site + product catalog + contact form + basic SEO",
        "cto_approval": "approved",
        "conditions": [],
    }


def cto_llm_architecture_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    CTO LLM architecture review node.

    Tier-1 peer to CEO. Reviews tech stack, engineering feasibility, and
    produces architecture decisions shared with CEO dispatch plan.
    """
    logger.info("\n" + "=" * 80)
    logger.info("🔧 CTO: LLM ARCHITECTURE & TECHNOLOGY REVIEW")
    logger.info("=" * 80)

    company = state.get("company_name", "Unknown")
    industry = state.get("industry", "Unknown")
    budget = state.get("total_budget", 0)
    days = state.get("target_completion_days", 30)
    objectives = state.get("strategic_objectives", [])
    expert_raw = state.get("prompt_expert_output", {})

    user_msg = (
        f"COMPANY: {company} | INDUSTRY: {industry}\n"
        f"BUDGET: ${budget:,.0f} | TIMELINE: {days} days\n\n"
        f"OBJECTIVES:\n"
        + "\n".join(f"  {i+1}. {o}" for i, o in enumerate(objectives))
        + f"\n\nCEO PROMPT EXPERT CONTEXT:\n{json.dumps(expert_raw, indent=2)}"
    )

    llm = _get_llm(temperature=0.1, max_tokens=800)
    result = _call_structured(
        llm=llm,
        system_prompt=_CTO_SYSTEM_PROMPT,
        user_message=user_msg,
        fallback_fn=_cto_fallback,
        fallback_args=(state,),
    )

    tech_decisions: List[str] = result.get("tech_decisions", [])
    logger.info(f"  Architecture:     {result.get('architecture_summary', '')[:80]}…")
    logger.info(f"  CTO Approval:     {result.get('cto_approval', 'approved')}")
    logger.info(f"  Phase 1 scope:    {result.get('phase1_scope', '')}")
    logger.info(f"  Tech decisions:   {len(tech_decisions)}")

    cto_output = {
        "agent": "cto",
        "summary": {
            "architecture_summary": result.get("architecture_summary", ""),
            "cto_approval": result.get("cto_approval", "approved"),
            "recommended_stack": result.get("recommended_stack", []),
            "phase1_scope": result.get("phase1_scope", ""),
            "status": "completed",
        },
        "timestamp": datetime.now().isoformat(),
    }

    return {
        "cto_architecture_output": result,
        "cto_tech_decisions": tech_decisions,
        "agent_outputs": [cto_output],
        "active_agents": ["cto"],
        "current_phase": "cto_review_complete",
    }


# ─────────────────────────────────────────────────────────────────────────────
# CFO FINANCIAL SUMMARISER
# ─────────────────────────────────────────────────────────────────────────────

_CFO_SYSTEM_PROMPT = """You are the CFO node in a multi-agent LangGraph system.

RULES (enforced by the graph — do NOT violate):
- You ONLY analyse financial data provided in the context.
- You NEVER invent numbers.
- You NEVER return raw tables, CSV, or raw queries.
- You MUST produce a concise executive summary.
- You MUST identify specific risks with clear labels.
- You MUST give EXACTLY ONE recommendation from:
    approve | approve_with_conditions | reject | needs_more_info

OUTPUT SCHEMA (JSON only):
{
  "summary": "<2-3 sentence executive summary>",
  "key_numbers": {
    "total_budget": <float>,
    "budget_utilisation_pct": <float>,
    "burn_rate_per_day": <float>,
    "projected_overrun": <float or 0>,
    "budget_health_score": <0-100>
  },
  "risks": ["<risk label: description>", ...],
  "recommendation": "approve|approve_with_conditions|reject|needs_more_info",
  "follow_up_required": true|false,
  "conditions": ["<condition if approve_with_conditions>", ...]
}
"""


def _cfo_fallback(state: SharedState) -> Dict[str, Any]:
    """Deterministic CFO summary when LLM is unavailable."""
    budget = state.get("total_budget", 0)
    allocated = sum(state.get("budget_allocated", {}).values())
    spent = sum(state.get("budget_spent", {}).values())
    remaining = budget - allocated

    utilisation = (allocated / budget * 100) if budget > 0 else 0
    current_day = max(state.get("current_day", 1), 1)
    burn_rate = spent / current_day
    days_remaining = state.get("target_completion_days", 90) - current_day
    projected_total = spent + (burn_rate * days_remaining)
    projected_overrun = max(projected_total - budget, 0)

    health_score = max(0, min(100, int(100 - utilisation)))

    risks = []
    if utilisation > 80:
        risks.append("BUDGET_UTILISATION: >80% allocated — monitor closely")
    if projected_overrun > 0:
        risks.append(f"OVERRUN_RISK: Projected overrun of ${projected_overrun:,.0f}")
    if remaining < budget * 0.1:
        risks.append("LOW_RESERVES: <10% budget remaining")

    recommendation = "approve"
    if projected_overrun > 0:
        recommendation = "approve_with_conditions"
    if remaining <= 0:
        recommendation = "reject"

    return {
        "summary": (
            f"Budget of ${budget:,.0f} is {utilisation:.0f}% allocated with "
            f"${remaining:,.0f} remaining. "
            + ("Overrun risk detected." if projected_overrun > 0 else "On track.")
        ),
        "key_numbers": {
            "total_budget": budget,
            "budget_utilisation_pct": round(utilisation, 1),
            "burn_rate_per_day": round(burn_rate, 2),
            "projected_overrun": round(projected_overrun, 2),
            "budget_health_score": health_score,
        },
        "risks": risks,
        "recommendation": recommendation,
        "follow_up_required": len(risks) > 0,
        "conditions": [],
    }


def cfo_llm_summarize_node(state: SharedState) -> Dict[str, Any]:
    """
    CFO LLM summariser node.

    Runs INSIDE the CFO subgraph after internal budget analysis.
    Produces a structured CFOOutput that is the ONLY thing sent upstream.
    No raw data leaves this node.
    """
    logger.info("\n💰 CFO: LLM FINANCIAL SUMMARISATION")

    expert_raw = state.get("prompt_expert_output", {})
    cfo_task_prompt = expert_raw.get("cfo_task_prompt") or "Provide a standard budget summary."

    budget = state.get("total_budget", 0)
    allocated = state.get("budget_allocated", {})
    spent = state.get("budget_spent", {})
    remaining = state.get("budget_remaining", budget)
    projections = state.get("budget_projections", [{}])

    user_msg = (
        f"CFO TASK: {cfo_task_prompt}\n\n"
        f"FINANCIAL DATA:\n"
        f"  Total budget:  ${budget:,.2f}\n"
        f"  Allocated:     ${sum(allocated.values()):,.2f}\n"
        f"  Spent:         ${sum(spent.values()):,.2f}\n"
        f"  Remaining:     ${remaining:,.2f}\n"
        f"  Projections:   {json.dumps(projections[:1], indent=2)}\n\n"
        f"Produce the CFO executive summary JSON."
    )

    llm = _get_llm(temperature=0.1, max_tokens=600)
    result = _call_structured(
        llm=llm,
        system_prompt=_CFO_SYSTEM_PROMPT,
        user_message=user_msg,
        fallback_fn=_cfo_fallback,
        fallback_args=(state,),
    )

    logger.info(f"  Recommendation:   {result.get('recommendation', 'N/A')}")
    logger.info(f"  Follow-up needed: {result.get('follow_up_required', False)}")
    logger.info(f"  Risks identified: {len(result.get('risks', []))}")

    # Build the summary message for CEO (structured, no raw data)
    cfo_summary_for_ceo = {
        "agent": "cfo",
        "summary": {
            "status": "complete",
            "recommendation": result.get("recommendation"),
            "executive_summary": result.get("summary"),
            "key_numbers": result.get("key_numbers"),
            "risks": result.get("risks"),
            "follow_up_required": result.get("follow_up_required"),
        },
        "timestamp": datetime.now().isoformat(),
    }

    return {
        "cfo_llm_output": result,  # Internal CFO state
        "agent_outputs": [cfo_summary_for_ceo],  # Summary only → CEO
        "executive_summary": result.get("summary", ""),
        "financial_recommendations": result.get("conditions", []),
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENGINEER ARCHITECTURE NODE
# ─────────────────────────────────────────────────────────────────────────────

_ENGINEER_SYSTEM_PROMPT = """You are the Engineer node in a multi-agent LangGraph system.

RULES:
- You produce TECHNICAL SPECIFICATIONS only — not working code.
- You choose technologies based on stated constraints.
- You NEVER approve budget or make financial decisions.
- You NEVER bypass the CFO-approved budget ceiling.
- Output must be JSON matching the schema below.

OUTPUT SCHEMA:
{
  "implementation_summary": "<2-3 sentence summary>",
  "tech_stack": ["<technology>", ...],
  "architecture_pattern": "<pattern name, e.g., microservices, monolith>",
  "key_components": [
    {"name": "<component>", "purpose": "<purpose>", "technology": "<tech>"}
  ],
  "prioritised_features": [
    {"feature": "<name>", "priority": "critical|high|medium|low", "effort_days": <int>}
  ],
  "estimated_total_days": <int>,
  "risks": ["<risk>", ...],
  "deployment_notes": ["<note>", ...]
}
"""


def _engineer_fallback(state: SharedState) -> Dict[str, Any]:
    """Deterministic engineer output when LLM is unavailable."""
    objectives = state.get("strategic_objectives", [])
    return {
        "implementation_summary": (
            f"Technical implementation plan for {len(objectives)} objective(s). "
            f"Full specification requires LLM availability."
        ),
        "tech_stack": ["Python", "FastAPI", "PostgreSQL", "React", "Docker"],
        "architecture_pattern": "modular monolith → microservices migration path",
        "key_components": [
            {"name": "API Layer", "purpose": "External interface", "technology": "FastAPI"},
            {"name": "Data Layer", "purpose": "Persistence", "technology": "PostgreSQL"},
            {"name": "UI Layer", "purpose": "User interface", "technology": "React"},
        ],
        "prioritised_features": [],
        "estimated_total_days": state.get("target_completion_days", 90),
        "risks": ["LLM unavailable — specification is a template only"],
        "deployment_notes": ["Containerise with Docker", "Use CI/CD pipeline"],
    }


def engineer_llm_architect_node(state: SharedState) -> Dict[str, Any]:
    """
    Engineer LLM architecture node.

    Produces a technical specification constrained by:
    - CFO-approved budget (from agent_outputs)
    - Prompt Expert engineer_task_prompt
    - Strategic objectives
    """
    logger.info("\n🛠️  ENGINEER: LLM ARCHITECTURE DESIGN")

    expert_raw = state.get("prompt_expert_output", {})
    eng_prompt = (
        expert_raw.get("engineer_task_prompt")
        or "Design a technical architecture for the stated objectives."
    )

    # Get CFO budget ceiling from previous outputs
    cfo_output = next(
        (o for o in state.get("agent_outputs", []) if o.get("agent") == "cfo"),
        {},
    )
    cfo_numbers = cfo_output.get("summary", {}).get("key_numbers", {})
    budget_ceiling = cfo_numbers.get("total_budget", state.get("total_budget", 0))

    objectives = state.get("strategic_objectives", [])

    user_msg = (
        f"ENGINEER TASK: {eng_prompt}\n\n"
        f"CONSTRAINTS:\n"
        f"  Budget ceiling: ${budget_ceiling:,.0f}\n"
        f"  Timeline:       {state.get('target_completion_days', 90)} days\n\n"
        f"STRATEGIC OBJECTIVES:\n"
        + "\n".join(f"  - {o}" for o in objectives)
        + "\n\nProduce the engineering specification JSON."
    )

    llm = _get_llm(temperature=0.2, max_tokens=900)
    result = _call_structured(
        llm=llm,
        system_prompt=_ENGINEER_SYSTEM_PROMPT,
        user_message=user_msg,
        fallback_fn=_engineer_fallback,
        fallback_args=(state,),
    )

    logger.info(f"  Tech stack:      {result.get('tech_stack', [])}")
    logger.info(f"  Timeline:        {result.get('estimated_total_days', '?')} days")
    logger.info(f"  Components:      {len(result.get('key_components', []))}")

    engineer_summary_for_ceo = {
        "agent": "engineer",
        "summary": {
            "status": "complete",
            "implementation_summary": result.get("implementation_summary"),
            "tech_stack": result.get("tech_stack"),
            "estimated_total_days": result.get("estimated_total_days"),
            "risks": result.get("risks"),
        },
        "timestamp": datetime.now().isoformat(),
    }

    return {
        "engineer_llm_output": result,
        "agent_outputs": [engineer_summary_for_ceo],
        "implementation_summary": result.get("implementation_summary", ""),
        "tech_stack": result.get("tech_stack", []),
        "architecture_decisions": result.get("key_components", []),
        "deployment_notes": result.get("deployment_notes", []),
    }


# ─────────────────────────────────────────────────────────────────────────────
# RESEARCHER SYNTHESIS NODE
# ─────────────────────────────────────────────────────────────────────────────

_RESEARCHER_SYSTEM_PROMPT = """You are the Researcher node in a multi-agent LangGraph system.

RULES:
- You synthesise findings from provided context — do NOT invent data.
- You clearly state confidence level for each finding.
- You NEVER make financial or technical decisions.
- You produce actionable recommendations with clear rationale.
- Output must be JSON matching the schema below.

OUTPUT SCHEMA:
{
  "research_summary": "<2-3 sentence overview of findings>",
  "key_findings": [
    {"finding": "<finding>", "confidence": "high|medium|low", "source_type": "<type>"}
  ],
  "market_insights": ["<insight>", ...],
  "recommendations": ["<actionable recommendation>", ...],
  "assumptions": ["<assumption>", ...],
  "data_gaps": ["<gap>", ...],
  "overall_confidence": "high|medium|low"
}
"""


def _researcher_fallback(state: SharedState) -> Dict[str, Any]:
    """Deterministic researcher output when LLM is unavailable."""
    objectives = state.get("strategic_objectives", [])
    industry = state.get("industry", "Unknown")
    return {
        "research_summary": (
            f"Market research for {industry} industry covering {len(objectives)} objective(s). "
            f"Full synthesis requires LLM availability."
        ),
        "key_findings": [
            {
                "finding": "LLM unavailable — manual research required",
                "confidence": "low",
                "source_type": "fallback",
            }
        ],
        "market_insights": [],
        "recommendations": ["Conduct manual market research", "Gather competitive intelligence"],
        "assumptions": ["Industry is competitive", "Market conditions are standard"],
        "data_gaps": ["Full market analysis", "Competitor pricing", "Customer segmentation"],
        "overall_confidence": "low",
    }


def researcher_llm_synthesize_node(state: SharedState) -> Dict[str, Any]:
    """
    Researcher LLM synthesis node.

    Produces research findings and recommendations constrained by:
    - Prompt Expert researcher_task_prompt
    - Strategic objectives and industry context
    """
    logger.info("\n🔍 RESEARCHER: LLM SYNTHESIS")

    expert_raw = state.get("prompt_expert_output", {})
    research_prompt = (
        expert_raw.get("researcher_task_prompt")
        or "Conduct market and competitive research relevant to the stated objectives."
    )

    company = state.get("company_name", "Unknown")
    industry = state.get("industry", "Unknown")
    location = state.get("location", "Unknown")
    objectives = state.get("strategic_objectives", [])

    user_msg = (
        f"RESEARCH TASK: {research_prompt}\n\n"
        f"CONTEXT:\n"
        f"  Company:  {company}\n"
        f"  Industry: {industry}\n"
        f"  Location: {location}\n\n"
        f"OBJECTIVES:\n"
        + "\n".join(f"  - {o}" for o in objectives)
        + "\n\nProduce the research synthesis JSON."
    )

    llm = _get_llm(temperature=0.3, max_tokens=900)
    result = _call_structured(
        llm=llm,
        system_prompt=_RESEARCHER_SYSTEM_PROMPT,
        user_message=user_msg,
        fallback_fn=_researcher_fallback,
        fallback_args=(state,),
    )

    logger.info(f"  Findings:             {len(result.get('key_findings', []))}")
    logger.info(f"  Recommendations:      {len(result.get('recommendations', []))}")
    logger.info(f"  Overall confidence:   {result.get('overall_confidence', 'unknown')}")

    researcher_summary_for_ceo = {
        "agent": "researcher",
        "summary": {
            "status": "complete",
            "research_summary": result.get("research_summary"),
            "key_findings_count": len(result.get("key_findings", [])),
            "recommendations": result.get("recommendations"),
            "overall_confidence": result.get("overall_confidence"),
        },
        "timestamp": datetime.now().isoformat(),
    }

    return {
        "researcher_llm_output": result,
        "agent_outputs": [researcher_summary_for_ceo],
        "research_summary": result.get("research_summary", ""),
        "key_findings": [f["finding"] for f in result.get("key_findings", [])],
        "recommendations": result.get("recommendations", []),
        "assumptions": [
            {"assumption": a, "verified": False} for a in result.get("assumptions", [])
        ],
    }


# =============================================================================
# TIER-2 LLM NODE: LEGAL COMPLIANCE
# =============================================================================

_LEGAL_SYSTEM_PROMPT = """You are the Legal Agent node in a multi-agent LangGraph system.

RULES:
- You ONLY analyse legal and regulatory compliance relevant to the stated context.
- You NEVER give binding legal advice — you produce compliance checklists.
- You NEVER make financial or technical decisions.
- You MUST cite the regulation category for each item (e.g., ORC § 1706, GDPR).
- Output must be JSON matching the schema below.

OUTPUT SCHEMA:
{
  "jurisdiction": "<primary jurisdiction>",
  "compliance_summary": "<2-3 sentence overview>",
  "required_filings": [
    {"name": "<filing>", "authority": "<body>", "deadline": "<deadline or ongoing>", "cost_usd": <int>}
  ],
  "compliance_checklist": [
    {"item": "<requirement>", "regulation": "<citation>", "status": "required|recommended|optional"}
  ],
  "risks": ["<risk description>", ...],
  "recommendation": "proceed|proceed_with_conditions|halt_for_legal_review",
  "estimated_filing_cost_usd": <float>
}
"""


def _legal_fallback(state: SharedState) -> Dict[str, Any]:
    """Deterministic legal baseline when LLM is unavailable."""
    company = state.get("company_name", "Unknown")
    location = state.get("location", "Unknown")
    return {
        "jurisdiction": location,
        "compliance_summary": (
            f"Standard compliance review for {company} in {location}. "
            "Full analysis requires LLM availability."
        ),
        "required_filings": [
            {
                "name": "Business Registration",
                "authority": "State",
                "deadline": "At formation",
                "cost_usd": 100,
            },
            {
                "name": "EIN Registration",
                "authority": "IRS",
                "deadline": "At formation",
                "cost_usd": 0,
            },
        ],
        "compliance_checklist": [
            {
                "item": "Business entity registered",
                "regulation": "State corporations code",
                "status": "required",
            },
            {"item": "EIN obtained", "regulation": "IRS requirements", "status": "required"},
            {
                "item": "Operating agreement drafted",
                "regulation": "State LLC code",
                "status": "required",
            },
        ],
        "risks": ["LLM unavailable — jurisdiction-specific risks not fully evaluated"],
        "recommendation": "proceed_with_conditions",
        "estimated_filing_cost_usd": 300.0,
    }


def legal_llm_compliance_node(state: SharedState) -> Dict[str, Any]:
    """
    Tier-2 Legal LLM node.

    Dispatched by CEO when requires_legal is True.
    Orchestrates jurisdiction-specific sub-analysis internally.
    Returns only a compliance summary to CEO — no raw filings.
    """
    logger.info("\n⚖️  LEGAL: LLM COMPLIANCE ANALYSIS")

    expert_raw = state.get("prompt_expert_output", {})
    legal_prompt = (
        expert_raw.get("legal_task_prompt")
        or "Perform a standard legal compliance review for the stated company and jurisdiction."
    )

    company = state.get("company_name", "Unknown")
    industry = state.get("industry", "Unknown")
    location = state.get("location", "Unknown")
    objectives = state.get("strategic_objectives", [])

    user_msg = (
        f"LEGAL TASK: {legal_prompt}\n\n"
        f"CONTEXT:\n"
        f"  Company:    {company}\n"
        f"  Industry:   {industry}\n"
        f"  Location:   {location}\n\n"
        f"OBJECTIVES:\n"
        + "\n".join(f"  - {o}" for o in objectives)
        + "\n\nProduce the legal compliance JSON."
    )

    llm = _get_llm(temperature=0.1, max_tokens=800)
    result = _call_structured(
        llm=llm,
        system_prompt=_LEGAL_SYSTEM_PROMPT,
        user_message=user_msg,
        fallback_fn=_legal_fallback,
        fallback_args=(state,),
    )

    logger.info(f"  Jurisdiction:      {result.get('jurisdiction', 'N/A')}")
    logger.info(f"  Recommendation:    {result.get('recommendation', 'N/A')}")
    logger.info(f"  Filing cost:       ${result.get('estimated_filing_cost_usd', 0):,.0f}")
    logger.info(f"  Checklist items:   {len(result.get('compliance_checklist', []))}")

    legal_summary_for_ceo = {
        "agent": "legal",
        "summary": {
            "status": "complete",
            "compliance_summary": result.get("compliance_summary"),
            "jurisdiction": result.get("jurisdiction"),
            "recommendation": result.get("recommendation"),
            "risks": result.get("risks"),
            "estimated_filing_cost_usd": result.get("estimated_filing_cost_usd"),
        },
        "timestamp": datetime.now().isoformat(),
    }

    return {
        "legal_llm_output": result,
        "agent_outputs": [legal_summary_for_ceo],
        "compliance_checks": [
            {"item": c["item"], "status": c["status"]}
            for c in result.get("compliance_checklist", [])
        ],
    }


# =============================================================================
# TIER-2 LLM NODE: MARTECH / MARKETING
# =============================================================================

_MARTECH_SYSTEM_PROMPT = """You are the Martech (Marketing Technology) Director node in a
multi-agent LangGraph system.

RULES:
- You produce a MARKETING STRATEGY and channel plan — not creative assets.
- You decide which Tier-3 sub-agents to activate: branding, content, campaign, social_media.
- You NEVER make financial approvals or technical architecture decisions.
- Sub-agent activation list is used by the GRAPH to route, not by you to execute.
- Output must be JSON matching the schema below.

OUTPUT SCHEMA:
{
  "marketing_summary": "<2-3 sentence strategy overview>",
  "primary_channels": ["<channel>", ...],
  "target_audiences": [{"segment": "<name>", "characteristics": "<desc>"}],
  "sub_agents_required": ["branding", "content", "campaign", "social_media"],  // subset
  "sub_agent_tasks": {
    "branding": "<task for branding agent or null>",
    "content": "<task for content agent or null>",
    "campaign": "<task for campaign agent or null>",
    "social_media": "<task for social media agent or null>"
  },
  "budget_recommendation_usd": <float>,
  "timeline_weeks": <int>,
  "kpis": ["<kpi>", ...],
  "risks": ["<risk>", ...]
}
"""


def _martech_fallback(state: SharedState) -> Dict[str, Any]:
    """Deterministic martech baseline when LLM is unavailable."""
    expert_raw = state.get("prompt_expert_output", {})
    sub_agents: List[str] = []
    if expert_raw.get("needs_branding", True):
        sub_agents.append("branding")
    if expert_raw.get("needs_content", True):
        sub_agents.append("content")
    if expert_raw.get("needs_campaign", False):
        sub_agents.append("campaign")
    if expert_raw.get("needs_social_media", False):
        sub_agents.append("social_media")
    if not sub_agents:
        sub_agents = ["content"]

    return {
        "marketing_summary": "Standard digital marketing strategy covering core channels.",
        "primary_channels": ["email", "social_media", "content_marketing", "seo"],
        "target_audiences": [{"segment": "Primary", "characteristics": "Defined by objectives"}],
        "sub_agents_required": sub_agents,
        "sub_agent_tasks": {
            "branding": "Develop brand identity guidelines" if "branding" in sub_agents else None,
            "content": "Create content calendar and core assets"
            if "content" in sub_agents
            else None,
            "campaign": "Plan launch campaign" if "campaign" in sub_agents else None,
            "social_media": "Build social presence" if "social_media" in sub_agents else None,
        },
        "budget_recommendation_usd": state.get("total_budget", 0) * 0.20,
        "timeline_weeks": 8,
        "kpis": ["Brand awareness", "Lead generation", "Engagement rate"],
        "risks": ["LLM unavailable — full strategy requires LLM"],
    }


def martech_llm_strategy_node(state: SharedState) -> Dict[str, Any]:
    """
    Tier-2 Martech LLM node.

    Dispatched by CEO when requires_marketing is True.
    Internally decides which Tier-3 sub-agents to activate (branding, content,
    campaign, social_media) — the Martech subgraph graph reads
    result["sub_agents_required"] to route further execution.
    Returns only a marketing summary to CEO.
    """
    logger.info("\n📣 MARTECH: LLM STRATEGY PLANNING")

    expert_raw = state.get("prompt_expert_output", {})
    martech_prompt = (
        expert_raw.get("martech_task_prompt")
        or "Develop a comprehensive marketing strategy aligned with stated objectives."
    )

    company = state.get("company_name", "Unknown")
    industry = state.get("industry", "Unknown")
    objectives = state.get("strategic_objectives", [])
    budget = state.get("total_budget", 0)

    user_msg = (
        f"MARTECH TASK: {martech_prompt}\n\n"
        f"CONTEXT:\n"
        f"  Company:  {company}\n"
        f"  Industry: {industry}\n"
        f"  Budget:   ${budget:,.0f}\n\n"
        f"OBJECTIVES:\n"
        + "\n".join(f"  - {o}" for o in objectives)
        + "\n\nProduce the marketing strategy JSON."
    )

    llm = _get_llm(temperature=0.3, max_tokens=900)
    result = _call_structured(
        llm=llm,
        system_prompt=_MARTECH_SYSTEM_PROMPT,
        user_message=user_msg,
        fallback_fn=_martech_fallback,
        fallback_args=(state,),
    )

    sub_agents_required: List[str] = result.get("sub_agents_required", [])
    logger.info(f"  Channels:          {result.get('primary_channels', [])}")
    logger.info(f"  Sub-agents needed: {sub_agents_required}")
    logger.info(f"  Timeline:          {result.get('timeline_weeks', '?')} weeks")

    martech_summary_for_ceo = {
        "agent": "martech",
        "summary": {
            "status": "complete",
            "marketing_summary": result.get("marketing_summary"),
            "primary_channels": result.get("primary_channels"),
            "sub_agents_activated": sub_agents_required,
            "budget_recommendation_usd": result.get("budget_recommendation_usd"),
            "kpis": result.get("kpis"),
            "risks": result.get("risks"),
        },
        "timestamp": datetime.now().isoformat(),
    }

    return {
        "martech_llm_output": result,
        "martech_sub_agents": sub_agents_required,  # Read by Martech subgraph router
        "agent_outputs": [martech_summary_for_ceo],
    }


# =============================================================================
# TIER-2 LLM NODE: SECURITY & BLOCKCHAIN AUDIT
# =============================================================================

_SECURITY_SYSTEM_PROMPT = """You are the Security Agent node in a multi-agent LangGraph system.

You specialise in software security and, optionally, blockchain/smart-contract security.

RULES:
- You produce a SECURITY AUDIT SUMMARY — not working code or patches.
- You NEVER modify architecture or budget — you only flag risks.
- You MUST categorise findings by severity: critical, high, medium, low.
- You produce actionable remediation guidance (not generic advice).
- Output must be JSON matching the schema below.

OUTPUT SCHEMA:
{
  "audit_summary": "<2-3 sentence overview>",
  "scope": ["<area audited>", ...],
  "findings": [
    {
      "severity": "critical|high|medium|low",
      "area": "<area>",
      "title": "<short title>",
      "detail": "<description>",
      "remediation": "<specific fix guidance>"
    }
  ],
  "critical_count": <int>,
  "high_count": <int>,
  "overall_risk": "critical|high|medium|low",
  "proceed_recommendation": "proceed|proceed_after_fixes|halt",
  "blockchain_scope": true|false
}
"""


def _security_fallback(state: SharedState) -> Dict[str, Any]:
    """Deterministic security baseline when LLM is unavailable."""
    return {
        "audit_summary": "Standard security checklist applied. Full audit requires LLM availability.",
        "scope": [
            "authentication",
            "api_endpoints",
            "dependency_vulnerabilities",
            "secrets_management",
        ],
        "findings": [
            {
                "severity": "high",
                "area": "secrets_management",
                "title": "API keys in environment — verify not committed to VCS",
                "detail": "Ensure .env is in .gitignore and secrets are rotated regularly.",
                "remediation": "Audit git history; use a secrets manager (e.g., AWS Secrets Manager)",
            },
            {
                "severity": "medium",
                "area": "dependencies",
                "title": "Run dependency vulnerability scan",
                "detail": "CVE exposure unknown without LLM analysis.",
                "remediation": "Run `pip audit` or `safety check` and update flagged packages",
            },
        ],
        "critical_count": 0,
        "high_count": 1,
        "overall_risk": "medium",
        "proceed_recommendation": "proceed_after_fixes",
        "blockchain_scope": False,
    }


def security_llm_audit_node(state: SharedState) -> Dict[str, Any]:
    """
    Tier-2 Security LLM node.

    Dispatched by CEO when requires_security_audit is True.
    Leverages the existing SecurityBlockchainAgent knowledge profile.
    Returns only an audit summary to CEO — no raw code analysis.
    """
    logger.info("\n🔒 SECURITY: LLM AUDIT ANALYSIS")

    expert_raw = state.get("prompt_expert_output", {})
    security_prompt = (
        expert_raw.get("security_task_prompt")
        or "Perform a security audit covering software security and operational readiness."
    )

    company = state.get("company_name", "Unknown")
    industry = state.get("industry", "Unknown")
    objectives = state.get("strategic_objectives", [])

    # Pull SecurityBlockchainAgent best-practices as grounding context
    try:
        from agents.security_blockchain_agent import SecurityBlockchainAgent

        sec_agent = SecurityBlockchainAgent()
        best_practices = sec_agent.get_best_practices()
        practices_str = json.dumps(best_practices, indent=2)
    except Exception:
        practices_str = "(best practices unavailable)"

    user_msg = (
        f"SECURITY TASK: {security_prompt}\n\n"
        f"CONTEXT:\n"
        f"  Company:  {company}\n"
        f"  Industry: {industry}\n\n"
        f"OBJECTIVES:\n"
        + "\n".join(f"  - {o}" for o in objectives)
        + f"\n\nSECURITY BEST PRACTICES REFERENCE:\n{practices_str[:1200]}"
        + "\n\nProduce the security audit JSON."
    )

    llm = _get_llm(temperature=0.1, max_tokens=900)
    result = _call_structured(
        llm=llm,
        system_prompt=_SECURITY_SYSTEM_PROMPT,
        user_message=user_msg,
        fallback_fn=_security_fallback,
        fallback_args=(state,),
    )

    logger.info(f"  Overall risk:       {result.get('overall_risk', 'N/A')}")
    logger.info(f"  Critical findings:  {result.get('critical_count', 0)}")
    logger.info(f"  High findings:      {result.get('high_count', 0)}")
    logger.info(f"  Recommendation:     {result.get('proceed_recommendation', 'N/A')}")

    security_summary_for_ceo = {
        "agent": "security",
        "summary": {
            "status": "complete",
            "audit_summary": result.get("audit_summary"),
            "overall_risk": result.get("overall_risk"),
            "critical_count": result.get("critical_count", 0),
            "high_count": result.get("high_count", 0),
            "proceed_recommendation": result.get("proceed_recommendation"),
            "risks": [
                f["title"]
                for f in result.get("findings", [])
                if f.get("severity") in ("critical", "high")
            ],
        },
        "timestamp": datetime.now().isoformat(),
    }

    return {
        "security_llm_output": result,
        "agent_outputs": [security_summary_for_ceo],
        "risks": [
            {"source": "security", "severity": f["severity"], "title": f["title"]}
            for f in result.get("findings", [])
        ],
    }


# =============================================================================
# TIER-3 SUB-AGENT NODES  — Engineering cluster
# These run INSIDE the Engineer subgraph, never directly from CEO.
# =============================================================================

_UX_SYSTEM_PROMPT = """You are the UX/UI Design Agent node (Tier-3, within Engineer subgraph).
Apply: Nielsen's 10 heuristics, WCAG 2.1 AAA accessibility, Material Design 3.

Output JSON:
{
  "design_summary": "<2-3 sentence overview>",
  "design_system": "<chosen system: Material / Fluent / custom>",
  "accessibility_score": <0-100>,
  "key_components": ["<component>", ...],
  "color_palette_recommendation": "<brief>",
  "typography_recommendation": "<brief>",
  "user_flow_issues": ["<issue>", ...],
  "deliverables": ["<deliverable>", ...]
}
"""


def ux_design_llm_node(state: SharedState) -> Dict[str, Any]:
    """
    Tier-3: UX/UI design within the Engineer subgraph.
    Activated when martech_sub_agents or engineer needs design.
    """
    logger.info("  🎨 UX/UI DESIGN: LLM spec generation")
    expert_raw = state.get("prompt_expert_output", {})
    prompt = (
        expert_raw.get("engineer_task_prompt")
        or "Design a user-centred UI for the stated product objectives."
    )
    objectives = state.get("strategic_objectives", [])
    user_msg = f"UX TASK: {prompt}\n\nOBJECTIVES: {'; '.join(objectives)}"

    llm = _get_llm(temperature=0.3, max_tokens=600)
    result = _call_structured(
        llm=llm,
        system_prompt=_UX_SYSTEM_PROMPT,
        user_message=user_msg,
        fallback_fn=lambda: {
            "design_summary": "Standard UX specification (fallback).",
            "design_system": "Material Design 3",
            "accessibility_score": 70,
            "key_components": ["Navigation", "Forms", "Dashboard", "Notifications"],
            "color_palette_recommendation": "Follow brand guidelines",
            "typography_recommendation": "Inter / Roboto — system fonts",
            "user_flow_issues": [],
            "deliverables": ["Wireframes", "Component library", "Accessibility report"],
        },
    )
    return {"ux_design_output": result}


_WEBDEV_SYSTEM_PROMPT = """You are the Web Development Agent node (Tier-3, within Engineer subgraph).

Produce a web development implementation plan. Output JSON:
{
  "implementation_summary": "<2-3 sentences>",
  "stack": {"frontend": "<tech>", "backend": "<tech>", "database": "<tech>", "hosting": "<tech>"},
  "phases": [{"phase": "<name>", "duration_weeks": <int>, "deliverables": ["<item>"]}],
  "ar_features": ["<ar feature if applicable>"],
  "estimated_weeks": <int>,
  "testing_strategy": "<brief>"
}
"""


def webdev_llm_node(state: SharedState) -> Dict[str, Any]:
    """Tier-3: Web development plan within the Engineer subgraph."""
    logger.info("  💻 WEBDEV: LLM implementation plan")
    expert_raw = state.get("prompt_expert_output", {})
    prompt = (
        expert_raw.get("engineer_task_prompt")
        or "Build a web application for the stated objectives."
    )
    objectives = state.get("strategic_objectives", [])
    user_msg = f"WEBDEV TASK: {prompt}\n\nOBJECTIVES: {'; '.join(objectives)}"

    llm = _get_llm(temperature=0.2, max_tokens=700)
    result = _call_structured(
        llm=llm,
        system_prompt=_WEBDEV_SYSTEM_PROMPT,
        user_message=user_msg,
        fallback_fn=lambda: {
            "implementation_summary": "Standard web implementation plan (fallback).",
            "stack": {
                "frontend": "React",
                "backend": "FastAPI",
                "database": "PostgreSQL",
                "hosting": "AWS",
            },
            "phases": [
                {
                    "phase": "Foundation",
                    "duration_weeks": 4,
                    "deliverables": ["Auth", "DB schema", "API skeleton"],
                },
                {"phase": "Core features", "duration_weeks": 8, "deliverables": ["Feature builds"]},
                {"phase": "QA & launch", "duration_weeks": 2, "deliverables": ["Tests", "Deploy"]},
            ],
            "ar_features": [],
            "estimated_weeks": 14,
            "testing_strategy": "Unit + integration + e2e tests (pytest, Playwright)",
        },
    )
    return {"webdev_output": result}


_SOFTWARE_ENG_SYSTEM_PROMPT = """You are the Software Engineering Agent node (Tier-3, within Engineer subgraph).
Specialise in code architecture review and quality improvement.

Output JSON:
{
  "architecture_review": "<2-3 sentence summary>",
  "patterns_recommended": ["<pattern>", ...],
  "critical_issues": [{"issue": "<desc>", "file_hint": "<hint>", "fix": "<fix>"}],
  "complexity_score": <1-10>,
  "maintainability_score": <1-10>,
  "top_recommendations": ["<rec>", ...]
}
"""


def software_eng_llm_node(state: SharedState) -> Dict[str, Any]:
    """Tier-3: Software engineering review within the Engineer subgraph."""
    logger.info("  🔧 SOFT-ENG: LLM architecture review")
    expert_raw = state.get("prompt_expert_output", {})
    prompt = (
        expert_raw.get("engineer_task_prompt")
        or "Review software architecture for the stated system."
    )
    objectives = state.get("strategic_objectives", [])
    user_msg = f"SW-ENG TASK: {prompt}\n\nOBJECTIVES: {'; '.join(objectives)}"

    llm = _get_llm(temperature=0.2, max_tokens=600)
    result = _call_structured(
        llm=llm,
        system_prompt=_SOFTWARE_ENG_SYSTEM_PROMPT,
        user_message=user_msg,
        fallback_fn=lambda: {
            "architecture_review": "Standard software architecture review (fallback).",
            "patterns_recommended": ["dependency_injection", "repository", "factory"],
            "critical_issues": [],
            "complexity_score": 5,
            "maintainability_score": 6,
            "top_recommendations": [
                "Add type annotations throughout",
                "Separate business logic from I/O",
                "Add comprehensive test coverage",
            ],
        },
    )
    return {"software_eng_output": result}


# =============================================================================
# TIER-3 SUB-AGENT NODES  — Martech cluster
# These run INSIDE the Martech subgraph, never directly from CEO.
# =============================================================================

_BRANDING_SYSTEM_PROMPT = """You are the Branding Agent — a senior brand strategist and creative director with expertise
in visual identity, RISD design principles, and Nielsen Norman UX methodology.

Your role is to create complete, actionable brand identities tailored to the specific company,
industry, location, and strategic objectives provided. Be specific — no generic advice.

Think through the brand architecture holistically:
- Market positioning relative to industry competitors
- Target audience psychographics and expectations
- Visual identity that communicates the brand promise
- Voice and tone that resonates with the target market
- Practical deliverables the team can execute immediately

Output valid JSON exactly matching this schema:
{
  "brand_summary": "<3-4 sentences: company positioning, what makes this brand distinctive, and the emotional promise to customers>",
  "brand_positioning": "<one sharp positioning statement: '[Company] is the only [category] that [differentiator] for [audience]'>",
  "brand_voice": {
    "adjectives": ["<adj1>", "<adj2>", "<adj3>", "<adj4>"],
    "tone": "<how it sounds in writing>",
    "avoid": "<what to never say or sound like>"
  },
  "color_palette": {
    "primary": "<hex>",
    "secondary": "<hex>",
    "accent": "<hex>",
    "neutral": "<hex>",
    "rationale": "<why these colors fit this industry and audience>"
  },
  "typography": {
    "heading": "<font name>",
    "body": "<font name>",
    "accent": "<font name or none>",
    "rationale": "<why this type system fits>"
  },
  "logo_concept": {
    "style": "<wordmark | lettermark | combination | emblem>",
    "description": "<detailed concept: shape, symbolism, layout>",
    "icon_motif": "<visual metaphor or symbol used, if any>"
  },
  "brand_kit_reference": {
    "primary_color": "<hex>",
    "secondary_color": "<hex>",
    "accent_color": "<hex>",
    "font_heading": "<font>",
    "font_body": "<font>",
    "logo_style": "<style>",
    "industry_palette_rationale": "<one sentence>"
  },
  "design_concepts": [
    {
      "name": "<concept name>",
      "description": "<what this concept communicates>",
      "color_application": "<how colors are applied>",
      "use_case": "<where this concept is used: digital, print, signage, etc.>"
    }
  ],
  "strategic_alignment": "<how this brand identity supports the company's stated strategic objectives>",
  "deliverables": [
    "<deliverable 1>",
    "<deliverable 2>",
    "<deliverable 3>",
    "<deliverable 4>",
    "<deliverable 5>"
  ],
  "implementation_priorities": [
    {"priority": 1, "item": "<most urgent deliverable>", "timeline": "<timeframe>"},
    {"priority": 2, "item": "<second most urgent>", "timeline": "<timeframe>"},
    {"priority": 3, "item": "<third>", "timeline": "<timeframe>"}
  ]
}
"""


def branding_llm_node(state: SharedState) -> Dict[str, Any]:
    """Tier-3: Brand identity within the Martech subgraph."""
    logger.info("  \U0001f3a8 BRANDING: LLM identity design")
    expert_raw = state.get("prompt_expert_output", {})
    prompt = (
        expert_raw.get("martech_task_prompt")
        or "Develop a complete brand identity for this company."
    )
    company = state.get("company_name", "the company")
    industry = state.get("industry", "general business")
    location = state.get("location", "")
    objectives = state.get("strategic_objectives", [])

    objectives_text = (
        "\n".join(f"  - {obj}" for obj in objectives)
        if objectives
        else "  - (no objectives specified)"
    )

    user_msg = (
        f"BRANDING TASK: {prompt}\n\n"
        f"Company: {company}\n"
        f"Industry: {industry}\n"
        f"Location: {location}\n"
        f"Strategic Objectives:\n{objectives_text}\n\n"
        f"Create a brand identity that is specific to this company, industry, and market context. "
        f"Every recommendation must tie directly to the company's objectives and target audience."
    )

    llm = _get_llm(temperature=0.5, max_tokens=1200)
    result = _call_structured(
        llm=llm,
        system_prompt=_BRANDING_SYSTEM_PROMPT,
        user_message=user_msg,
        fallback_fn=lambda: {
            "brand_summary": f"Professional brand identity for {company} in the {industry} market.",
            "brand_positioning": f"{company} is the trusted {industry} partner for quality and results.",
            "brand_voice": {
                "adjectives": ["Professional", "Trustworthy", "Innovative", "Approachable"],
                "tone": "Confident and clear, never condescending",
                "avoid": "Jargon, passive voice, generic corporate-speak",
            },
            "color_palette": {
                "primary": "#1E3A5F",
                "secondary": "#2563EB",
                "accent": "#F59E0B",
                "neutral": "#F8FAFC",
                "rationale": "Deep navy conveys authority; blue trust; amber energy and optimism.",
            },
            "typography": {
                "heading": "Inter",
                "body": "Inter",
                "accent": "none",
                "rationale": "Clean and modern; highly legible across digital and print.",
            },
            "logo_concept": {
                "style": "combination",
                "description": "Wordmark with a clean geometric icon representing the industry",
                "icon_motif": "Abstract form referencing the core business activity",
            },
            "brand_kit_reference": {
                "primary_color": "#1E3A5F",
                "secondary_color": "#2563EB",
                "accent_color": "#F59E0B",
                "font_heading": "Inter",
                "font_body": "Inter",
                "logo_style": "combination",
                "industry_palette_rationale": "Professional palette suited for the industry and target audience.",
            },
            "design_concepts": [
                {
                    "name": "Primary Identity",
                    "description": "Core brand expression for all primary touchpoints",
                    "color_application": "Navy background, white type, amber accents",
                    "use_case": "Website, pitch decks, business cards",
                },
                {
                    "name": "Digital Variant",
                    "description": "Optimized for screens and social media",
                    "color_application": "White background, navy type, blue highlights",
                    "use_case": "Social profiles, email headers, app icons",
                },
            ],
            "strategic_alignment": "Brand identity built to support growth objectives and market positioning.",
            "deliverables": [
                "Logo files (SVG, PNG, PDF — light and dark variants)",
                "Brand guidelines document (colors, type, usage rules)",
                "Business card template",
                "Social media profile kit (cover + avatar sizes)",
                "Email signature template",
            ],
            "implementation_priorities": [
                {"priority": 1, "item": "Logo and brand guidelines", "timeline": "Week 1-2"},
                {
                    "priority": 2,
                    "item": "Digital presence (website + social)",
                    "timeline": "Week 2-4",
                },
                {
                    "priority": 3,
                    "item": "Print collateral (cards, signage)",
                    "timeline": "Week 4-6",
                },
            ],
        },
    )
    return {"branding_output": result}


_CONTENT_SYSTEM_PROMPT = """You are the Content Strategy Agent node (Tier-3, within Martech subgraph).

Output JSON:
{
  "content_strategy_summary": "<2-3 sentences>",
  "content_pillars": ["<pillar>", ...],
  "content_calendar": [{"week": <int>, "type": "<type>", "topic": "<topic>", "channel": "<channel>"}],
  "seo_focus_keywords": ["<keyword>", ...],
  "distribution_channels": ["<channel>", ...],
  "estimated_pieces_per_month": <int>
}
"""


def content_llm_node(state: SharedState) -> Dict[str, Any]:
    """Tier-3: Content strategy within the Martech subgraph."""
    logger.info("  📝 CONTENT: LLM content strategy")
    expert_raw = state.get("prompt_expert_output", {})
    prompt = expert_raw.get("martech_task_prompt") or "Build a content marketing strategy."
    company = state.get("company_name", "Unknown")
    objectives = state.get("strategic_objectives", [])
    user_msg = f"CONTENT TASK: {prompt}\n\nCompany: {company}\nObjectives: {'; '.join(objectives)}"

    llm = _get_llm(temperature=0.3, max_tokens=700)
    result = _call_structured(
        llm=llm,
        system_prompt=_CONTENT_SYSTEM_PROMPT,
        user_message=user_msg,
        fallback_fn=lambda: {
            "content_strategy_summary": "SEO-first content strategy across owned channels (fallback).",
            "content_pillars": [
                "Education",
                "Industry insights",
                "Case studies",
                "Product updates",
            ],
            "content_calendar": [
                {"week": 1, "type": "blog", "topic": "Industry overview", "channel": "website"},
                {"week": 2, "type": "social", "topic": "Thought leadership", "channel": "linkedin"},
            ],
            "seo_focus_keywords": ["[to be defined]"],
            "distribution_channels": ["blog", "linkedin", "email_newsletter"],
            "estimated_pieces_per_month": 8,
        },
    )
    return {"content_output": result}


_CAMPAIGN_SYSTEM_PROMPT = """You are the Campaign Agent node (Tier-3, within Martech subgraph).

Output JSON:
{
  "campaign_summary": "<2-3 sentences>",
  "campaign_objectives": ["<objective>", ...],
  "target_audiences": [{"segment": "<name>", "size_estimate": "<size>"}],
  "channels": ["<channel>", ...],
  "budget_split_pct": {"<channel>": <pct>},
  "creative_concepts": ["<concept>", ...],
  "projected_reach": <int>,
  "projected_conversions": <int>
}
"""


def campaign_llm_node(state: SharedState) -> Dict[str, Any]:
    """Tier-3: Campaign plan within the Martech subgraph."""
    logger.info("  🚀 CAMPAIGN: LLM launch plan")
    expert_raw = state.get("prompt_expert_output", {})
    prompt = expert_raw.get("martech_task_prompt") or "Plan a go-to-market campaign."
    company = state.get("company_name", "Unknown")
    budget = state.get("total_budget", 0)
    objectives = state.get("strategic_objectives", [])
    user_msg = (
        f"CAMPAIGN TASK: {prompt}\n\nCompany: {company}\n"
        f"Available budget: ${budget:,.0f}\nObjectives: {'; '.join(objectives)}"
    )

    llm = _get_llm(temperature=0.3, max_tokens=700)
    result = _call_structured(
        llm=llm,
        system_prompt=_CAMPAIGN_SYSTEM_PROMPT,
        user_message=user_msg,
        fallback_fn=lambda: {
            "campaign_summary": "Integrated digital launch campaign (fallback).",
            "campaign_objectives": ["Awareness", "Lead generation"],
            "target_audiences": [{"segment": "Primary", "size_estimate": "TBD"}],
            "channels": ["google_ads", "linkedin_ads", "email"],
            "budget_split_pct": {"google_ads": 50, "linkedin_ads": 30, "email": 20},
            "creative_concepts": ["Product demo video", "Case study series"],
            "projected_reach": 50000,
            "projected_conversions": 500,
        },
    )
    return {"campaign_output": result}


_SOCIAL_MEDIA_SYSTEM_PROMPT = """You are the Social Media Agent node (Tier-3, within Martech subgraph).

Output JSON:
{
  "social_summary": "<2-3 sentences>",
  "platforms": ["<platform>", ...],
  "posting_frequency": {"<platform>": "<frequency>"},
  "content_themes": ["<theme>", ...],
  "community_playbook": "<brief community management approach>",
  "growth_tactics": ["<tactic>", ...],
  "kpis": ["<kpi>", ...]
}
"""


def social_media_llm_node(state: SharedState) -> Dict[str, Any]:
    """Tier-3: Social media plan within the Martech subgraph."""
    logger.info("  📱 SOCIAL MEDIA: LLM growth plan")
    expert_raw = state.get("prompt_expert_output", {})
    prompt = expert_raw.get("martech_task_prompt") or "Build a social media growth strategy."
    company = state.get("company_name", "Unknown")
    industry = state.get("industry", "Unknown")
    user_msg = f"SOCIAL TASK: {prompt}\n\nCompany: {company}\nIndustry: {industry}"

    llm = _get_llm(temperature=0.3, max_tokens=600)
    result = _call_structured(
        llm=llm,
        system_prompt=_SOCIAL_MEDIA_SYSTEM_PROMPT,
        user_message=user_msg,
        fallback_fn=lambda: {
            "social_summary": "Organic social growth strategy across primary platforms (fallback).",
            "platforms": ["linkedin", "twitter", "instagram"],
            "posting_frequency": {
                "linkedin": "3x/week",
                "twitter": "daily",
                "instagram": "4x/week",
            },
            "content_themes": ["Thought leadership", "Behind-the-scenes", "Product highlights"],
            "community_playbook": "Respond to comments within 24h; engage in industry conversations",
            "growth_tactics": [
                "Hashtag strategy",
                "Industry influencer engagement",
                "Employee advocacy",
            ],
            "kpis": ["Follower growth", "Engagement rate", "Profile visits", "Link clicks"],
        },
    )
    return {"social_media_output": result}


# =============================================================================
# TIER-2 AGENT NODE REGISTRY
# Convenience map used by main_graph route_dispatch and subgraph builders.
# =============================================================================

TIER1_NODE_MAP: Dict[str, Any] = {
    "ceo": ceo_llm_analyze_node,
    "cto": cto_llm_architecture_node,
}

TIER2_NODE_MAP: Dict[str, Any] = {
    "cfo": cfo_llm_summarize_node,
    "engineer": engineer_llm_architect_node,
    "researcher": researcher_llm_synthesize_node,
    "legal": legal_llm_compliance_node,
    "martech": martech_llm_strategy_node,
    "security": security_llm_audit_node,
}

TIER3_NODE_MAP: Dict[str, Any] = {
    # Engineering cluster
    "ux_design": ux_design_llm_node,
    "webdev": webdev_llm_node,
    "software_eng": software_eng_llm_node,
    # Martech cluster
    "branding": branding_llm_node,
    "content": content_llm_node,
    "campaign": campaign_llm_node,
    "social_media": social_media_llm_node,
}
