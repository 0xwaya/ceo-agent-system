# 🎯 CEO/CFO Quick Reference Guide

## TL;DR - What Changed

**Old:** CFO does everything (strategy + finance)
**New:** CEO leads, CFO oversees finances, USER approves spending

---

## Quick Commands

```bash
# Run CEO agent (strategic analysis)
python3 ceo_agent.py

# Run CFO agent (financial oversight)
python3 agents/new_cfo_agent.py

# Run old CFO (deprecated, for comparison)
python3 cfo_agent.py

# Start web app
python3 app.py
```

---

## 3 Key Changes

### 1. CEO Agent Now Leads
- Strategic planning
- Task breakdown
- Agent orchestration
- **CANNOT** approve payments

### 2. CFO Agent = Finance Only
- Budget tracking
- API cost monitoring
- Can approve: API fees <$100, legal fees <$500
- **CANNOT** approve: Services, subscriptions, ad spend

### 3. User Approval Required
- All payments >$100
- All service orders
- All subscriptions
- All advertising spend

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
⚠️ Software: Varies

---

## Guard Rails

### Forbidden
❌ Hiring contractors (agents must do work)
❌ External agencies
❌ Freelancers
❌ Consultants

### Allowed
✅ Software subscriptions (with approval)
✅ API services
✅ Government filing fees
✅ Platform fees

---

## Budget Breakdown

```yaml
Total: $50,000

CFO Manages ($970):
  - API fees: $470
  - Legal fees: $500

Requires User Approval ($49,030):
  - Website: $35,000
  - Marketing: $3,000
  - Software: $11,030
```

**Protection:** 98% of budget requires your explicit approval

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
