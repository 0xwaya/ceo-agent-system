# 👔 CEO Agent — Executive AI System v0.3

**🆕 v0.3 — 3-Tier LangGraph Architecture** — Prompt Expert → CEO → 6 Domain Directors → 7 Execution Specialists

> **LLM-driven dispatch, conditional agent routing, full 13-agent hierarchy**

---

## 🚀 Quick Start

```bash
# One-command startup
./start_ceo_agent.sh

# Primary entry points
Open: http://localhost:5001/        # Landing dashboard
Open: http://localhost:5001/admin   # Admin dashboard
Open: http://localhost:5001/reports # Reports section (direct)
```

**✨ What’s New in v0.3:**

- 🧠 **Prompt Expert Agent** — Node 0 converts raw user commands into structured routing signals (LLM-backed, keyword fallback)
- 🔄 **Conditional Dispatch Loop** — CEO builds a `dispatch_plan`; only required agents run — no more hard-coded sequences
- 🌐 **6 Tier-2 Domain Directors** — CFO · Engineer · Researcher · Legal · Martech · Security (each a full LLM subgraph)
- ⚡ **7 Tier-3 Execution Specialists** — UX/UI · WebDev · SoftEng · Branding · Content · Campaign · SocialMedia
- 🛠️ **Centralised `llm_nodes.py`** — One LLM function per role; `TIER2_NODE_MAP` / `TIER3_NODE_MAP` registries
- 🔒 **Role-Gated `tools.py`** — Domain permission enforcement before any tool executes
- 🛡️ **Security Tier-2 Subgraph** — Threat modelling, audit, compliance gap analysis now in the graph
- 📊 **Executive Reports** — CEO/domain-level summaries, risk snapshots, and budget analysis
- 🗂️ **Artifact Pipeline** — Every agent run persists reviewable output files in `static/generated_outputs/`

