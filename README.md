# 👔 CEO Agent System — v0.5

**LangGraph-powered multi-agent AI platform** — Prompt Expert → CEO/CTO → 6 Domain Directors → 7 Execution Specialists, with a full artifact pipeline and real-time dashboard.

> **v0.5** — Dynamic artifact generation · Brand palette from live agent output · Security + Social Media domain artifacts · Scenario defaults versioning · Payload validation hardening

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-multi--agent-blueviolet)](https://github.com/langchain-ai/langgraph)
[![Flask](https://img.shields.io/badge/Flask-SocketIO-black?logo=flask)](https://flask.palletsprojects.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🚀 Quick Start

```bash
git clone https://github.com/0xwaya/ceo-agent-system.git
cd ceo-agent-system
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY / ANTHROPIC_API_KEY
python3 app.py

# Dashboards
open http://localhost:5001/        # Main dashboard
open http://localhost:5001/admin   # Admin / agent runner
open http://localhost:5001/graph   # LangGraph live view
```

---

## 🏗️ Architecture — 3-Tier Agent Hierarchy

```
User Input
    │
    ▼
[Node 0]  Prompt Expert ─── parses intent → routing signals
    │
    ▼
[Tier 1]  CEO ──────────── builds dispatch_plan, orchestrates
[Tier 1]  CTO ──────────── architecture review, tech-stack decisions
    │
    ├─▶ [Tier 2] CFO          Finance, budget, projections
    ├─▶ [Tier 2] Engineer     Architecture, delegates to Tier 3
    ├─▶ [Tier 2] Researcher   Market & competitive intelligence
    ├─▶ [Tier 2] Legal        Compliance & regulatory
    ├─▶ [Tier 2] Martech      Marketing strategy, delegates to Tier 3
    └─▶ [Tier 2] Security     Threat model, audit, compliance gaps
          │
          ├─▶ [Tier 3] UX/UI Designer
          ├─▶ [Tier 3] Web Development
          ├─▶ [Tier 3] Software Engineering
          ├─▶ [Tier 3] Branding & Identity
          ├─▶ [Tier 3] Content Strategy
          ├─▶ [Tier 3] Campaign Execution
          └─▶ [Tier 3] Social Media
```

| Tier | Count | Role |
|------|-------|------|
| Node 0 | 1 | Prompt Expert — intent parsing & routing |
| Tier 1 | 2 | CEO + CTO — strategic orchestration |
| Tier 2 | 6 | Domain directors — delegation & subgraph execution |
| Tier 3 | 7 | Execution specialists — deliverables & artifact output |
| **Total** | **16** | **agents** |

---

## 🎯 What It Does

Given a company description, budget, and goals the system:

1. **Parses intent** — Prompt Expert converts natural language into structured routing
2. **Builds strategy** — CEO constructs a `dispatch_plan` across relevant domains
3. **Executes in parallel** — Domain directors spawn execution agents concurrently
4. **Generates artifacts** — Every agent persists reviewable output files:
   - **Branding:** SVG logo proposals (4 directions), social avatars, dynamic brand palette CSS, moodboard SVG
   - **Web Dev:** architecture diagram (Mermaid), homepage wireframe HTML, implementation timeline MD
   - **CFO:** financial report JSON, action plan MD
   - **Security:** audit report MD, vulnerability checklist MD, security report JSON
   - **Social Media:** content calendar MD, campaign ideas MD, community playbook MD
   - **Legal / Martech / Content / Campaign:** domain-specific MDs
   - **All agents:** `metadata.json`, `result.json`, `summary.md`, `deliverables.md`
5. **Renders in report UI** — Every report shows a 📎 artifact grid with clickable file links

---

## 📊 Dashboard Features

### Main Dashboard (`/`)
- **Live Feed** — animated progress/success/error cards as agents run
- **Agents Tab** — run any of the 14 specialists individually
- **Reports Tab** — full agent report with 📎 artifact preview panel
- **Tasks Tab** — execution task tracker
- **Log Tab** — raw execution log

### Admin Dashboard (`/admin`)
- Scenario builder: company info, budget, objectives
- Run individual agents and view structured output
- Artifact browser — browse and open all generated files

### Graph Dashboard (`/graph`)
- Real-time LangGraph execution view
- Node state inspector
- Approval / human-in-the-loop controls

### Real-Time Chat (embedded)
- Per-agent conversational memory
- SocketIO `ai_chat_request/response` + REST `/api/chat/message`
- **Strategic Debate Mode** — devil's advocate persona toggle

---

## 🗂️ Artifact Pipeline

Every agent run persists files at:
```
static/generated_outputs/
└── <agent_slug>/
    └── <run_id>_<company_slug>/
        ├── metadata.json
        ├── result.json
        ├── summary.md
        ├── deliverables.md
        └── <domain-specific files…>
```

```python
from services.artifact_service import artifact_service

bundle = artifact_service.persist_agent_execution(
    agent_type="branding",
    agent_name="Branding Agent",
    task="Visual identity for ACME Corp",
    company_info={"company_name": "ACME Corp", "industry": "Technology"},
    result=agent_result_dict,
)
# bundle["artifacts"]  → [{title, url, type, mime_type}, …]
# bundle["directory"]  → relative path in static/
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Orchestration | LangGraph |
| LLM Backend | OpenAI GPT-4 / Anthropic Claude (configurable) |
| Web Framework | Flask + Flask-SocketIO |
| State Management | TypedDict + LangGraph checkpointing |
| Frontend | Vanilla JS ES6, SocketIO client |
| Artifact Storage | Filesystem (`static/generated_outputs/`) |
| Testing | pytest · 56 tests |

---

## 📦 Project Structure

```
ceo-agent-system/
├── app.py                          # Flask app — all routes + SocketIO
├── config.py                       # Settings, env, scenario defaults
├── services/
│   ├── artifact_service.py         # Artifact persistence + domain file generation
│   ├── agent_service.py
│   ├── orchestration_service.py
│   └── report_service.py
├── agents/
│   ├── base_agent.py
│   ├── ceo_agent.py
│   ├── cto_agent.py
│   ├── specialized_agents.py       # Branding, WebDev, Legal, Martech, Content, Campaign, Social
│   └── security_blockchain_agent.py
├── graph_architecture/
│   ├── main_graph.py               # Root LangGraph graph
│   ├── llm_nodes.py                # All LLM node functions (Tier 1/2/3)
│   ├── tools.py                    # Role-gated tool registry
│   ├── schemas.py
│   └── subgraphs/
├── static/
│   ├── js/app.js                   # Dashboard logic + report rendering
│   ├── js/admin.js
│   └── generated_outputs/          # Agent artifact output (git-ignored)
├── templates/
├── utils/
│   └── validators.py               # Input validation + company_info allowlist
└── tests/                          # 56 pytest tests
```

---

## 🧪 Testing

```bash
make test          # full pytest suite (56 tests)
make smoke         # fast dashboard render smoke check
make consistency   # consistency gate for docs/runtime drift
```

---

## 🔄 Version History

| Version | Highlights |
|---------|-----------|
| **v0.5** | Dynamic artifact pipeline · Brand palette from live colors · Security & Social domain artifacts · Scenario defaults v2 · Payload validation hardening |
| **v0.4** | CTO Agent (Tier 1) · Real-time LLM chat · 3-panel dashboard · Live feed cards · SocketIO |
| **v0.3** | Prompt Expert (Node 0) · Conditional dispatch loop · 6 Tier-2 directors · 7 Tier-3 specialists · Centralised `llm_nodes.py` |
| **v0.2** | CFO orchestrator · Multi-agent graph · LangGraph checkpointing |
| **v0.1** | Single-domain marketing agent |

---

## 📖 Documentation

| Doc | Purpose |
|-----|---------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Full system design, data flow, API reference |
| [docs/QUICK_START.md](docs/QUICK_START.md) | Day-to-day runbook and commands |
| [docs/CEO_AGENT_README.md](docs/CEO_AGENT_README.md) | CEO-mode deep guide |
| [graph_architecture/README.md](graph_architecture/README.md) | LangGraph subgraph guide |
| [docs/ARTIFACT_WORKFLOW.md](docs/ARTIFACT_WORKFLOW.md) | Artifact pipeline walkthrough |
| [docs/SECURITY.md](docs/SECURITY.md) | Security posture and audit notes |

---

## 🤝 Contributing

1. Fork the repo → create branch `feat/<name>`
2. Add tests for new agent behavior in `tests/`
3. Run `make test && make smoke && make consistency` — tests + dashboard + consistency gate must stay green
4. Open a PR

---

## 📄 License

[MIT](LICENSE) — built by [@0xwaya](https://github.com/0xwaya) / [Waya Labs](https://wayalabs.com)

---

**Built with** LangGraph · Flask · OpenAI · Python 3.10+
**Domains** Branding · Web Dev · Legal · Finance · Security · Martech · Content · Campaigns · Social Media

---
