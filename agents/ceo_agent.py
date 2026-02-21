"""
[DEPRECATED — v0.3]
CEO (Chief Executive Officer) Agent - Executive Orchestrator

The class-based CEOAgent has been superseded by the LangGraph node
ceo_llm_analyze_node in graph_architecture/llm_nodes.py and the full
orchestration graph in graph_architecture/main_graph.py.

This file is RETAINED for backward compatibility with app.py's
  from agents.ceo_agent import CEOAgentState, analyze_strategic_objectives
Do NOT add new CEO logic here — use graph_architecture/main_graph.py instead.
3. Multi-agent orchestration and delegation
4. Risk assessment and mitigation authority
5. Final approval for all financial commitments

UPGRADED FROM: CFO Agent (which focused on financial planning)
NOW: CEO handles executive strategy, CFO handles financial oversight

Governance Model:
- CEO makes strategic decisions autonomously within guard rails
- CEO delegates operational tasks to specialized agents
- CEO requires user approval for financial commitments >$0
- CEO works with CFO for budget oversight and financial compliance
"""

from langgraph.graph import START, END, StateGraph
from typing_extensions import TypedDict
from typing import Annotated, Dict, List, Any, Optional
import operator
from dataclasses import dataclass, field
from datetime import datetime
from agents.specialized_agents import AgentFactory
from agents.agent_knowledge_base import get_expertise, get_all_expertise_areas


# ============================================================================
# CEO AGENT STATE
# ============================================================================


class CEOAgentState(TypedDict):
    """State for the CEO (Chief Executive Officer) - Executive Orchestrator"""

    # Strategic Input
    company_name: str
    industry: str
    location: str
    strategic_objectives: Annotated[list[str], operator.add]
    business_goals: Annotated[list[Dict], operator.add]

    # Executive Authority & Decision Making
    executive_decisions: Annotated[list[Dict], operator.add]  # Strategic decisions made
    pending_approvals: Annotated[list[Dict], operator.add]  # Awaiting user approval
    approved_actions: Annotated[list[str], operator.add]  # User-approved actions
    rejected_actions: Annotated[list[str], operator.add]  # User-rejected actions

    # Budget & Resource Management (Works with CFO)
    total_budget: float
    budget_allocated: Dict[str, float]
    budget_reserved_for_fees: float  # API and legal filing fees only
    pending_payments: Annotated[list[Dict], operator.add]  # Awaiting payment approval

    # Timeline Management
    target_completion_days: int
    current_day: int
    milestones: Annotated[list[Dict], operator.add]

    # Multi-Agent Orchestration
    active_agents: Annotated[list[str], operator.add]
    agent_outputs: Annotated[list[Dict], operator.add]
    agent_status: Dict[str, str]
    delegated_tasks: Dict[str, List[str]]

    # Task Breakdown & Assignment
    identified_tasks: Annotated[list[Dict], operator.add]
    assigned_tasks: Dict[str, List[str]]
    completed_tasks: Annotated[list[str], operator.add]
    blocked_tasks: Annotated[list[Dict], operator.add]  # Tasks blocked pending approval

    # Risk & Opportunity Management (CEO Core Responsibility)
    risks: Annotated[list[Dict], operator.add]
    risk_mitigation_plans: Dict[str, str]
    opportunities: Annotated[list[str], operator.add]
    opportunity_analysis: Annotated[list[Dict], operator.add]

    # Compliance & Governance
    guard_rail_violations: Annotated[list[Dict], operator.add]
    liability_warnings: Annotated[list[str], operator.add]
    compliance_status: Dict[str, bool]

    # Deliverables & Reporting
    deliverables: Annotated[list[str], operator.add]
    status_reports: Annotated[list[str], operator.add]
    final_executive_summary: str

    # CEO strategic output (set, not appended)
    recommendations: list
    discovery_questions: list

    # Workflow Control
    current_phase: str
    completed_phases: Annotated[list[str], operator.add]


