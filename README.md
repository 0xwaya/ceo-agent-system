# CEO Agent System

**16-agent LangGraph executive hierarchy** that turns a company description + budget into strategy, parallel domain execution, and downloadable artifacts (branding, finance, security, web, campaigns…).

> Most multi-agent demos stop at chat. This one produces reviewable files and a live ops dashboard.

**Current release: v0.8.2** — polished membership and sidebar controls,
protected first-administrator setup, customer sign-up,
one free successful customer analysis followed by verified subscription gating,
public homepage evidence, named authentication, private owner-scoped artifacts,
legacy runtime cleanup, opt-in MemPalace memory, durable local jobs,
token/cost ceilings, and approval-gated local exports.
No publishing, purchases, outreach, deployment, broader live research, or generated-code
execution is performed. Optional website text is attributed, untrusted homepage evidence.
Model and homepage failures are reported rather than replaced with preset results.
See [account setup and Oracle access](docs/UPGRADE_NEXT_SESSION.md) for onboarding.

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

# Optional: full test suite
make test          # full offline pytest suite
```

Use the isolated interpreter (`.venv/bin/python app.py`) when the environment is not
activated. Local startup honors `FLASK_HOST` and `FLASK_PORT`; the example binds to
`127.0.0.1:5001`. Keep credentials in ignored `.env`, never in tracked `.env.example`.

### v0.7 memory, jobs, usage, and approval policy

- Optional memory dependency: `.venv/bin/python -m pip install -r requirements-memory.txt`.
  The MIT-licensed official [MemPalace repository](https://github.com/MemPalace/mempalace)
  is pinned to commit `741254421c31fb8e511c429133f5148d29bd4073` (3.11.0).
  We use its local SQLite lexical backend, not cloud embeddings, Chroma telemetry,
  automatic mining, or Claude hooks. No embedding model is downloaded by our adapter.
- Enable memory explicitly for an agent/scenario. Exact successful exchanges are stored
  locally, isolated by authenticated account, agent, and scenario digest (browser
  session only in explicit private-development mode). Retrieval is
  capped at three excerpts / 3,000 characters, plus four recent exchanges. Excerpts enter
  model prompts: local storage does NOT mean inference is offline. Treat recall as
  historical context, not factual verification. Disable stops future use/storage;
  Delete removes retained records and disables the policy. Database deletion is logical,
  not guaranteed forensic erasure; encrypted disks and backup retention are operator concerns.
- `POST /api/graph/execute` returns HTTP 202 and a server-generated `job_id`.
  `GET /api/jobs/<id>` provides persisted status, results, token usage, calculated cost,
  and outstanding reservations. The dashboard restores polling after reload.
  Queue state survives restart; jobs that were running become `interrupted`, never
  automatically replayed. This worker supports one Flask process, not multiple WSGI workers.
- Graph jobs and synchronous analyze/agent/chat operations have a 20,000-token / US$1
  ceiling. Set `PRICED_MODEL`, `MODEL_INPUT_USD_PER_MILLION`, and
  `MODEL_OUTPUT_USD_PER_MILLION` from verified provider pricing for your exact model.
  Missing/mismatched pricing blocks model calls. Provider tokens are measured; cost is
  rate-calculated, NOT an invoice. Conservative reservations precede calls, schema/text
  overhead is included, and uncertain billing retains the reservation. SDK retries are
  disabled so retries cannot bypass accounting. Direct CLI graph examples are not metered.
- `POST /api/jobs/<id>/cancel` is cooperative: in-flight API calls may still complete
  and be billed; subsequent calls are blocked. Queued jobs cancel immediately.
- `POST /api/connectors/local-export` with `{"source_job":"..."}` creates an immutable
  proposal; `POST /api/jobs/<proposal-id>/approve` authorizes a local ZIP only.
  Download via `GET /api/jobs/<proposal-id>/download` after success. Ownership,
  source file hashes, allowed paths, and ZIP receipts are checked. In authenticated
  mode only an admin can approve their own local export; reviewer export approval
  remains on hold pending a cross-account approval policy. No external connector is enabled.
- Runtime state lives in ignored `data/runtime/` (override with `APP_RUNTIME_DIR`).
  Run the dashboard using a dedicated OS account and keep it localhost-only.

### Scenario and execution contract

- Local environment configuration is loaded before service configuration is imported.
  Existing process environment variables take precedence over the repository `.env`.
- Company, industry, location, budget, timeline, and objectives must be supplied explicitly.
  The dashboard opens blank; incomplete or non-finite execution inputs return HTTP 400.
  Analyze and agent launch validate all required fields before starting, focusing the
  first invalid field. Scenario budget must be greater than zero (separate from API
  spending limits); timeline must be a positive whole number of days.
- Analyze produces objective-linked tasks with estimated budgets/durations, not completed work.
- **Actual source builds are separate and approval-gated:** use “Propose Python source
  build” to generate private `tool.py`, `test_tool.py`, and `README.md`. Source is
  syntax-checked, never executed locally. Tests remain **NOT run**. Separate approval
  prepares a hash-bound isolated runner request, not test execution.
  See [isolated runner design](docs/ISOLATED_RUNNER.md). Oracle deployment, remote
  execution, and verification of test evidence remain pending.
- Offline tests validate wiring with mocked providers; they do not establish live model
  access or successful execution of every agent. Graph execution always includes CTO
  review after CEO routing; engineering and other directors run only when selected for
  the supplied objectives. A failed model step stops the graph and prevents a complete
  report. Model access errors identify the configuration to correct without exposing keys.
- Graph launch sends `total_budget` and `target_days`; analyze uses `budget` and `timeline`.
- Narrow dashboards stack scenario setup, activity, and chat instead of hiding controls.
- The graph runs CTO review, selected directors, and only requested specialists. It persists
  JSON/Markdown deliverables with file sizes and SHA-256 hashes. Artifact generation is real;
  the business actions described inside the files remain proposals requiring review.
  Legacy template-based logo, wireframe, and architecture previews are excluded from v0.6
  bundles; the files contain the actual model output, not a preset design.
- Chat memory is isolated by account (or private-development browser session), agent, and scenario. Clearing chat clears server
  history too. Changing objectives or budget starts a new context.
- Legacy simulation/report-generation endpoints return HTTP 501. Historical report files
  are not evidence that actions were executed. Existing checkpoints from v0.5 should not
  be reused with the changed v0.6 workflow.
- SQLite checkpointing creates its parent directory, closes run-owned connections, and
  fails explicitly if its dependency is missing rather than silently using memory.
- Model calls have a 45-second per-call timeout and no hidden retries. The durable worker
  executes one graph job at a time; director dependencies remain sequential.

### Authorized VM testing (no deployment performed)

**Pending TODO — tester access is on hold at the owner's request.** Do not
provision an account, enable an email whitelist, issue tester credentials, or
grant remote access until explicitly authorized. Named-account admin/reviewer
roles and login/session protection are implemented; real tester provisioning and
cross-account export approval remain pending. No real tester account has been created.

### Private authentication and artifacts

**Pending TODO — login activation is on hold.** Private development currently
defaults to `ENABLE_AUTH=False` and accepts only localhost requests. Production
startup refuses disabled authentication. Enable login explicitly before any
authorized Oracle SSH-tunnel testing; no tunnel or remote access is configured.
There is no default
account, public registration, email whitelist, or API-key bypass. Provision only
your own admin account locally when ready; the CLI prompts for a password
(14–256 characters) without putting it in command arguments:

```bash
.venv/bin/python -m flask --app app create-account --email <your-admin-email> --role admin
.venv/bin/python -m flask --app app revoke-account --email <account-email>
```

Accounts use Werkzeug scrypt password hashes. Server-side session tokens are
stored hashed, expire after eight hours, and are invalidated by logout or account
revocation. Login attempts are limited to five per source address per 15 minutes.
REST endpoints require login; state changes require CSRF tokens. Socket.IO uses
same-origin validation, CSRF at connection, and account validity on each event.
Cookies are HttpOnly and SameSite=Strict; production requires authentication and
Secure cookies over HTTPS. Existing explicit `ENABLE_AUTH=False` local configuration
is not silently edited: change it before using accounts or sharing the service.

New artifacts live under ignored `data/artifacts/` (`APP_ARTIFACT_DIR` override),
outside the public static tree. Manifests carry the execution owner's identity.
`/api/artifacts/runs` lists only that owner's runs; download URLs check ownership,
allowed paths and hashes, force attachment downloads, and disable caching.
`/static/generated_outputs/...` is denied even for authenticated users. Old
ownerless artifacts and browser-owned history are preserved on disk but are not
automatically assigned to named accounts or exposed through authenticated downloads.
Browser scenario/job storage is account-namespaced; authenticated pages do not load
the old shared development storage keys.

The dashboard supports text chat only. Audio input/output code and audio
credentials are not part of the supported application.

The local dashboard is bound to `127.0.0.1:5001`; other devices cannot connect directly.
For an already-running VM instance, provision a separate SSH account/key for each tester,
allow SSH only from approved IPs, and keep dashboard port 5001 closed publicly:

```bash
ssh -N -L 5002:127.0.0.1:5001 <tester>@<vm-public-ip>
```

The tester opens `http://127.0.0.1:5002/`. Granting SSH access grants host privileges
according to that account's permissions: use least privilege and revoke test accounts
afterward. Use authentication in addition to the tunnel. This single-process
local setup is not a public-hosting approval; HTTPS, proxy configuration and
deployment validation are still required.

