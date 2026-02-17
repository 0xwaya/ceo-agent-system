# 🎯 CEO Agent v0.3 — Quick Reference

## TL;DR — What’s New in v0.3

**Old (v0.2):** CEO always runs CFO → Engineer → Researcher in sequence.
**New (v0.3):** Prompt Expert parses intent → CEO builds `dispatch_plan` → only required agents run.

---

## Quick Commands

```bash
# Run the graph system (recommended — v0.3 dispatch loop)
python3 graph_architecture/main_graph.py

# Run CEO agent (legacy entry point)
python3 ceo_agent.py

# Run CFO agent (legacy entry point)
python3 agents/new_cfo_agent.py

# Start web app
python3 app.py
```

---

## 3-Tier Hierarchy

### Tier 1 — CEO (Orchestrator)
- Receives enriched prompt from Prompt Expert
- Calls `ceo_llm_analyze_node` → derives `dispatch_plan`
- **CANNOT** approve payments
- Consolidates summaries from all domain directors

### Tier 2 — Domain Directors (6 agents)

| Agent | Domain | Notes |
|-------|--------|-------|
| CFO | Finance | Budget gate — always runs first when finance needed |
| Engineer | Engineering | Delegates UX/WebDev/SoftEng via Tier-3 hints |
| Researcher | Research | Market & competitive analysis |
| Legal | Legal | Compliance, contracts, regulatory |
| Martech | Marketing | Delegates Branding/Content/Campaign/Social |
| Security | Security | Threat model, audit, compliance gaps |

### Tier 3 — Execution Specialists (7 agents)
Activated by Tier-3 hint flags set by Prompt Expert:
`needs_ux_design` · `needs_web_development` · `needs_software_review`
`needs_branding` · `needs_content` · `needs_campaign` · `needs_social_media`

---

## Dispatch Flow (v0.3)

```
User types raw command
       ↓
Prompt Expert (Node 0)
  → detects: finance, engineering, marketing, security, etc.
  → sets Tier-2 flags + Tier-3 hints
       ↓
CEO LLM Analysis
  → builds dispatch_plan = ["cfo", "martech", "security"]
       ↓
dispatch_orchestrator (loop)
  → idx=0 → cfo_subgraph
  → idx=1 → martech_subgraph (+ Branding/Content/Campaign/Social Tier-3)
  → idx=2 → security_subgraph
  → all done → consolidate
       ↓
[approval gate if pending_approvals]
       ↓
CEO Final Report
```

---

## Approval Workflow

```
Agent needs $$ → CEO analyzes → CFO reviews → YOU approve
```

### Auto-Approved (CFO)
✅ OpenAI API: $45
✅ DALL-E images: $12
✅ DBA filing: $50
✅ SendGrid: Free

### Requires Your Approval
⚠️ Website: $35,000
⚠️ Marketing: $3,000
⚠️ Software: varies

**Protection:** 98% of budget requires your explicit approval

---

## Guard Rails (Updated v0.3)

### Domains & Permissions

| Domain | Allowed Roles |
|--------|---------------|
| FINANCE | CEO, CFO |
| ENGINEERING | CEO, Engineer |
| RESEARCH | CEO, Researcher |
| LEGAL | CEO, Legal |
| MARKETING | CEO, Martech |
| SECURITY | CEO, Security |
| STRATEGY | CEO only |

### Forbidden
❌ Tier-2 agents bypassing CEO
❌ Tier-3 agents calling the CEO directly
❌ Any agent accessing a domain outside its permission set

---

## API Quick Reference

```python
# Analyze strategy (was: POST /api/cfo/analyze)
POST /api/ceo/analyze
{
  "company_name": "...",
  "budget": 50000,
  "objectives": [...]
}

# Get pending approvals (NEW)
GET /api/approvals/pending

# Approve payment (NEW)
POST /api/approval/<approval_id>/approve

# Reject payment (NEW)
POST /api/approval/<approval_id>/reject

# CFO financial report (NEW)
GET /api/cfo/report
```

---

## Testing