# ============================================================================
# CEO AGENT - STRATEGIC ANALYSIS & EXECUTIVE PLANNING
# ============================================================================


def analyze_strategic_objectives(state: CEOAgentState) -> dict:
    """
    CEO analyzes strategic objectives and makes executive decisions

    Applies frameworks from:
    - Harvard Business School: Strategic Leadership
    - Stanford GSB: Executive Decision Making
    - MIT Sloan: Strategic Management
    - McKinsey: Strategic Problem Solving (MECE Framework)
    """
    print("\n" + "=" * 80)
    print("👔 CEO AGENT - EXECUTIVE STRATEGIC ANALYSIS")
    print("=" * 80)

    print(f"\nCompany: {state['company_name']}")
    print(f"Industry: {state['industry']}")
    print(f"Location: {state['location']}")
    print(f"Total Budget: ${state.get('total_budget', 100000):,.0f}")
    print(f"Timeline: {state.get('target_completion_days', 90)} days")

    print("\n📋 STRATEGIC OBJECTIVES:")
    objectives = state.get("strategic_objectives", [])
    for i, obj in enumerate(objectives, 1):
        print(f"  {i}. {obj}")

    # Executive Decision: Task Decomposition
    print("\n\n🎯 EXECUTIVE DECISION - TASK DECOMPOSITION:")
    print("-" * 80)

    # ── Contextual task templates ────────────────────────────────────────────
    industry = state.get("industry", "Business").strip()
    company = state.get("company_name", "the company")
    total_bud = float(state.get("total_budget", 5000) or 5000)
    objectives_text = " ".join(str(o) for o in objectives).lower()

    # Scale budgets proportionally so they fit inside the declared budget
    def scaled(pct: float, min_val: float = 50, max_val: float = None) -> float:
        val = round(total_bud * pct, -1)  # round to nearest $10
        if max_val:
            val = min(val, max_val)
        return max(val, min_val)

    # Detect vertical so we can tune descriptions
    is_entertainment = any(
        w in industry.lower() for w in ("entertain", "event", "music", "concert", "venue")
    )
    is_food = any(w in industry.lower() for w in ("food", "restaurant", "beverage", "cafe"))
    is_retail = any(w in industry.lower() for w in ("retail", "shop", "store", "ecommerce"))
    is_tech = any(w in industry.lower() for w in ("tech", "software", "saas", "app"))

    # T003 — digital presence: generic, no AR unless explicitly requested
    if is_entertainment:
        t003_name = "Digital Presence & Event Ticketing Platform"
        t003_desc = f"Build website, event calendar, and ticketing integration for {company}"
    elif is_food:
        t003_name = "Digital Presence — Website & Online Ordering"
        t003_desc = (
            f"Build website with menu, online ordering, and reservation system for {company}"
        )
    elif is_retail:
        t003_name = "Digital Presence — E-Commerce & SEO"
        t003_desc = (
            f"Build e-commerce website with payment processing and search visibility for {company}"
        )
    elif is_tech:
        t003_name = "Product Website & Developer Documentation"
        t003_desc = f"Build marketing site, product docs, and onboarding flow for {company}"
    else:
        t003_name = "Digital Presence — Website & Online Visibility"
        t003_desc = f"Build website, SEO foundation, and digital discovery channels for {company}"

    # T004 — martech
    if is_entertainment:
        t004_desc = (
            "Ticketing analytics, email marketing, audience CRM, and social scheduling tools"
        )
    elif is_tech:
        t004_desc = "Product analytics, customer success tooling, and growth experimentation stack"
    else:
        t004_desc = "CRM, email marketing, analytics, and marketing automation setup"

    # T005 — content
    if is_entertainment:
        t005_desc = (
            "Event announcements, artist profiles, press releases, and social content calendar"
        )
    else:
        t005_desc = "Create marketing content, photography plan, videos, and editorial calendar"

    # T006 — campaigns
    if is_entertainment:
        t006_desc = "Multi-channel campaign: paid social, email blasts, influencer outreach, and pre-sale promotions"
        t006_payment = "advertising_spend"
    else:
        t006_desc = "Multi-channel marketing campaign execution across paid and organic channels"
        t006_payment = "advertising_spend"

    identified_tasks = [
        {
            "task_id": "T001",
            "task_name": "Legal Foundation & Compliance",
            "description": f"Establish legal entity, DBA registration, business licenses, and trademark protection for {company}",
            "required_expertise": "legal",
            "priority": "CRITICAL",
            "executive_rationale": "Legal foundation protects the company from liability and establishes a legitimate market presence",
            "dependencies": [],
            "estimated_budget": scaled(0.10, 200, 800),
            "requires_payment": True,
            "payment_type": "government_filing_fees",
            "estimated_days": 21,
            "risk_level": "HIGH",
            "success_criteria": [
                "Legal entity registered",
                "DBA or trademark filed",
                "Business licenses obtained",
            ],
        },
        {
            "task_id": "T002",
            "task_name": "Brand Identity Development",
            # ── FIRST deliverable: starts in parallel with Legal ──
            "description": f"Design logo, visual system, brand voice, and complete brand guidelines for {company}",
            "required_expertise": "branding",
            "priority": "CRITICAL",
            "executive_rationale": "A strong brand identity is the foundation of customer perception and drives every downstream creative asset",
            "dependencies": [],  # Runs in parallel with T001 — no blocking dependency
            "estimated_budget": scaled(0.06, 80, 300),
            "requires_payment": False,
            "estimated_days": 14,
            "risk_level": "MEDIUM",
            "success_criteria": [
                "Logo designed following golden ratio principles",
                "Full brand guidelines documented (colors, fonts, tone)",
                "Brand asset pack created (print, digital, social formats)",
            ],
        },
        {
            "task_id": "T003",
            "task_name": t003_name,
            "description": t003_desc,
            "required_expertise": "web_development",
            "priority": "HIGH",
            "executive_rationale": "Digital presence is the primary discovery channel for new customers; critical for revenue generation",
            "dependencies": ["T002"],
            "estimated_budget": scaled(0.20, 300, 5000),
            "requires_payment": True,
            "payment_type": "service_subscription",
            "estimated_days": 45,
            "risk_level": "MEDIUM",
            "success_criteria": [
                "Website live and functional",
                "Mobile-responsive and fast-loading",
                "SEO metadata and sitemap submitted",
            ],
        },
        {
            "task_id": "T004",
            "task_name": "Marketing Technology Stack",
            "description": t004_desc,
            "required_expertise": "martech",
            "priority": "MEDIUM",
            "executive_rationale": "Data-driven marketing maximizes ROI and provides actionable insights on customer journey",
            "dependencies": ["T003"],
            "estimated_budget": scaled(0.05, 50, 400),
            "requires_payment": True,
            "payment_type": "software_subscription",
            "estimated_days": 14,
            "risk_level": "LOW",
            "success_criteria": [
                "CRM configured with lead pipeline",
                "Analytics tracking live",
                "Marketing automation sequences active",
            ],
        },
        {
            "task_id": "T005",
            "task_name": "Content Strategy & Production",
            "description": t005_desc,
            "required_expertise": "content",
            "priority": "MEDIUM",
            "executive_rationale": "Quality content educates customers, builds authority, and supports organic discovery",
            "dependencies": ["T002"],
            "estimated_budget": scaled(0.05, 50, 300),
            "requires_payment": False,
            "estimated_days": 30,
            "risk_level": "LOW",
            "success_criteria": [
                "60-day content calendar created",
                "Initial content assets produced",
                "SEO keyword strategy documented",
            ],
        },
        {
            "task_id": "T006",
            "task_name": "Campaign Launch & Execution",
            "description": t006_desc,
            "required_expertise": "campaigns",
            "priority": "HIGH",
            "executive_rationale": "Strategic campaigns drive customer acquisition, brand awareness, and initial revenue",
            "dependencies": ["T004", "T005"],
            "estimated_budget": scaled(0.30, 200, None),
            "requires_payment": True,
            "payment_type": t006_payment,
            "estimated_days": 60,
            "risk_level": "MEDIUM",
            "success_criteria": [
                "Campaign live across priority channels",
                "Lead generation or ticket sales initiated",
                "Performance tracking dashboard operational",
            ],
        },
    ]

    # CEO reviews each task for risk and approval requirements
    print("\n📊 TASK ANALYSIS:")
    total_budget_required = 0
    payment_required_tasks = []

    for task in identified_tasks:
        total_budget_required += task["estimated_budget"]

        print(f"\n  {task['task_id']}: {task['task_name']}")
        print(f"    Priority: {task['priority']} | Risk: {task['risk_level']}")
        print(f"    Budget: ${task['estimated_budget']:,.0f}")

        if task.get("requires_payment"):
            print(f"    ⚠️  PAYMENT REQUIRED: {task['payment_type']}")
            print(f"    🔒 Will require user approval before proceeding")
            payment_required_tasks.append(task["task_id"])

            # Add to pending approvals
            state["pending_approvals"].append(
                {
                    "approval_id": f"PAY_{task['task_id']}",
                    "task_id": task["task_id"],
                    "task_name": task["task_name"],
                    "amount": task["estimated_budget"],
                    "payment_type": task["payment_type"],
                    "rationale": task["executive_rationale"],
                    "status": "pending_user_approval",
                    "created_at": datetime.now().isoformat(),
                }
            )

    # CEO makes budget allocation decision
    print(f"\n\n💼 EXECUTIVE BUDGET DECISION:")
    print(f"  Total Required: ${total_budget_required:,.0f}")
    print(f"  Available Budget: ${state.get('total_budget', 0):,.0f}")
    print(f"  Tasks Requiring Payment Approval: {len(payment_required_tasks)}")

    if total_budget_required > state.get("total_budget", 0):
        print(
            f"  ⚠️  WARNING: Budget shortfall of ${total_budget_required - state.get('total_budget', 0):,.0f}"
        )
        print(
            f"  🎯 CEO Decision: Prioritize critical tasks, seek additional funding or scope reduction"
        )

    # Update state with CEO decisions
    state["identified_tasks"].extend(identified_tasks)

    state["executive_decisions"].append(
        {
            "decision_id": "DEC_001",
            "decision": "Strategic task breakdown approved",
            "rationale": "Tasks align with business objectives and market requirements",
            "tasks_count": len(identified_tasks),
            "budget_impact": total_budget_required,
            "timestamp": datetime.now().isoformat(),
        }
    )

    # Calculate CFO oversight budget (API fees only)
    api_budget = sum(
        t["estimated_budget"] for t in identified_tasks if not t.get("requires_payment")
    )
    service_budget = sum(
        t["estimated_budget"] for t in identified_tasks if t.get("requires_payment")
    )

    state["budget_allocated"] = {
        "api_and_tools": api_budget,  # Managed by CFO
        "services_and_payments": service_budget,  # Requires user approval
    }

    state["budget_reserved_for_fees"] = api_budget

    # ── Strategic Recommendations ────────────────────────────────────────────
    budget_shortfall = total_budget_required > total_bud
    recommendations = [
        (
            f"Run Legal (T001) and Brand Identity (T002) in parallel from Day 1 to compress "
            f"the critical path by up to {identified_tasks[1].get('estimated_days', 14)} days."
        ),
        (
            f"With a ${total_bud:,.0f} budget, prioritize owned-media channels "
            f"(SEO, email, social) before paid advertising to extend runway and build compounding assets."
        ),
        (
            "Establish clear success KPIs for each domain before deploying agents so ROI is "
            "measurable from day 1 \u2014 track CAC, conversion rate, and brand recall."
        ),
        (
            "Build a reusable content library in the first 30 days; assets created for the website "
            "and brand kit should be repurposed across all marketing channels."
        ),
        (
            f"Phase your technology investment: launch an MVP in 45 days, then iterate based on "
            f"real customer feedback before committing to larger platform features."
        ),
    ]
    if budget_shortfall:
        recommendations.insert(
            0,
            f"\u26a0\ufe0f Budget alert: estimated task cost exceeds your declared budget by "
            f"${total_budget_required - total_bud:,.0f}. "
            "Consider deferring payment-gated tasks to Phase 2 or securing additional capital before launch.",
        )

    # ── CEO Discovery Questions (financial & operational state) ──────────────
    discovery_questions = [
        {
            "category": "Financial",
            "icon": "\ud83d\udcb0",
            "question": "What is your current monthly revenue, or are you pre-revenue? "
            "This determines how aggressively we can invest in growth vs. foundation.",
        },
        {
            "category": "Financial",
            "icon": "\ud83c\udfe6",
            "question": "Beyond the stated project budget, what is your total operating runway "
            "(months of capital)? This shapes our risk tolerance and phasing decisions.",
        },
        {
            "category": "Operational",
            "icon": "\ud83d\udc65",
            "question": "Do you have existing staff, co-founders, or contractors we should factor "
            "into task delegation, or will agents handle all execution?",
        },
        {
            "category": "Operational",
            "icon": "\ud83e\udd1d",
            "question": "Are there existing vendor relationships, contracts, or partnerships "
            "already in place that agents should be aware of before outreach?",
        },
        {
            "category": "Market",
            "icon": "\ud83c\udfaf",
            "question": "Do you have paying customers or signed LOIs today? "
            "Existing demand changes our prioritization \u2014 retention before acquisition.",
        },
    ]

    state["recommendations"] = recommendations
    state["discovery_questions"] = discovery_questions

    print(f"\n\n\u2705 CEO STRATEGIC ANALYSIS COMPLETE")
    print(f"  Tasks Identified: {len(identified_tasks)}")
    print(f"  Pending User Approvals: {len(state['pending_approvals'])}")
    print(f"  CFO Budget (API/Tools): ${api_budget:,.0f}")
    print(f"  Requires User Approval: ${service_budget:,.0f}")
    print(f"  Recommendations: {len(recommendations)}")
    print(f"  Discovery Questions: {len(discovery_questions)}")

    return state