### Local regression checks (no paid model calls)

```bash
.venv/bin/python -m pytest -q tests/test_v06_wiring.py tests/test_smoke_dashboard_render.py
.venv/bin/python -m pytest -q tests/test_v07_runtime.py
.venv/bin/python -m pytest -q tests/test_auth_artifacts.py
node --check static/js/app.js
.venv/bin/python tools/smoke_dashboard_render.py
```

Tests use mocks and temporary artifact directories, not your API credentials. A passing
offline suite verifies wiring, not the accuracy of live model responses. See
[the execution roadmap](docs/REAL_WORLD_EXECUTION_ROADMAP.md) for the next safe upgrade stage.

### API entrypoint
`POST /api/graph/execute` is the canonical orchestration endpoint for running the multi-agent graph against the current scenario.

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
- **Live Feed** — single-page dashboard for company scenario creation and workflow execution
- **Agents Tab** — inspect agent roster and run domain specialists
- **Reports Tab** — view generated deliverables, recommendations, and budget summaries
- **Tasks Tab** — task breakdown from the current graph execution
- **Log Tab** — raw execution/log stream for progress tracking
- **Header Voice Control** — UI placeholder; the optional cloud voice integration
  remains unavailable and is not part of the validated runtime

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
- SocketIO `ai_chat_request/response` for live chat
- REST fallback via `/api/chat/message` and `/api/chat/clear`
- **Strategic Debate Mode** — devil's advocate persona toggle

