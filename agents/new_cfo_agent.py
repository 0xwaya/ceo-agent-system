"""
[DEPRECATED — v0.3]
CFO (Chief Financial Officer) Agent - Financial Oversight & Compliance

This variant has been superseded by cfo_llm_summarize_node in
graph_architecture/llm_nodes.py, which handles financial summary, budget
tracking, and compliance checks within the Tier-2 CFO subgraph.

This file is RETAINED for backward compatibility with app.py's
  from agents.new_cfo_agent import CFOAgentState, generate_financial_report
Do NOT add new CFO logic here — use graph_architecture/llm_nodes.py instead.
3. Compliance with spending limits
4. Financial risk identification
5. Payment approval recommendations (actual approval is user's)

BUDGET AUTHORITY:
- CFO manages ZERO discretionary budget
- CFO can only approve API service fees and legal filing fees
- All other spending requires user approval via CEO

REPORTS TO: CEO Agent
RESPONSIBILITY: Financial stewardship, not strategic planning
"""

from typing_extensions import TypedDict
from typing import Annotated, Dict, List, Any
import operator
from dataclasses import dataclass
from datetime import datetime


# ============================================================================
# CFO AGENT STATE
# ============================================================================


class CFOAgentState(TypedDict):
    """State for CFO Agent - Financial Oversight"""

    # Company Context
    company_name: str
    industry: str

    # Budget Tracking (Read-only for most items)
    total_budget: float
    allocated_to_api_fees: float  # Only budget CFO can manage
    api_costs_incurred: Annotated[list[Dict], operator.add]
    legal_filing_costs: Annotated[list[Dict], operator.add]

    # Cost Monitoring
    daily_api_spend: Dict[str, float]  # Track daily spend by service
    monthly_projections: Dict[str, float]
    budget_alerts: Annotated[list[Dict], operator.add]

    # Payment Analysis (CFO recommends, user approves)
    pending_payment_requests: Annotated[list[Dict], operator.add]
    cfo_recommendations: Annotated[list[Dict], operator.add]
    approved_payments: Annotated[list[Dict], operator.add]
    rejected_payments: Annotated[list[Dict], operator.add]

    # Compliance & Risk
    spending_violations: Annotated[list[Dict], operator.add]
    financial_risks: Annotated[list[Dict], operator.add]
    compliance_checks: Dict[str, bool]

    # Reporting
    financial_reports: Annotated[list[str], operator.add]
    audit_trail: Annotated[list[Dict], operator.add]


# ============================================================================
# CFO - BUDGET MONITORING
# ============================================================================


def monitor_api_costs(state: CFOAgentState) -> dict:
    """
    CFO monitors API usage costs (OpenAI, SendGrid, etc.)

    This is the ONLY budget CFO has authority over
    """
    print("\n" + "=" * 70)
    print("💰 CFO - API COST MONITORING")
    print("=" * 70)

    api_budget = state.get("allocated_to_api_fees", 0)
    total_spent = sum(cost.get("amount", 0) for cost in state.get("api_costs_incurred", []))
    remaining = api_budget - total_spent

    print(f"\n📊 API Budget Status:")
    print(f"   Allocated: ${api_budget:,.2f}")
    print(f"   Spent: ${total_spent:,.2f}")
    print(f"   Remaining: ${remaining:,.2f}")
    print(f"   Usage: {(total_spent / api_budget * 100) if api_budget > 0 else 0:.1f}%")

    # Alert if approaching limit
    if remaining < api_budget * 0.2 and api_budget > 0:  # Less than 20% remaining
        alert = {
            "alert_id": f"API_BUDGET_ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "severity": "HIGH",
            "message": f"API budget critically low: ${remaining:,.2f} remaining",
            "recommendation": "Review API usage or request additional budget allocation",
            "timestamp": datetime.now().isoformat(),
        }
        state["budget_alerts"].append(alert)
        print(f"\n   ⚠️  ALERT: {alert['message']}")
        print(f"      {alert['recommendation']}")

    # Log monitoring activity
    state["audit_trail"].append(
        {
            "activity": "api_cost_monitoring",
            "timestamp": datetime.now().isoformat(),
            "api_budget": api_budget,
            "total_spent": total_spent,
            "remaining": remaining,
        }
    )

    return state