def deploy_specialized_agents(state: CEOAgentState) -> dict:
    """
    CEO delegates tasks to specialized agents

    Only deploys agents for approved tasks or tasks not requiring payment
    """
    print("\n" + "=" * 80)
    print("👔 CEO - AGENT DEPLOYMENT & DELEGATION")
    print("=" * 80)

    # Identify which tasks can proceed without approval
    approved_task_ids = []
    blocked_task_ids = []

    for task in state["identified_tasks"]:
        if not task.get("requires_payment"):
            # Non-payment tasks can proceed automatically
            approved_task_ids.append(task["task_id"])
        else:
            # Payment tasks need user approval
            approval_status = "pending"
            for approval in state["pending_approvals"]:
                if approval["task_id"] == task["task_id"]:
                    approval_status = approval.get("status", "pending")
                    break

            if approval_status == "approved_by_user":
                approved_task_ids.append(task["task_id"])
            else:
                blocked_task_ids.append(task["task_id"])
                state["blocked_tasks"].append(
                    {
                        "task_id": task["task_id"],
                        "reason": "Awaiting user payment approval",
                        "blocked_at": datetime.now().isoformat(),
                    }
                )

    print(f"\n📊 DEPLOYMENT STATUS:")
    print(f"  Tasks Ready to Deploy: {len(approved_task_ids)}")
    print(f"  Tasks Blocked (Pending Approval): {len(blocked_task_ids)}")

    if blocked_task_ids:
        print(f"\n  ⏸️  BLOCKED TASKS:")
        for task_id in blocked_task_ids:
            task = next(t for t in state["identified_tasks"] if t["task_id"] == task_id)
            print(f"    {task_id}: {task['task_name']} - ${task['estimated_budget']:,.0f}")
            print(f"      Reason: Awaiting user approval for {task.get('payment_type', 'payment')}")

    # Deploy agents for approved tasks only
    print(f"\n\n🚀 DEPLOYING AGENTS FOR APPROVED TASKS:")

    deployed_agents = []
    for task_id in approved_task_ids:
        task = next(t for t in state["identified_tasks"] if t["task_id"] == task_id)
        agent_type = task["required_expertise"]

        if agent_type not in state["active_agents"]:
            print(f"\n  ✅ Deploying {agent_type.upper()} Agent")
            print(f"     Task: {task['task_name']}")
            print(f"     Budget: ${task['estimated_budget']:,.0f}")

            state["active_agents"].append(agent_type)
            deployed_agents.append(agent_type)

            if agent_type not in state["agent_status"]:
                state["agent_status"][agent_type] = "deployed"

            if agent_type not in state["delegated_tasks"]:
                state["delegated_tasks"][agent_type] = []
            state["delegated_tasks"][agent_type].append(task_id)

    state["executive_decisions"].append(
        {
            "decision_id": f"DEC_DEPLOY_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "decision": "Agent deployment approved",
            "agents_deployed": deployed_agents,
            "tasks_delegated": approved_task_ids,
            "tasks_blocked": blocked_task_ids,
            "timestamp": datetime.now().isoformat(),
        }
    )

    print(f"\n\n✅ AGENT DEPLOYMENT COMPLETE")
    print(f"  Agents Deployed: {len(deployed_agents)}")
    print(f"  Tasks Delegated: {len(approved_task_ids)}")

    if blocked_task_ids:
        print(f"\n  ⚠️  {len(blocked_task_ids)} task(s) awaiting user approval")
        print(f"     User action required to proceed with payment-based services")

    return state