> **First Push to Empty Repo:** If your GitHub repository exists but has no commits yet, use the quick upload commands in [GITHUB_SETUP.md → Fast Path (Your Current Status)](docs/GITHUB_SETUP.md#fast-path-your-current-status).

👉 **[Complete CEO Agent Documentation →](docs/CEO_AGENT_README.md)**
👉 **[Rebrand Summary & Features →](docs/archive/CEO_AGENT_REBRAND_SUMMARY.md)**

---

## 🎨 **Graph Architecture — v0.3 (3-Tier LangGraph)**

### LLM-driven dispatch, Prompt Expert, 13-agent hierarchy

```bash
# Run the v0.3 graph system directly
python3 graph_architecture/main_graph.py

# Or via the web dashboard
Open: http://localhost:5001/graph
```

**Architecture overview:**

| Tier | Agent | Role |
|------|-------|------|
| Node 0 | Prompt Expert | Parses raw user input into routing signals |
| Tier 1 | CEO | LLM orchestrator, builds `dispatch_plan` |
| Tier 2 | CFO | Finance, budget analysis |
| Tier 2 | Engineer | Architecture, delegates Tier-3 |
| Tier 2 | Researcher | Market & competitive analysis |
| Tier 2 | Legal | Compliance & regulatory |
| Tier 2 | Martech | Marketing strategy, delegates Tier-3 |
| Tier 2 | Security | Threat model & audit |
| Tier 3 | UX/UI, WebDev, SoftEng | Under Engineer |
| Tier 3 | Branding, Content, Campaign, SocialMedia | Under Martech |

👉 **[Graph Dashboard Quick Start →](docs/GRAPH_DASHBOARD_QUICK_START.md)**
👉 **[Full Implementation Details →](docs/GRAPH_UI_IMPLEMENTATION.md)**
👉 **[Graph Architecture Docs →](graph_architecture/README.md)**

---

## 🤖 Legacy Interfaces (Still Available)

### 1. 💬 Interactive Chat

**Chat with AI experts in real-time** - The most engaging way to get help!

```bash
python3 interactive_chat.py
```

Chat naturally with specialized agents:

- 💼 **CFO Agent** - Strategy, budgets, planning
- 🎨 **Branding Agent** - Logo design, visual identity
- 💻 **Web Dev Agent** - Websites, AR integration
- ⚖️ **Legal Agent** - DBA, trademark, compliance
- 📊 **MarTech Agent** - CRM, analytics, automation
- 📸 **Content Agent** - Video, photography, SEO
- 🚀 **Campaign Agent** - Ads, media, launch strategy

**[📖 Quick usage & commands →](docs/QUICK_START.md)**

### 2. 🎯 CFO Multi-Agent Orchestrator

**Execute complete strategic plans** with coordinated expert agents

```bash
python3 cfo_agent.py
```

The CFO agent analyzes objectives, creates specialized agents, manages budgets, and delivers executive summaries.

**[📖 CEO/CFO quick reference →](docs/CEO_CFO_QUICK_REFERENCE.md)**

### 3. 📊 Marketing Agent (Original)

**Focused marketing strategy** for countertop businesses

```bash
python3 agent.py
```

Specialized in brand analysis and marketing for granite/quartz industry.

---

## ✨ Quick Start

### Verify Real Output Artifacts

After running an agent from `/admin` → `Agents` → `Run & View Output`, you can review saved files in two ways:

- In-app: generated files appear directly in the workspace under **Generated Files**
- On disk: open `static/generated_outputs/<agent_type>/<run_id>_<company_slug>/`

Common generated outputs include `result.json`, `summary.md`, and agent-specific artifacts (for branding this includes SVG logo proposals and social avatars).

### Interactive Chat Example

```text
python3 interactive_chat.py

👤 You: @branding @web I need a logo and website for SURFACECRAFT STUDIO

🎨 Branding: I'll create 4 logo concepts following the Golden Ratio...
💻 Web Dev: I'll build a Next.js site with AR countertop visualization...
```

### CFO Orchestrator Example

```text
python3 cfo_agent.py

🎯 CFO: Analyzing strategic objectives...
⚖️ Deploying Legal Agent for DBA registration...
🎨 Deploying Branding Agent for visual identity...
💻 Deploying Web Dev Agent for AR website...
📊 Executive Summary: $95.5K budget, 287-day timeline, 6 agents deployed
```

---

## 🎓 Expert Knowledge Base

Each agent is designed with **master-level expertise** from:

### Academic Institutions

- **MIT** - OpenCourseWare (Business, Technology, Design)
- **Stanford GSB** - Marketing Strategy, Brand Management
- **Harvard Business School** - Strategic Planning, Case Studies
- **RISD** - Visual Design Principles, Typography
- **Carnegie Mellon** - Human-Computer Interaction
- **Northwestern Kellogg** - Integrated Marketing

### Industry Frameworks

- **Consulting**: McKinsey, BCG, Bain methodologies
- **Venture Capital**: Y Combinator, a16z best practices
- **Technology**: Google, Meta, Microsoft design systems
- **Marketing**: HubSpot, Salesforce, Adobe frameworks

---

## 📁 Project Files

```text
langraph/
├── interactive_chat.py          # 💬 Interactive multi-agent chat (NEW!)
├── cfo_agent.py                 # 💼 CFO orchestrator agent (NEW!)
├── specialized_agents.py        # 🤖 Expert agent implementations (NEW!)
├── agent_knowledge_base.py      # 🎓 Master-level expertise database (NEW!)
├── agent.py                     # 📊 Marketing agent (upgraded)
├── chat_agent.py                # Original interactive agent
├── docs/QUICK_START.md          # 🚀 Main runbook and command guide
├── docs/CEO_CFO_QUICK_REFERENCE.md  # 🎯 CEO/CFO architecture quick reference
└── README.md                    # This file
```

---

## 🚀 Installation

### Prerequisites

- Python 3.10+
- pip 26.0.1+

### Setup

```bash
# Navigate to project
cd /Users/pc/code/langraph

# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install langgraph langchain-core typing-extensions

# Run interactive chat
python3 interactive_chat.py
```

---

## 🧪 Smoke Checks

Use the lightweight dashboard smoke check to verify rendering/config wiring across routes and environments.

```bash
make smoke
```

What it covers:

- `/graph` renders with graph dashboard bootstrap config
- `/admin` renders with admin dashboard bootstrap config
- Legacy `index.html` template renders with legacy bootstrap config
- Both `ENVIRONMENT=development` and `ENVIRONMENT=production` paths are validated

This smoke check also runs automatically:

- In CI via `.github/workflows/code-quality.yml`
- In pytest via `tests/test_smoke_dashboard_render.py`

---

## 💡 Usage Examples

### Chat: Get Logo Design Help

```text
You: @branding I need a modern logo for my countertop business

Branding: For your logo, I recommend:
          - Golden Ratio (1.618) proportions
          - Navy (#1A365D) + Warm Gray for trust & craftsmanship
          - Works from 16px (favicon) to building signage
          Budget: $10K | Timeline: 28 days
```

### Chat: Plan Website with AR

```text
You: @web How much for a website where customers can visualize countertops?

Web Dev: I'll build with Next.js + 8th Wall WebAR:
         - Users upload kitchen photo
         - Overlay different stone options in AR
         - 3D models with Three.js
         - Performance: Lighthouse >90
         Budget: $25-35K | Timeline: 13 weeks
```

### Chat: Complete Strategy

```text
You: @all I'm rebranding to SURFACECRAFT STUDIO with $100K budget

CFO: Strategic breakdown across 6 domains...
Legal: DBA filing process starts immediately...
Branding: 4 logo concepts following RISD principles...
Web Dev: Next.js site with AR integration...
MarTech: CRM + analytics implementation...
Content: Video, photography, case studies...
Campaigns: 90-day launch strategy...
```

---

## 🎯 Use Case: SURFACECRAFT STUDIO Launch

Complete rebrand execution for granite/quartz countertop business:

### Strategic Objectives

✅ File DBA registration for SURFACECRAFT STUDIO
✅ Create professional logo and visual identity (AI-designed)
✅ Build website with AR integration (AI-coded)
✅ Set up marketing technology stack (AI-configured)
✅ Produce foundational content (AI-created)
✅ Launch Phase 1 campaigns within 90 days (AI-managed)

### Budget Allocation ($4,500 total - AI agents do the work)

#### AI-Powered Execution Model

All design, development, and marketing work performed by specialized AI agents. Budget covers only essential tools, platforms, and advertising spend.

| Domain | Budget | Purpose |
| --- | --- | --- |
| Campaign Launch (Ad Spend) | $3,000 | Actual advertising budget for Google/Meta campaigns |
| Web Development (Hosting/Platforms) | $500 | Domain, hosting, AR platform access |
| Legal & Compliance | $500 | DBA filing fees, required government costs |
| Content Production (Tools) | $150 | Stock assets, design software subscriptions |
| Branding & Identity (Tools) | $150 | Adobe CC/Figma subscription, font licenses |
| MarTech Stack (Minimal) | $200 | Free-tier platforms + minimal paid features |

#### AI-Powered Value Proposition

All creative, technical, and strategic work executed by AI agents - not outsourced to external agencies.

### Success Metrics (90-day)

- 📊 **Website Traffic**: 5,000+ unique visitors/month
- 🎯 **Lead Generation**: 50+ qualified quote requests
- 🚀 **AR Engagement**: 500+ feature interactions
- 💰 **Revenue Pipeline**: $200K+ in new opportunities
- 📈 **Brand Awareness**: 25% increase in Cincinnati metro

---

## 🤖 Available Agents

### 💼 CFO Agent

Strategic planning, budget management, multi-agent orchestration.

**Knowledge:** Harvard MBA strategic frameworks, McKinsey problem-solving, MIT Sloan financial management.

**Core Capabilities:**

- MECE task decomposition
- Budget allocation & tracking
- Risk assessment & mitigation
- Timeline & dependency management
- Executive reporting

---

### 🎨 Branding Agent

Logo design, visual identity, brand strategy.

**Knowledge:** RISD design principles, Stanford brand management, color theory, typography.

**Core Capabilities:**

- Logo design (4 concepts)
- Brand positioning frameworks
- Color palette development
- Typography systems
- Brand guideline creation
- Trademark strategy

**Budget & Timeline:** $8-12K | 28 days

---

### 💻 Web Development Agent

Full-stack development, AR integration, performance optimization.

**Knowledge:** MIT software engineering, CMU HCI, Google web fundamentals.

**Core Capabilities:**

- Next.js/React development
- WebAR integration (8th Wall)
- 3D visualization (Three.js)
- CMS integration (Sanity)
- SEO & accessibility (WCAG 2.1)
- Core Web Vitals optimization

**Budget & Timeline:** $25-35K | 91 days

---

### ⚖️ Legal Agent

DBA registration, trademark filing, compliance.

**Knowledge:** Harvard Law, SBA legal guidelines, Ohio business law.

**Core Capabilities:**

- DBA registration process
- USPTO trademark search
- Business licensing
- Compliance management
- Contract review
- Risk assessment

**Budget & Timeline:** $500 | 21 days

---

### 📊 MarTech Agent

CRM setup, analytics, marketing automation.

**Knowledge:** HubSpot Academy, Salesforce frameworks, marketing operations.

**Core Capabilities:**

- CRM configuration
- Google Analytics 4 setup
- Marketing automation workflows
- Lead scoring systems
- Integration architecture
- Analytics dashboards

**Budget & Timeline:** $6-8K | 21 days

---

### 📸 Content Agent

Video production, photography, content marketing.

**Knowledge:** USC Cinematic Arts, content marketing best practices, SEO.

**Core Capabilities:**

- Brand video production
- Professional photography
- Case study creation
- Blog content & SEO
- Social media assets
- Content distribution planning

**Budget & Timeline:** $12-15K | 35 days

---

### 🚀 Campaign Agent

Media planning, ad campaigns, optimization.

**Knowledge:** Northwestern Kellogg IMC, Google/Meta certifications, growth marketing.

**Core Capabilities:**

- Multi-channel campaign strategy
- Google Ads management
- Meta (Facebook/Instagram) campaigns
- Budget allocation (70-20-10)
- Performance optimization
- Attribution modeling

**Budget & Timeline:** $20-25K | 90 days

---

## 📖 Documentation

- **[README.md](README.md)** - Project overview and navigation
- **[QUICK_START.md](docs/QUICK_START.md)** - Day-to-day runbook and commands
- **[CEO_AGENT_README.md](docs/CEO_AGENT_README.md)** - CEO-mode deep guide
- **[CEO_CFO_QUICK_REFERENCE.md](docs/CEO_CFO_QUICK_REFERENCE.md)** - CEO/CFO operating model
- **[DOCS_KEEP_ARCHIVE_MANIFEST.md](docs/DOCS_KEEP_ARCHIVE_MANIFEST.md)** - Doc lifecycle and archive candidates

---

## 🔧 Advanced Features

### Multi-Agent Collaboration

Agents work together on complex tasks:

```python
# CFO coordinates specialized agents
cfo_agent.deploy_agents({
    "legal": ["DBA registration"],
    "branding": ["Logo design", "Brand guidelines"],
    "web_development": ["Website", "AR integration"]
})
```

### Session Memory

Chat system maintains context:

- Company information
- Budget constraints
- Previous decisions
- Conversation history

### Dynamic Agent Invocation

Automatically suggests relevant agents:

```text
You: I need help with trademark filing

💡 This sounds like a question for the Legal Agent!
💡 Type '@legal' to get expert help
```

---

## 🎯 LangGraph Architecture

### State Management

```python
class CFOAgentState(TypedDict):
    strategic_objectives: Annotated[list[str], operator.add]
    budget_allocated: Dict[str, float]
    active_agents: Annotated[list[str], operator.add]
    agent_outputs: Annotated[list[Dict], operator.add]
```

### Graph Workflow

```text
START → Strategic Analysis → Agent Deployment → Execution → Summary → END
```

### Best Practices Applied

- **TypedDict**: Compile-time type checking
- **State Accumulation**: Lists with `operator.add`
- **Conditional Routing**: Dynamic workflow branching
- **Pure Functions**: Immutable state updates
- **Factory Pattern**: Dynamic agent creation

---

## 🚀 Getting Started

1. **Try Interactive Chat First** (most engaging)

   ```bash
   python3 interactive_chat.py
   ```

2. **Explore CFO Orchestrator** (full automation)

   ```bash
   python3 cfo_agent.py
   ```

3. **Check Original Marketing Agent** (legacy)

   ```bash
   python3 agent.py
   ```

---

## 🤝 Contributing

This is a demonstration of advanced LangGraph capabilities. To adapt:

1. Modify strategic objectives in [cfo_agent.py](cfo_agent.py)
2. Add new agents in [specialized_agents.py](agents/specialized_agents.py)
3. Extend knowledge base in [agent_knowledge_base.py](agents/agent_knowledge_base.py)
4. Customize chat responses in [interactive_chat.py](interactive_chat.py)

---

## 📄 License

Educational demonstration project showcasing LangGraph multi-agent systems.

---

**Built with**: LangGraph | Python 3.10+ | Master-level expertise from MIT, Stanford, Harvard, RISD, CMU

**Perfect for**: Brand launches, digital transformation, strategic planning, startup execution

**Try it now**: `python3 interactive_chat.py` 🚀

## Legacy Installation Guide

```bash
# Clone or navigate to project directory
cd /Users/pc/code/langraph
```

```bash
# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
```

```bash
# Install dependencies
pip install langgraph langchain-core typing-extensions
```

```bash
# Run the agent
python3 agent.py
```

## Usage

### Automated Mode (Default)

Run the full strategic analysis automatically:

```bash
python3 agent.py
```

The agent will execute all 7 phases and generate a comprehensive report.

### Interactive Chat Mode

Interact with the agent and provide custom inputs:

```bash
python3 chat_agent.py
```

Answer prompts to customize:

- Company name and industry
- Location and target market
- Brand preferences (e.g., name style, visual direction)
- Budget constraints

## Project Structure

```text
langraph/
├── agent.py              # Main agent workflow (automated mode)
├── chat_agent.py         # Interactive chat interface
├── README.md             # This file
└── docs/
    └── copilot-instructions.md  # AI coding assistant guidelines
```

## Agent Workflow

### Phase 1: Market Research

- Demographics analysis for Cincinnati metro area
- Competitor identification and positioning
- Market size estimation and growth opportunities

### Phase 2: Trend Analysis

- Design trends (waterfall edges, book-matched slabs)
- Material trends (quartz vs granite ratio)
- Technology trends (AR visualization, online booking)
- Customer behavior patterns

### Phase 3: Brand Assessment

- Current brand name analysis (trademark risks, SEO conflicts)
- Competitive positioning gaps
- Target audience perception study
- Social media audit (@amazongranite Instagram analysis)
- Digital presence evaluation

### Phase 4: DBA Creation

- Generate 6 craft-focused name options
- Detailed scoring matrix (memorability, SEO, craft focus, premium feel, scalability)
- Recommended DBA: **SURFACECRAFT STUDIO**

### Phase 5: Brand Positioning

- Brand positioning statement and pillars
- **4 logo design prototypes**:
  - Concept A: The Craftsman Mark (SC monogram)
  - Concept B: The Studio Seal (badge format)
  - Concept C: The Modern Surface ⭐ (layered geometric - RECOMMENDED)
  - Concept D: The Veined Signature (organic flowing)
- Complete visual identity system (colors, typography, photography)
- Social media migration plan (@amazongranite → @surfacecraftstudio)

### Phase 6: Marketing Strategy

- Target audience profiles (affluent homeowners, designers, investors)
- Marketing channel mix (Google Ads, Instagram, Houzz, SEO, partnerships)
- 6 campaign ideas with activation plans
- Budget recommendation: $85K/year with expected 4:1 ROI

### Phase 7: Final Report

- Executive summary
- Complete strategic roadmap
- KPIs and success metrics
- 90-day phased launch plan
- Next steps checklist

## Output Examples

### DBA Recommendations

```text
1. SURFACECRAFT STUDIO ⭐ (44/50)
2. THE SURFACECRAFT CO. (42/50)
3. SURFACECRAFT COLLECTIVE (40/50)
4. ARTISAN SURFACEWORKS (40/50)
5. CINCINNATI SURFACECRAFT (38/50)
6. STONE & SURFACECRAFT (34/50)
```

### Logo Concept (Recommended)

```text
Concept C: 'THE MODERN SURFACE'
- Layered rectangles representing stacked stone slabs
- 3 offset layers in gradient (charcoal → slate → copper)
- Clean, contemporary, scalable design
- Perfect for digital/web applications
```

### Marketing Budget Breakdown

```text
$85,000/year total:
- Digital Advertising (Google/Meta): $60K (70%)
- Content Creation: $10K (12%)
- Events & Sponsorships: $8K (9%)
- Tools & Software: $5K (6%)
- Collateral & Print: $2K (3%)

Expected ROI: 4:1 in Year 1
```

## Customization

### Modify Company Details

Edit the `app.invoke()` parameters in `agent.py`:

```python
result = app.invoke({
    "company_name": "Your Company Name",
    "industry": "Your Industry",
    "location": "Your Location",
    "target_market": "Your Target Market",
    # ... other parameters
})
```

### Add Custom Phases

Add new nodes to the workflow:

```python
def custom_analysis(state: MarketingAgentState) -> dict:
    # Your custom logic
    return {"current_phase": "next_phase"}

graph.add_node("custom", custom_analysis)
graph.add_edge("previous_phase", "custom")
```

## Technologies

- **LangGraph**: State machine orchestration
- **Python 3.10**: Core language
- **TypedDict**: Type-safe state management
- **Operator.add**: List accumulation for state updates

## Future Enhancements

- [ ] LLM integration (OpenAI/Anthropic) for dynamic strategy generation
- [ ] Human-in-the-loop checkpoints for approval at each phase
- [ ] Checkpointing/persistence for resumable workflows
- [ ] Export reports to PDF/Word formats
- [ ] Multi-location market analysis
- [ ] A/B testing recommendations for campaigns
- [ ] Competitive intelligence scraping

## Contributing

This is a specialized agent for Amazon Granite LLC. For custom implementations:

1. Fork the repository
2. Modify industry-specific data in analysis functions
3. Update state schema for your use case
4. Adjust workflow phases as needed

## License

Proprietary - Amazon Granite LLC / Surfacecraft Studio

## Contact

For questions about the rebrand strategy or agent implementation:

- Project: Amazon Granite LLC → Surfacecraft Studio
- Market: Cincinnati, Ohio
- Industry: Granite & Engineered Quartz Countertops

---

**Built with LangGraph** | AI-Powered Brand Strategy | Cincinnati's Premier Surfacecraft
