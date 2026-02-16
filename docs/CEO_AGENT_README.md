# 👔 CEO Agent - Executive AI System

> **Production-Ready Multi-Agent AI System with Executive Governance, Financial Oversight, and Real-World Execution Capabilities**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Training Mode](https://img.shields.io/badge/status-training%20mode-orange.svg)](docs/CEO_AGENT_README.md)

![CEO Agent System](https://img.shields.io/badge/CEO_Agent-Executive_AI-667eea?style=for-the-badge&logo=openai)

---

## 🌟 What is CEO Agent

**CEO Agent** is an advanced multi-agent AI system featuring executive-level governance, financial oversight, and autonomous task execution. Built with LangGraph state machines, it orchestrates specialized AI agents to execute real-world business tasks while maintaining strict financial guard rails and requiring user approval for spending.

### 🎯 Key Features

- **👔 CEO Agent**: Executive orchestrator making strategic decisions within defined guard rails
- **💰 CFO Agent**: Financial oversight with budget management ($970 auto-approve limit)
- **🤖 6 Specialized Agents**: Brand, Legal, MarTech, UX/UI, Content, Campaigns
- **✅ Payment Approval Workflow**: 98% of budget ($49,030) requires user approval
- **🎓 Interactive Training Interface**: Develop and refine agents before production
- **🔬 Daily Research & Evolution**: Agents autonomously research latest tools and best practices
- **📊 Executive Reports**: CEO strategic summaries, CFO financial reports, performance analytics
- **🛡️ Financial Guard Rails**: Prevents unauthorized spending and liability exposure
- **⚡ Real-time Dashboard**: Professional admin interface for complete system control
- **🗂️ Artifact Persistence**: Each execution writes structured output files to `static/generated_outputs/`
- **🖼️ In-UI File Preview**: `Run & View Output` now includes a Generated Files section with previews/links

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.10 or higher
python3 --version

# Virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

### Installation

```bash
# 1. Clone or navigate to project
cd /path/to/ceo-agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment (optional - for real-world execution)
echo "OPENAI_API_KEY=your_key_here" > .env
echo "ANTHROPIC_API_KEY=your_key_here" >> .env

# 4. Start the system
python3 app.py
```

### Access Admin Dashboard

```text
🌐 Open browser: http://localhost:5001/admin
```

**Default Configuration:**

- System Mode: **Training** (safe for development)
- Total Budget: **$50,000**
- CFO Auto-Approve: **$100** (API fees), **$500** (legal fees)
- User Approval Required: **$49,030** (98% of budget)

---

## 📱 Admin Dashboard

The CEO Agent admin dashboard is your command center for managing the entire AI system.

### Dashboard Sections

| Section | Description |
| ------- | ----------- |
| **📊 Dashboard** | Real-time metrics, quick actions, activity feed |
| **🤖 Agents** | View and interact with all 6 specialized agents |
| **🎓 Training** | Interactive training modules for agent development |
| **🔬 Research** | Configure daily research for continuous improvement |
| **✅ Approvals** | Review and approve/reject payment requests |
| **📈 Reports** | Generate CEO, CFO, performance, and training reports |
| **⚙️ Settings** | System configuration, budget controls, mode switching |

### Quick Actions

```javascript
// Start CEO Strategic Analysis
Click "Strategic Analysis" → CEO analyzes objectives → Generates tasks

// Train Agents
Click "Train Agents" → Select module → Run scenarios → Save progress

// Daily Research
Click "Daily Research" → Configure topics → Start research → Review findings

// Approve Payments
Click "Pending Approvals" → Review request → Approve/Reject

// Review Real Outputs
Click "Run & View Output" on any agent → inspect Generated Files previews → open saved artifacts
```

### Generated Artifact Workflow

```text
1) User runs agent from Admin dashboard
2) API returns structured result + artifact list
3) Backend persists bundle under static/generated_outputs/
4) Dashboard renders Generated Files with preview/open links
5) Team reviews artifacts and iterates with next run
```

Standard run bundle files:

- `metadata.json`
- `result.json`
- `summary.md`
- agent-specific outputs (e.g., branding SVG logo proposals, social avatars, palette files)

Run listing endpoints:

- `GET /api/artifacts/runs`
- `GET /api/artifacts/runs/<agent_type>`

---

## 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                    CEO AGENT (Executive)                 │
│  Strategic Decisions • Task Orchestration • Risk Mgmt   │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼────────┐ ┌───▼────────┐ ┌───▼────────────┐
│  CFO Agent     │ │  Approval  │ │  Specialized   │
│  Financial     │ │  Workflow  │ │  Agents (6)    │
│  Oversight     │ │  User Gate │ │  Execution     │
└────────────────┘ └────────────┘ └────────────────┘
```

### Agent Hierarchy

### Tier 1: Executive (CEO)

- Makes strategic decisions
- Orchestrates specialized agents
- **CANNOT approve payments without user**

### Tier 2: Financial (CFO)

- Monitors spending vs budget
- Analyzes payment requests
- Auto-approves: API <$100, Legal <$500
- **NO strategic planning authority**

### Tier 3: Specialized Agents

- Brand Agent 🎨: Design, branding, visual content ($4,500 budget)
- Legal Agent ⚖️: Compliance, filings, contracts ($3,000 budget)
- MarTech Agent 📱: Marketing automation, analytics ($6,500 budget)
- UX/UI Agent ✨: User experience, interface design ($5,000 budget)
- Content Agent 📝: Marketing content creation
- Campaigns Agent 📢: Advertising campaign management

---

## 💰 Financial Guard Rails

### Budget Structure

| Category | Amount | Approval Level |
| -------- | ------ | -------------- |
| **Total Budget** | $50,000 | - |
| **CFO Managed** | $970 (2%) | Auto-approved |
| **User Approval Required** | $49,030 (98%) | Manual approval |

### Payment Types & Rules

| Payment Type | Auto-Approve Limit | Approval Required |
| ------------ | ------------------ | ----------------- |
| API Fees | <$100 | ✅ CFO |
| Legal Filing Fees | <$500 | ✅ CFO |
| Software Subscriptions | ANY | ❌ User Required |
| Service Orders | ANY | ❌ User Required |
| Advertising Spend | ANY | ❌ User Required |
| Hardware Purchase | ANY | ❌ User Required |
| Contractor Payments | **FORBIDDEN** | 🚫 Never allowed |

### Approval Workflow

```text
1. Agent identifies task requiring payment
   ↓
2. CEO creates payment approval request
   ↓
3. CFO analyzes financial impact
   ↓
4. If >$100 (API) or >$500 (legal):
   → User approval required
   → Task BLOCKED until approved
   ↓
5. User reviews in /admin → Approvals section
   ↓
6. User clicks Approve/Reject
   ↓
7. If approved: Agent executes task
   If rejected: Task cancelled
```

---

## 🎓 Training Mode

Before deploying to production, train your agents using the interactive training interface.

### Training Modules

1. **💬 Communication Skills** - Agent interaction patterns
2. **🎯 Decision Making** - Strategic decision frameworks
3. **⚠️ Risk Assessment** - Identifying and mitigating risks
4. **💰 Budget Management** - Cost control and optimization
5. **🤝 Agent Collaboration** - Multi-agent coordination

### Training Workflow

```bash
# 1. Access Training Section
Navigate to Admin Dashboard → Training

# 2. Select Module
Click on training module (e.g., "Decision Making")

# 3. Run Scenarios
Click "Run Scenario" → Agent learns from interaction

# 4. Provide Feedback
Use chat interface to give instructions and corrections

# 5. Save Progress
Click "Save Progress" to checkpoint training
```

---

## 🔬 Daily Research & Evolution

Configure agents to autonomously research and discover:

- **Latest APIs & Tools**: New services that could improve performance
- **Best Practices**: Industry standards and methodologies
- **Competitive Analysis**: Market positioning insights
- **Cost Optimization**: More affordable alternatives
- **Emerging Technologies**: Cutting-edge capabilities

### Research Configuration

```javascript
// In Admin Dashboard → Research

1. Research Schedule: Daily | Weekly | Manual
2. Research Topics: ✓ Latest APIs, ✓ Best Practices, ✓ Cost Optimization
3. Research Depth: Quick ←→ Comprehensive (1-5)
4. Click "Start Research Now"
```

### Research Findings

Results appear in real-time with:

- **Title**: Discovery headline
- **Description**: Detailed explanation
- **Tags**: Categorization (API, Best Practices, etc.)
- **Timestamp**: When discovered

---

## 📊 Reports

Generate comprehensive reports for different stakeholders:

### CEO Strategic Report

```text
- System status and operational overview
- Strategic objectives and progress
- Task completion metrics
- Recommendations for next steps
```

### CFO Financial Report

```text
- Budget summary (total, allocated, spent, remaining)
- Payment approval statistics
- Spending by category
- Financial health assessment
- Cost optimization recommendations
```

### Agent Performance Report

```text
- Tasks completed per agent
- Success rates
- Budget utilization
- Efficiency metrics
```

### Training Progress Report

```text
- Module completion status
- Agent readiness scores
- Next training steps
- Production readiness assessment
```

---

## 🔌 API Endpoints

### CEO/CFO Operations

```http
POST /api/ceo/analyze
Content-Type: application/json

{
  "objective": "Launch new product",
  "budget": 50000,
  "constraints": ["financial_safety", "user_approval_required"]
}

Response:
{
  "success": true,
  "tasks": [...],
  "pending_approvals": [...]
}
```

### Approvals Management

```http
# Get pending approvals
GET /api/approvals/pending

# Approve payment
POST /api/approval/{id}/approve

# Reject payment
POST /api/approval/{id}/reject
```

### Financial Reports

```http
GET /api/cfo/report

Response:
{
  "total_budget": 50000,
  "cfo_managed": 970,
  "user_approval_required": 49030,
  "pending_approvals": 2
}
```

### Settings

```http
POST /api/settings/update
Content-Type: application/json

{
  "systemMode": "training",
  "autoApproveAPI": true,
  "totalBudget": 50000,
  "cfoAPILimit": 100
}
```

---

## 🛠️ Real-World Execution

CEO Agent can execute actual tasks using integrated tools and APIs.

### Supported Capabilities

| Category | Tools | Status |
| -------- | ----- | ------ |
| **Design** | DALL-E 3, Canva API | ✅ Ready |
| **Email** | SendGrid | 📋 Configured |
| **Calendar** | Google Calendar API | 📋 Configured |
| **Social Media** | Twitter API v2 | 📋 Configured |
| **Storage** | AWS S3 | 📋 Configured |
| **LLM** | OpenAI GPT-4, Claude | ✅ Ready |

### Quick Start: Logo Generation

```bash
# Example: Generate logo with DALL-E
python3 tools/quick_start_dalle.py

# Or use CEO Agent:
# 1. Analyze objectives → CEO identifies logo needed
# 2. CEO creates approval request: "DALL-E image generation ($0.04)"
# 3. CFO auto-approves (under $100 API limit)
# 4. Brand Agent executes → Logo created
```

### Cost Structure

```text
Minimal Setup:    $43/month  (OpenAI + basic SendGrid)
Standard Setup:   $150/month (+ Twitter Basic, storage)
Production Setup: $500/month (+ premium tiers, higher limits)
```

See `REAL_WORLD_EXECUTION_ROADMAP.md` for complete implementation guide.

---

## 🔄 Upgrading from Old CFO System

If migrating from the previous CFO-led architecture:

```bash
# 1. Review upgrade documentation
cat docs/archive/CEO_CFO_UPGRADE_SUMMARY.md
cat CEO_CFO_QUICK_REFERENCE.md

# 2. Update imports in your code
# OLD:
from agents.cfo_agent import CFOAgentState, analyze_strategic_objectives

# NEW:
from agents.ceo_agent import CEOAgentState, analyze_strategic_objectives as ceo_analyze
from agents.new_cfo_agent import CFOAgentState, generate_financial_report

# 3. Update routes
# OLD: /api/cfo/analyze
# NEW: /api/ceo/analyze (backward compatible - both work)

# 4. Use admin dashboard
# Navigate to http://localhost:5001/admin (new primary interface)
```

**Backward Compatibility:** The old `/api/cfo/analyze` endpoint still works and routes to CEO agent.

---

## ⚙️ Configuration

### Environment Variables

```bash
# .env file
OPENAI_API_KEY=sk-...                  # For GPT-4, DALL-E
ANTHROPIC_API_KEY=sk-ant-...           # For Claude
SENDGRID_API_KEY=SG...                 # Email service
TWITTER_BEARER_TOKEN=...               # Social media
GOOGLE_CALENDAR_CREDENTIALS=./creds    # Calendar integration
AWS_ACCESS_KEY_ID=...                  # File storage
AWS_SECRET_ACCESS_KEY=...              # File storage
SECRET_KEY=your-secret-key             # Flask session

# Optional production settings
FLASK_ENV=production
GUNICORN_WORKERS=4
```

### System Settings (Admin Dashboard)

| Setting | Default | Description |
| ------- | ------- | ----------- |
| System Mode | `training` | `training` or `production` |
| Auto-Approve API | `true` | CFO auto-approves API fees <$100 |
| Email Notifications | `false` | Email alerts for approvals |
| Total Budget | `50000` | Maximum spending limit |
| CFO API Limit | `100` | Auto-approve threshold for API fees |
| CFO Legal Limit | `500` | Auto-approve threshold for legal fees |

---

## 🚀 Production Deployment

### Production Prerequisites

```bash
# Install production dependencies
pip install gunicorn gevent gevent-websocket

# Configure environment
export FLASK_ENV=production
export SECRET_KEY=$(openssl rand -hex 32)
```

### Deployment Options

#### Option 1: Gunicorn + Nginx

```bash
# Start with Gunicorn
gunicorn -w 4 \
  -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker \
  -b 0.0.0.0:5001 \
  app:app
```

#### Option 2: Docker

```bash
# Build image
docker build -t ceo-agent .

# Run container
docker run -d -p 5001:5001 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  --name ceo-agent \
  ceo-agent
```

#### Option 3: Cloud Platform

- **Heroku**: `heroku create && git push heroku main`
- **AWS EC2**: Deploy with Elastic Beanstalk
- **Google Cloud Run**: Containerized deployment
- **DigitalOcean**: App Platform

### Production Checklist

- [ ] Switch system mode to `production` in settings
- [ ] Complete all agent training modules
- [ ] Configure environment variables for all integrations
- [ ] Set up monitoring and logging
- [ ] Enable email notifications for approvals
- [ ] Configure HTTPS/SSL certificates
- [ ] Set up backup and disaster recovery
- [ ] Review and test payment approval workflow
- [ ] Configure rate limiting and security headers
- [ ] Set up automated testing and CI/CD

---

## 📚 Documentation

| Document | Description |
| -------- | ----------- |
| **README.md** | This file - comprehensive overview |
| **REAL_WORLD_EXECUTION_ROADMAP.md** | 10-week plan for real task execution |
| **docs/archive/CEO_CFO_UPGRADE_SUMMARY.md** | Complete architecture upgrade guide (archived) |
| **CEO_CFO_QUICK_REFERENCE.md** | Quick commands and decision trees |
| **SETUP_INSTRUCTIONS.md** | Step-by-step setup for real execution |
| **ARCHITECTURE.md** | Technical architecture details |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Test specific components
python3 -m pytest tests/test_api_endpoints.py
python3 -m pytest tests/test_integration.py

# Manual testing
bash tools/test_agents_quick.sh      # Test agent execution
bash tools/verify_all_agents.sh      # Verify all agents work
bash tools/test_all_buttons.sh       # Test frontend buttons
```

---

## 🤝 Contributing

CEO Agent is designed for extensibility. To add new features:

1. **New Agent**: Create in `agents/` following `base_agent.py` pattern
2. **New Tool**: Add to `tools/` with proper error handling
3. **New Guard Rail**: Update `agents/agent_guard_rails.py`
4. **New Dashboard Feature**: Update `templates/admin_dashboard.html` and `static/js/admin.js`

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🆘 Support

**Issues?**

- Check troubleshooting in documentation files
- Review agent logs in `logs/` directory
- Verify environment variables are set correctly
- Ensure all dependencies are installed

**Questions?**

- Review `CEO_CFO_QUICK_REFERENCE.md` for common scenarios
- Check `REAL_WORLD_EXECUTION_ROADMAP.md` for implementation guidance
- Examine working examples in `tools/` directory

---

## 🎯 Roadmap

### Current Version: 2.0 (Training Mode)

- ✅ CEO/CFO architecture with financial guard rails
- ✅ Interactive admin dashboard
- ✅ Payment approval workflow
- ✅ Agent training interface
- ✅ Daily research capability
- ✅ Executive reporting

### Next Version: 2.1 (Production Ready)

- 🔜 Complete agent training modules
- 🔜 Enhanced research algorithms
- 🔜 Advanced budget forecasting
- 🔜 Multi-user access control
- 🔜 Audit logs and compliance tracking
- 🔜 Mobile-responsive dashboard

### Future: 3.0 (Enterprise)

- 📅 Multi-tenancy support
- 📅 Custom agent builders
- 📅 Marketplace integration
- 📅 Advanced analytics and ML insights
- 📅 White-label options

---

## Built with ❤️ using LangGraph, Flask, and OpenAI

[![LangGraph](https://img.shields.io/badge/LangGraph-0.0.20-blue)](https://github.com/langchain-ai/langgraph)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange)](https://openai.com/)

CEO Agent - Executive AI that works for you 👔