def synthesize_executive_report(state: CEOAgentState) -> dict:
    """
    CEO creates final executive summary with decisions and outcomes
    """
    print("\n" + "=" * 80)
    print("👔 CEO - EXECUTIVE SUMMARY & RECOMMENDATIONS")
    print("=" * 80)

    total_budget = state.get("total_budget", 0)
    allocated_api = state["budget_allocated"].get("api_and_tools", 0)
    allocated_services = state["budget_allocated"].get("services_and_payments", 0)

    pending_approvals = len(
        [
            a
            for a in state.get("pending_approvals", [])
            if a.get("status") == "pending_user_approval"
        ]
    )

    executive_summary = f"""

╔══════════════════════════════════════════════════════════════════════════════╗
║                         EXECUTIVE SUMMARY                                    ║
║                    CEO Strategic Analysis Report                             ║
╔══════════════════════════════════════════════════════════════════════════════╗

COMPANY: {state['company_name']}
INDUSTRY: {state['industry']}
LOCATION: {state['location']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRATEGIC ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tasks Identified: {len(state.get('identified_tasks', []))}
Agents Deployed: {len(state.get('active_agents', []))}
Timeline: {state.get('target_completion_days', 90)} days

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BUDGET ALLOCATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Budget: ${total_budget:,.2f}

API & Tools (Auto-Approved): ${allocated_api:,.2f}
  - Design software subscriptions
  - Development tools & platforms
  - Analytics & monitoring

Services & Payments (User Approval Required): ${allocated_services:,.2f}
  - Legal filing fees
  - Service subscriptions
  - Advertising spend

Pending User Approvals: {pending_approvals}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RISK ASSESSMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Identified Risks: {len(state.get('risks', []))}
"""

    # Add risk details
    for risk in state.get("risks", [])[:5]:  # Top 5 risks
        executive_summary += f"\n  • {risk.get('description', 'Risk identified')}"
        executive_summary += (
            f"\n    Severity: {risk.get('severity', 'MEDIUM')} | "
            f"Probability: {risk.get('probability', 'MEDIUM')}"
        )

    executive_summary += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CEO RECOMMENDATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. IMMEDIATE ACTIONS (No Payment Required)
   - Brand identity development with AI tools
   - Content strategy planning
   - Marketing technology evaluation

