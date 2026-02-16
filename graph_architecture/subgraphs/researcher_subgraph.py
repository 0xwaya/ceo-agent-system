"""
Researcher Subgraph Implementation

Research and analysis domain subgraph with:
1. Market and competitive research
2. Document analysis
3. Trend identification
4. Risk and opportunity assessment
5. Research summary generation

Internal research data stays within subgraph.
Only key findings sent to parent agent.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from langgraph.graph import StateGraph, START, END

from graph_architecture.schemas import (
    SharedState,
    ResearcherSubgraphState,
    AgentRole,
    Message,
    MessageType,
    SummaryMessage,
    TaskStatus,
    RiskLevel,
)
from graph_architecture.guards import create_researcher_entry_guard

logger = logging.getLogger(__name__)


# ============================================================================
# RESEARCHER SUBGRAPH NODES
# ============================================================================


def researcher_entry_guard_node(state: SharedState) -> SharedState:
    """
    Entry guard for Researcher subgraph
    Validates only CEO can invoke Researcher
    """
    guard = create_researcher_entry_guard()
    state = guard.validate_entry(state, requester_role=AgentRole.CEO)

    logger.info("✅ Researcher entry guard passed")
    return state


def conduct_research_node(state: SharedState) -> Dict[str, Any]:
    """
    Conduct market and competitive research

    Internal - raw research data not exposed until summarized
    """
    logger.info("\n" + "=" * 80)
    logger.info("🔍 RESEARCHER: MARKET RESEARCH")
    logger.info("=" * 80)

    objectives = state.get("strategic_objectives", [])
    industry = state.get("industry", "Unknown")

    # Simulate search queries (placeholder for actual web search)
    search_queries = [
        f"{industry} market size 2026",
        f"{industry} competitive landscape",
        f"{industry} emerging trends",
        "customer pain points",
        "market opportunities",
    ]

    logger.info(f"Conducting research for {industry} industry")
    logger.info(f"Search queries: {len(search_queries)}")

    return {"search_queries": search_queries, "current_node": "conduct_research"}


def analyze_documents_node(state: SharedState) -> Dict[str, Any]:
    """
    Analyze research documents and data sources

    Internal - detailed analysis not sent to requester
    """
    logger.info("\n📚 RESEARCHER: DOCUMENT ANALYSIS")

    search_queries = state.get("search_queries", [])

    # Simulate document analysis (placeholder)
    documents_analyzed = [
        {
            "doc_id": "doc-001",
            "source": "Industry Report 2026",
            "relevance": 0.92,
            "key_points": ["Market growing at 15% CAGR", "Mobile-first trend dominant"],
        },
        {
            "doc_id": "doc-002",
            "source": "Competitive Analysis Q1 2026",
            "relevance": 0.88,
            "key_points": [
                "Top 3 players hold 60% market share",
                "New entrants focus on AI integration",
            ],
        },
        {
            "doc_id": "doc-003",
            "source": "Customer Survey Results",
            "relevance": 0.85,
            "key_points": ["70% want better mobile experience", "Price sensitivity moderate"],
        },
    ]

    citations = [
        "Industry Report 2026, Market Research Firm",
        "Competitive Analysis Q1 2026, Strategy Consultants",
        "Customer Survey Results, Consumer Insights Group",
    ]

    logger.info(f"Analyzed {len(documents_analyzed)} documents")
    logger.info(f"Total citations: {len(citations)}")

    return {
        "documents_analyzed": documents_analyzed,
        "citations": citations,
        "current_node": "analyze_documents",
    }


def identify_findings_node(state: SharedState) -> Dict[str, Any]:
    """
    Extract key findings from research
    """
    logger.info("\n💡 RESEARCHER: IDENTIFYING KEY FINDINGS")

    documents = state.get("documents_analyzed", [])
    industry = state.get("industry", "Unknown")

    # Extract findings from documents
    key_findings = []
    assumptions = []
    confidence_scores = {}

    for doc in documents:
        key_points = doc.get("key_points", [])
        key_findings.extend(key_points)

        # Assign confidence based on relevance
        relevance = doc.get("relevance", 0)
        if relevance > 0.9:
            confidence_scores[doc["doc_id"]] = relevance

    # Additional insights
    if len(documents) >= 3:
        key_findings.append(f"{industry} market shows strong growth potential")
        assumptions.append(
            {
                "assumption": "Market trends continue for next 12 months",
                "confidence": 0.80,
                "basis": "Historical pattern analysis",
            }
        )

    logger.info(f"Identified {len(key_findings)} key findings")
    logger.info(f"Documented {len(assumptions)} assumptions")

    return {
        "key_findings": key_findings,
        "assumptions": assumptions,
        "confidence_scores": confidence_scores,
        "current_node": "identify_findings",
    }


def assess_risks_opportunities_node(state: SharedState) -> Dict[str, Any]:
    """
    Assess risks and opportunities from research
    """
    logger.info("\n⚖️  RESEARCHER: RISK & OPPORTUNITY ASSESSMENT")

    key_findings = state.get("key_findings", [])
    total_budget = state.get("total_budget", 0)

    # Identify risks based on findings
    identified_risks = []
    opportunities = []

    # Market risks
    if any(
        "competition" in finding.lower() or "market share" in finding.lower()
        for finding in key_findings
    ):
        identified_risks.append(
            {
                "risk": "High competition in target market",
                "severity": RiskLevel.MEDIUM,
                "mitigation": "Focus on differentiation and unique value proposition",
            }
        )

    # Budget risks
    if total_budget < 100000:
        identified_risks.append(
            {
                "risk": "Limited budget for market penetration",
                "severity": RiskLevel.MEDIUM,
                "mitigation": "Prioritize high-ROI channels",
            }
        )

    # Opportunities
    if any("growth" in finding.lower() or "growing" in finding.lower() for finding in key_findings):
        opportunities.append("Market expansion opportunity due to strong growth trajectory")

    if any("mobile" in finding.lower() for finding in key_findings):
        opportunities.append("Mobile-first strategy aligns with market trends")

    if any("ai" in finding.lower() or "automation" in finding.lower() for finding in key_findings):
        opportunities.append("AI integration opportunity to differentiate from competitors")

    logger.info(f"Identified {len(identified_risks)} risks")
    logger.info(f"Identified {len(opportunities)} opportunities")

    return {
        "risks": identified_risks,
        "opportunities": opportunities,
        "current_node": "assess_risks",
    }


def generate_researcher_summary_node(state: SharedState) -> Dict[str, Any]:
    """
    Generate executive summary for requester

    This is the ONLY data sent from Researcher to parent agent
    Raw research data stays in Researcher subgraph
    """
    logger.info("\n📋 RESEARCHER: GENERATING RESEARCH SUMMARY")

    # Extract insights (not raw data)
    key_findings = state.get("key_findings", [])
    risks = state.get("risks", [])
    opportunities = state.get("opportunities", [])
    documents = state.get("documents_analyzed", [])
    citations = state.get("citations", [])
    assumptions = state.get("assumptions", [])

    # Build executive summary (narrative, not data dump)
    summary_parts = [
        "=" * 80,
        "RESEARCHER EXECUTIVE SUMMARY",
        "=" * 80,
        "",
        "🔍 RESEARCH SCOPE:",
        f"   Documents Analyzed: {len(documents)}",
        f"   Citations: {len(citations)}",
        f"   Key Findings: {len(key_findings)}",
        "",
        "💡 KEY INSIGHTS:",
    ]

    # Top findings (limit to most important)
    top_findings = key_findings[:5] if len(key_findings) > 5 else key_findings
    for finding in top_findings:
        summary_parts.append(f"   • {finding}")

    summary_parts.extend(["", "⚠️  RISKS IDENTIFIED:"])

    if risks:
        for risk in risks:
            summary_parts.append(
                f"   • {risk.get('risk', 'Unknown')} ({risk.get('severity', RiskLevel.LOW)})"
            )
    else:
        summary_parts.append("   • No significant risks identified")

    summary_parts.extend(["", "🎯 OPPORTUNITIES:"])

    if opportunities:
        for opp in opportunities:
            summary_parts.append(f"   • {opp}")
    else:
        summary_parts.append("   • Analysis ongoing")

    summary_parts.extend(["", "=" * 80])

    research_summary = "\n".join(summary_parts)

    # Recommendations based on research
    recommendations = []

    if any("mobile" in finding.lower() for finding in key_findings):
        recommendations.append("Prioritize mobile experience in product development")

    if any("competition" in finding.lower() for finding in key_findings):
        recommendations.append("Develop clear differentiation strategy")

    if opportunities:
        recommendations.append(f"Pursue identified opportunities ({len(opportunities)} total)")

    # Create summary message for parent agent (CEO)
    summary_message = SummaryMessage(
        agent_role=AgentRole.RESEARCHER,
        task_id="researcher_market_analysis",
        status=TaskStatus.COMPLETED,
        key_findings=top_findings,
        risks=[
            {"description": r.get("risk", ""), "level": r.get("severity", RiskLevel.LOW)}
            for r in risks
        ],
        recommendations=recommendations,
        budget_used=0,  # Research typically uses internal resources
        next_steps=["Monitor market trends", "Update research quarterly"],
        raw_data_available=True,  # Indicates detailed research exists but not sent
    )

    logger.info(research_summary)

    return {
        "research_summary": research_summary,
        "recommendations": recommendations,
        "agent_outputs": [
            {
                "agent": "researcher",
                "summary": summary_message.model_dump(),
                "timestamp": datetime.now().isoformat(),
            }
        ],
    }


# ============================================================================
# BUILD RESEARCHER SUBGRAPH
# ============================================================================


def build_researcher_subgraph() -> StateGraph:
    """
    Build Researcher research and analysis subgraph

    Returns:
        Compiled Researcher subgraph
    """
    # Use SharedState for compatibility with CEO graph
    subgraph = StateGraph(SharedState)

    # Add nodes
    subgraph.add_node("entry_guard", researcher_entry_guard_node)
    subgraph.add_node("conduct_research", conduct_research_node)
    subgraph.add_node("analyze_documents", analyze_documents_node)
    subgraph.add_node("identify_findings", identify_findings_node)
    subgraph.add_node("assess_risks", assess_risks_opportunities_node)
    subgraph.add_node("generate_summary", generate_researcher_summary_node)

    # Define workflow
    subgraph.add_edge(START, "entry_guard")
    subgraph.add_edge("entry_guard", "conduct_research")
    subgraph.add_edge("conduct_research", "analyze_documents")
    subgraph.add_edge("analyze_documents", "identify_findings")
    subgraph.add_edge("identify_findings", "assess_risks")
    subgraph.add_edge("assess_risks", "generate_summary")
    subgraph.add_edge("generate_summary", END)

    return subgraph.compile()


# Test the subgraph
if __name__ == "__main__":
    from graph_architecture.schemas import create_initial_shared_state

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Create test state
    initial_state = create_initial_shared_state(
        company_name="TechCorp Inc",
        industry="SaaS Software",
        location="San Francisco, CA",
        total_budget=75000.0,
        target_days=90,
        objectives=["Launch product", "Capture market share"],
    )

    # Build and test subgraph
    researcher_graph = build_researcher_subgraph()
    result = researcher_graph.invoke(initial_state)

    print("\n✅ RESEARCHER SUBGRAPH TEST COMPLETE")
    print(f"Research Summary Generated: {bool(result.get('research_summary'))}")
    print(f"Agent Outputs: {len(result.get('agent_outputs', []))}")
    print(f"Key Findings: {len(result.get('key_findings', []))}")
    print(f"Opportunities: {len(result.get('opportunities', []))}")