```bash
# Test CEO
python3 agents/ceo_agent.py
# Should show: "Pending User Approvals: 2"

# Test CFO
python3 agents/new_cfo_agent.py
# Should show: "Payment Requests Awaiting User Approval: 2"

# Test guard rails
python3 -c "
from agents.agent_guard_rails import *
guard = AgentGuardRail(AgentDomain.BRANDING)
result = guard.validate_payment_request(
    PaymentType.SERVICE_ORDER, 35000, 'Website'
)
print('Requires User Approval:', result['requires_user_approval'])
"
# Should output: True
```

---

## Safety Features

✅ No unauthorized spending
✅ Liability protection
✅ Financial loss prevention
✅ Audit trail
✅ Risk warnings
✅ Approval timeouts

---

## Common Scenarios

### Scenario 1: Generate Logo
```
Branding Agent → Needs DALL-E ($0.04)
→ CFO Auto-Approves (low cost)
→ Logo generated immediately
```

### Scenario 2: Build Website
```
Web Dev Agent → Needs $35,000
→ CEO proposes task
→ CFO analyzes: "HIGH risk, 70% of budget"
→ Pending YOUR approval
→ You approve → Website built
→ You reject → Task blocked
```

### Scenario 3: Run Ad Campaign
```
Campaign Agent → Needs $3,000 ad spend
→ CEO proposes task
→ CFO analyzes: "MEDIUM risk, track ROI"
→ Pending YOUR approval
→ Timeout in 24 hours
→ No response → Auto-rejected
```

---

## Decision Tree

```
Need to spend money?
│
├─ <$100 API fee? → CFO approves → Done
├─ <$500 legal fee? → CFO approves → Done
└─ Anything else? → USER MUST APPROVE → Your call
```

---

## Red Flags (Will Be Blocked)

❌ "Hire a designer" → FORBIDDEN
❌ "Contact an agency" → FORBIDDEN
❌ "Outsource to freelancer" → FORBIDDEN
❌ "Work with consultant" → FORBIDDEN

---

## Green Lights (Permitted)

✅ "Generate logo with DALL-E" → CFO can approve
✅ "File DBA with county" → CFO can approve
✅ "Subscribe to Canva Pro" → Needs your approval
✅ "Deploy website to Vercel" → Needs your approval

---

## Files Changed

```
NEW FILES:
✅ agents/ceo_agent.py (was cfo_agent.py)
✅ agents/new_cfo_agent.py (financial oversight)
✅ ceo_agent.py (launcher)
✅ docs/archive/CEO_CFO_UPGRADE_SUMMARY.md (this guide)
✅ CEO_CFO_QUICK_REFERENCE.md (quick ref)

UPDATED FILES:
✅ agents/agent_guard_rails.py (enhanced financial safety)

DEPRECATED (still works):
⚠️  cfo_agent.py (old version, use ceo_agent.py instead)
```

---

## Next Steps

1. **Read:** docs/archive/CEO_CFO_UPGRADE_SUMMARY.md (complete guide)
2. **Test:** Run `python3 ceo_agent.py`
3. **Review:** Check pending approvals
4. **Approve:** Decide which tasks proceed
5. **Monitor:** Watch CFO financial reports

---

## When to Use What

### Use CEO Agent When
- Planning strategy
- Analyzing objectives
- Breaking down tasks
- Orchestrating agents
- Assessing risks

### Use CFO Agent When
- Checking API costs
- Reviewing budget
- Tracking spending
- Analyzing payments
- Monitoring compliance

### Approve Payments When
- ROI is clear
- Budget allows
- Risk is acceptable
- Service is necessary
- Alternative options exhausted

---

## Support

📖 Full Guide: docs/archive/CEO_CFO_UPGRADE_SUMMARY.md
🚀 Roadmap: REAL_WORLD_EXECUTION_ROADMAP.md
🧪 Tests: Run agent files directly
📊 Results: docs/archive/TEST_RESULTS.md

---

**Remember:** You now have full control. No agent can spend your money without permission! 🔒