2. PENDING USER APPROVAL
   - Legal filing fees (~$500)
   - Website development services (~$35,000)
   - Marketing campaign ad spend (~$3,000)

3. RISK MITIGATION
   - All payments require explicit user approval
   - Guard rails prevent unauthorized spending
   - CFO agent monitors API/tool costs
   - Compliance checks before any legal filings

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Agents ready to execute non-payment tasks immediately
⏸️  Payment-based services await your approval
🔒 All financial commitments protected by approval workflow

╚══════════════════════════════════════════════════════════════════════════════╝
"""

    state["final_executive_summary"] = executive_summary
    print(executive_summary)

    return state


# ============================================================================
# CEO WORKFLOW ROUTING
# ============================================================================


def route_ceo_workflow(state: CEOAgentState) -> str:
    """Route CEO workflow based on current phase"""
    current_phase = state.get("current_phase", "analysis")

    if current_phase == "analysis":
        return "deployment"
    elif current_phase == "deployment":
        return "reporting"
    else:
        return END


# ============================================================================
# BUILD CEO ORCHESTRATION GRAPH
# ============================================================================


def build_ceo_graph() -> StateGraph:
    """Build the CEO orchestration workflow graph"""
    graph = StateGraph(CEOAgentState)

    # Add nodes
    graph.add_node("analyze", analyze_strategic_objectives)
    graph.add_node("deploy", deploy_specialized_agents)
    graph.add_node("report", synthesize_executive_report)

    # Add edges
    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "deploy")
    graph.add_edge("deploy", "report")
    graph.add_edge("report", END)

    return graph.compile()


if __name__ == "__main__":
    # Test CEO agent
    print("🚀 CEO Agent - Executive Orchestration System")
    print("=" * 80)

    initial_state = {
        "company_name": "Amazon Granite LLC",
        "industry": "Granite & Engineered Quartz Countertops",
        "location": "Cincinnati, Ohio",
        "strategic_objectives": [
            "Launch digital brand presence",
            "Implement AR customer experience",
            "Establish legal foundation",
        ],
        "total_budget": 50000,
        "target_completion_days": 90,
        "budget_allocated": {},
        "budget_reserved_for_fees": 0,
        "pending_approvals": [],
        "approved_actions": [],
        "rejected_actions": [],
        "executive_decisions": [],
        "business_goals": [],
        "active_agents": [],
        "agent_outputs": [],
        "agent_status": {},
        "delegated_tasks": {},
        "identified_tasks": [],
        "assigned_tasks": {},
        "completed_tasks": [],
        "blocked_tasks": [],
        "risks": [],
        "risk_mitigation_plans": {},
        "opportunities": [],
        "opportunity_analysis": [],
        "guard_rail_violations": [],
        "liability_warnings": [],
        "compliance_status": {},
        "deliverables": [],
        "status_reports": [],
        "final_executive_summary": "",
        "current_phase": "analysis",
        "completed_phases": [],
        "milestones": [],
    }

    # Build and run CEO graph
    ceo_graph = build_ceo_graph()
    final_state = ceo_graph.invoke(initial_state)

    print("\n\n✅ CEO ORCHESTRATION COMPLETE")
    print(f"Executive Decisions Made: {len(final_state.get('executive_decisions', []))}")
    print(f"Agents Deployed: {len(final_state.get('active_agents', []))}")
    print(f"Pending User Approvals: {len(final_state.get('pending_approvals', []))}")