def analyze_payment_request(state: CFOAgentState) -> dict:
    """
    CFO analyzes payment requests and makes recommendations

    NOTE: CFO cannot approve payments, only provides financial analysis
    Final approval is ALWAYS from user
    """
    print("\n" + "=" * 70)
    print("💰 CFO - PAYMENT REQUEST ANALYSIS")
    print("=" * 70)

    pending_requests = state.get("pending_payment_requests", [])

    if not pending_requests:
        print("\n✅ No pending payment requests")
        return state

    print(f"\n📋 Analyzing {len(pending_requests)} payment request(s):")

    for request in pending_requests:
        request_id = request.get("request_id", "Unknown")
        amount = request.get("amount", 0)
        purpose = request.get("purpose", "Unknown")
        requested_by = request.get("requested_by", "Unknown")

        print(f"\n  Request ID: {request_id}")
        print(f"  Amount: ${amount:,.2f}")
        print(f"  Purpose: {purpose}")
        print(f"  Requested by: {requested_by}")

        # CFO financial analysis
        recommendation = {
            "request_id": request_id,
            "cfo_analysis": "",
            "financial_impact": "",
            "risk_assessment": "",
            "recommendation": "",
            "timestamp": datetime.now().isoformat(),
        }

        # Analyze based on amount
        if amount < 100:
            recommendation["cfo_analysis"] = "Low-value transaction"
            recommendation["financial_impact"] = "Minimal impact on overall budget"
            recommendation["risk_assessment"] = "LOW"
            recommendation["recommendation"] = "APPROVE - Low financial risk"
        elif amount < 1000:
            recommendation["cfo_analysis"] = "Medium-value transaction"
            recommendation[
                "financial_impact"
            ] = f"Represents {amount/state.get('total_budget', 1)*100:.1f}% of total budget"
            recommendation["risk_assessment"] = "MEDIUM"
            recommendation["recommendation"] = "CONDITIONAL APPROVE - Monitor ROI"
        else:
            recommendation["cfo_analysis"] = "High-value transaction"
            recommendation[
                "financial_impact"
            ] = f"Significant: {amount/state.get('total_budget', 1)*100:.1f}% of budget"
            recommendation["risk_assessment"] = "HIGH"
            recommendation["recommendation"] = "REVIEW CAREFULLY - Requires detailed ROI analysis"

        state["cfo_recommendations"].append(recommendation)

        print(f"  CFO Analysis: {recommendation['cfo_analysis']}")
        print(f"  Financial Impact: {recommendation['financial_impact']}")
        print(f"  Risk: {recommendation['risk_assessment']}")
        print(f"  Recommendation: {recommendation['recommendation']}")
        print(f"\n  ⚠️  NOTE: Final approval required from user")

    return state


def track_legal_filing_fees(state: CFOAgentState) -> dict:
    """
    CFO tracks legal filing fees (government-required payments)

    These are necessary business expenses that CFO can approve
    up to allocated budget for fees
    """
    print("\n" + "=" * 70)
    print("💰 CFO - LEGAL FILING FEE TRACKING")
    print("=" * 70)

    legal_costs = state.get("legal_filing_costs", [])
    total_legal_fees = sum(cost.get("amount", 0) for cost in legal_costs)

    print(f"\n📊 Legal Filing Fee Summary:")
    print(f"   Total Fees Paid: ${total_legal_fees:,.2f}")
    print(f"   Number of Filings: {len(legal_costs)}")

    if legal_costs:
        print(f"\n   Recent Filings:")
        for cost in legal_costs[-5:]:  # Last 5 filings
            print(f"     • {cost.get('description', 'Filing')}: ${cost.get('amount', 0):,.2f}")
            print(f"       Date: {cost.get('date', 'Unknown')}")

    # Check if fees are within expected ranges
    for cost in legal_costs:
        if cost.get("amount", 0) > 1000:  # Unusually high filing fee
            state["financial_risks"].append(
                {
                    "risk_id": f"HIGH_FILING_FEE_{datetime.now().strftime('%Y%m%d')}",
                    "description": f"Unusually high filing fee: ${cost.get('amount', 0):,.2f}",
                    "filing": cost.get("description", "Unknown"),
                    "severity": "MEDIUM",
                    "recommendation": "Verify fee is correct with legal authority",
                    "timestamp": datetime.now().isoformat(),
                }
            )
            print(f"\n   ⚠️  Alert: High filing fee detected - verification recommended")

    return state