---

## 🗂️ Artifact Pipeline

Every agent run persists files at:
```
data/artifacts/generated_outputs/
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
| Artifact Storage | Private filesystem (`data/artifacts/`) with owner-checked downloads |
| Testing | pytest · offline wiring and runtime regressions |

---

## 📦 Project Structure

```
ceo-agent-system/
├── app.py                          # Flask app — all routes + SocketIO
├── config.py                       # Settings, env, scenario defaults
├── services/
│   ├── artifact_service.py         # Artifact persistence + domain file generation
│   ├── agent_service.py
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
│   ├── js/auth.js                   # Same-origin CSRF request handling
│   └── generated_outputs/          # Agent artifact output (git-ignored)
├── templates/
├── utils/
│   └── validators.py               # Input validation + company_info allowlist
└── tests/                          # offline API, memory, jobs, and graph regressions
```

---

## 🧪 Testing

```bash
make test          # full pytest suite
make smoke         # fast dashboard render smoke check
make check         # format + lint + consistency + smoke + tests
```

---

## 🔄 Version History

| Version | Highlights |
|---------|-----------|
| **v0.8 (current)** | Named accounts · revocable sessions · CSRF and Socket.IO protection · private artifacts · legacy preset cleanup · broad lint repairs |
| **v0.7** | Opt-in MemPalace lexical memory · durable jobs · measured token usage and rate-calculated ceilings · approved local ZIP exports |
| **v0.6** | Scenario-specific planning · verified local artifacts · session isolation · responsive dashboard fixes |
| **v0.4** | REST-native orchestration via `/api/graph/execute` · simplified dashboard controls · graph-driven execution path |
| **v0.3** | CTO Agent (Tier 1) · real-time LLM chat · 3-panel dashboard · live feed cards · SocketIO · Prompt Expert (Node 0) · 6 Tier-2 directors · 7 Tier-3 specialists |
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
| [docs/STRIPE_INTEGRATION_TUTORIAL.md](docs/STRIPE_INTEGRATION_TUTORIAL.md) | Memberships, Apple Pay, signed webhooks, execution credits and sandbox testing |

---

## 🤝 Contributing

1. Fork the repo → create branch `feat/<name>`
2. Add tests for new agent behavior in `tests/`
3. Run `make check` — formatting, lint, consistency, smoke and tests must pass.
   Voice remains paused; its optional credential-dependent test may skip.
4. Open a PR

---

## 📄 License

[MIT](LICENSE) — built by [@0xwaya](https://github.com/0xwaya) / [Waya Labs](https://wayalabs.com)

---

**Built with** LangGraph · Flask · OpenAI · Python 3.10+  
**Domains** Branding · Web Dev · Legal · Finance · Security · Martech · Content · Campaigns · Social Media