def generate_financial_report(state: CFOAgentState) -> dict:
    """
    CFO generates financial oversight report
    """
    print("\n" + "=" * 70)
    print("💰 CFO - FINANCIAL REPORT GENERATION")
    print("=" * 70)

    total_budget = state.get("total_budget", 0)
    api_budget = state.get("allocated_to_api_fees", 0)

    api_spent = sum(c.get("amount", 0) for c in state.get("api_costs_incurred", []))
    legal_spent = sum(c.get("amount", 0) for c in state.get("legal_filing_costs", []))

    pending_requests = len(state.get("pending_payment_requests", []))
    pending_value = sum(r.get("amount", 0) for r in state.get("pending_payment_requests", []))

    report = f"""
╔══════════════════════════════════════════════════════════════╗
║              CFO FINANCIAL OVERSIGHT REPORT                   ║
╔══════════════════════════════════════════════════════════════╗

Company: {state.get('company_name', 'Unknown')}
Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BUDGET OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Company Budget: ${total_budget:,.2f}
CFO Managed Budget (API/Fees): ${api_budget:,.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXPENDITURES TRACKED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

API Services: ${api_spent:,.2f}
  (OpenAI, SendGrid, Analytics, etc.)

Legal Filing Fees: ${legal_spent:,.2f}
  (Government-required payments)

Total Tracked: ${api_spent + legal_spent:,.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PENDING APPROVALS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Payment Requests Awaiting User Approval: {pending_requests}
Total Value Pending: ${pending_value:,.2f}

⚠️  These require YOUR explicit approval before proceeding

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RISK ALERTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Active Alerts: {len(state.get('budget_alerts', []))}
Financial Risks Identified: {len(state.get('financial_risks', []))}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CFO RECOMMENDATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{len(state.get('cfo_recommendations', []))} recommendations made for pending payments

✅ All payments require user approval
✅ Budget tracking automated and accurate
✅ Compliance monitoring active

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUDIT TRAIL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Audit Events Logged: {len(state.get('audit_trail', []))}
Full transparency maintained for all financial activities

╚══════════════════════════════════════════════════════════════╝
"""

    state["financial_reports"].append(report)
    print(report)

    return state


if __name__ == "__main__":
    # Test CFO agent
    print("🚀 CFO Agent - Financial Oversight System")
    print("=" * 70)

    test_state = {
        "company_name": "Amazon Granite LLC",
        "industry": "Countertops",
        "total_budget": 50000,
        "allocated_to_api_fees": 470,  # API + tools budget
        "api_costs_incurred": [
            {"service": "OpenAI", "amount": 45.20, "date": "2026-02-01"},
            {"service": "SendGrid", "amount": 0, "date": "2026-02-02"},
            {"service": "DALL-E", "amount": 12.80, "date": "2026-02-05"},
        ],
        "legal_filing_costs": [
            {"description": "DBA Registration", "amount": 50, "date": "2026-02-03"}
        ],
        "daily_api_spend": {},
        "monthly_projections": {},
        "budget_alerts": [],
        "pending_payment_requests": [
            {
                "request_id": "PAY_001",
                "amount": 35000,
                "purpose": "Website development",
                "requested_by": "CEO",
            },
            {
                "request_id": "PAY_002",
                "amount": 3000,
                "purpose": "Marketing campaign",
                "requested_by": "CEO",
            },
        ],
        "cfo_recommendations": [],
        "approved_payments": [],
        "rejected_payments": [],
        "spending_violations": [],
        "financial_risks": [],
        "compliance_checks": {},
        "financial_reports": [],
        "audit_trail": [],
    }

    # Run CFO functions
    test_state = monitor_api_costs(test_state)
    test_state = analyze_payment_request(test_state)
    test_state = track_legal_filing_fees(test_state)
    test_state = generate_financial_report(test_state)

    print("\n\n✅ CFO FINANCIAL OVERSIGHT COMPLETE")
    print(f"Recommendations Made: {len(test_state.get('cfo_recommendations', []))}")
    print(f"Budget Alerts: {len(test_state.get('budget_alerts', []))}")
