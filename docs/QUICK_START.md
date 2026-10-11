# 🚀 Quick Start Guide - Running the Multi-Agent System

## Main Entry Points

## Supported v0.8 local dashboard

Use the current dashboard for explicit scenario-driven, metered local artifact
execution. Keep the service localhost-only. Enable named authentication, use a
random persistent `SECRET_KEY` of at least 32 characters, and provision your own
admin with a hidden password prompt:

**Activation on hold:** leave local login disabled for now. The account setup
below is for the later, explicitly authorized SSH-tunnel testing stage.

```bash
.venv/bin/python -m flask --app app create-account --email <your-admin-email> --role admin
.venv/bin/python app.py
make check PYTHON=.venv/bin/python
```

Open `http://127.0.0.1:5001/login`. New artifacts are private in `data/artifacts/`;
use the authenticated dashboard download links, not static file URLs.
Tester provisioning and remote access are on hold. Dashboard conversations are
text-only; audio input and output are not part of this application.

**Legacy CLI reference below:** these compatibility entry points do not share
the dashboard's authentication, metering or truthful execution contract, and
some retain historical preset scenarios. They are not recommended for live
testing or as proof that business actions were executed.

---

## 1. 💼 CFO Multi-Agent Orchestrator

**Automated strategic execution with coordinated expert agents**

```bash
python3 cfo_agent.py
```

**What it does:**
- Analyzes strategic objectives
- Creates specialized agents (Legal, Branding, Web Dev, etc.)
- Coordinates multi-agent workflows
- Manages budgets and timelines
- Generates executive summaries

**Use case:** Complete strategic plans with multiple coordinated agents

---

## 2. 💬 Interactive Chat Interface

**Chat with AI experts in real-time**

```bash
python3 interactive_chat.py
```

**What it does:**
- Interactive conversation with specialized agents
- Invoke agents by name (@branding, @web, @legal, etc.)
- Multi-agent roundtable discussions
- Session memory and history

**Use case:** Exploratory conversations, Q&A with specific experts

---

## 3. 📊 Marketing Agent (Original)

**Focused marketing strategy for countertop businesses**

```bash
python3 agent.py
```

**What it does:**
- Market research and competitor analysis
- DBA name recommendations
- Brand positioning
- Marketing channel strategy
- Budget planning

**Use case:** Marketing-focused strategic planning

---

## 4. 🌐 Web Application (Dashboard)

**Interactive web dashboard for all agents**

```bash
python3 app.py
```

Then visit: **http://localhost:5001**

**What it does:**
- Web-based interface for all agents
- Real-time WebSocket updates
- Visual dashboards and charts
- Execute agents via API endpoints
- Persist generated execution artifacts to private `data/artifacts/`
- Show generated files with previews in the agent workspace panel
- Debug console

**Use case:** Private local testing; not a public production deployment

---

## 🔧 Utility Scripts

### Check Dependencies
```bash
python3 tools/check_dependencies.py
```

### Setup Encrypted Environment
```bash
# Initial setup
python3 tools/encrypted_env_demo.py setup

# Encrypt your .env file
python3 tools/encrypted_env_demo.py encrypt

# Decrypt for use
python3 tools/encrypted_env_demo.py decrypt

# Check status
python3 tools/encrypted_env_demo.py show
```

### Shell Scripts
```bash
# Start web server
tools/start_web.sh

# Quick agent test
tools/test_agents_quick.sh

# Test all buttons (web interface)
tools/test_all_buttons.sh

# Verify all agents are working
tools/verify_all_agents.sh
```

---

## 📁 Project Structure Reference

```
langraph/
├── cfo_agent.py              # ✅ CFO orchestrator (wrapper)
├── interactive_chat.py        # ✅ Interactive chat (wrapper)
├── agent.py                   # ✅ Marketing agent
├── app.py                     # ✅ Web application
│
├── agents/                    # Core agent implementations
│   ├── cfo_agent.py          # Actual CFO agent code
│   ├── specialized_agents.py # All specialized agents
│   ├── base_agent.py         # Abstract base class
│   └── agent_guard_rails.py  # Safety & validation
│
├── services/                  # Business logic layer
├── utils/                     # Shared utilities
├── tools/                     # Scripts & automation
└── templates/                 # Web UI templates
```

---

## 💡 Quick Examples

### Example 1: Run CFO for Complete Strategy
```bash
# Just run it - uses default SURFACECRAFT STUDIO example
python3 cfo_agent.py

# Watch as it:
# - Analyzes objectives
# - Creates 6 specialized agents
# - Coordinates execution
# - Generates executive summary
```

### Example 2: Chat with Specific Agent
```bash
python3 interactive_chat.py

# Then in the chat:
You: @branding I need a logo for SURFACECRAFT STUDIO
You: @web Can you build a website with AR countertop visualization?
You: @legal Help me file a DBA in Ohio
```

### Example 3: Web Dashboard
```bash
python3 app.py

# Visit http://localhost:5001
# - Click "Analyze Strategy" for CFO analysis
# - Click individual agent buttons to deploy them
# - View real-time progress
# - Open "Run & View Output" for any agent to see generated files
# - Review saved artifacts through owner-checked dashboard download links
```

### Artifact Review Flow

1. Open `/admin` and run an agent via **Run & View Output**
2. Inspect **Generated Files** in the workspace panel (preview + open links)
3. Files are private in `data/artifacts/generated_outputs/<agent>/<run_id>_<company>/`;
   use authenticated download links once login is activated.

Generated bundle includes:
- `metadata.json` (run context)
- `result.json` (full structured agent result)
- `summary.md` (execution summary)
- agent-specific files (for example branding SVG concepts and avatar exports)

---

## 🔍 Troubleshooting

### "Module not found" errors
```bash
# Make sure you're in the project root
cd /Users/pc/code/langraph

# Verify Python path
python3 -c "import sys; print(sys.path)"

# Test imports
python3 -c "from agents import AgentFactory; print('✓ OK')"
```

### "Can't open file" errors
```bash
# The files moved during reorganization
# Use these instead:

# OLD                          # NEW
python3 base_agent.py    →     python3 -m agents.base_agent
python3 specialized_agents.py → python3 -m agents.specialized_agents

# Or use the wrapper scripts:
python3 cfo_agent.py           # ✓ Works from root
python3 interactive_chat.py    # ✓ Works from root
python3 agent.py               # ✓ Works from root
python3 app.py                 # ✓ Works from root
```

### Missing dependencies
```bash
# Check what's missing
python3 tools/check_dependencies.py

# Install everything
pip install -r requirements.txt

# Install cryptography for encrypted env
pip install cryptography
```

---

## 🎯 Common Workflows

### Workflow 1: Development Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup environment
python3 tools/encrypted_env_demo.py setup
nano .env  # Add your API keys

# 3. Encrypt environment
python3 tools/encrypted_env_demo.py encrypt

# 4. Test the system
python3 tools/check_dependencies.py
python3 cfo_agent.py
```

### Workflow 2: Daily Development
```bash
# Start interactive chat for experiments
python3 interactive_chat.py

# Or run web app for visual interface
python3 app.py
```

### Workflow 3: Production Deployment
```bash
# Decrypt environment on server
python3 tools/encrypted_env_demo.py decrypt

# Start web server
python3 app.py

# Or use production server
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

---

## 🆘 Need Help

1. **Read the docs:**
   - [README.md](README.md) - Project overview
   - [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
   - [ENCRYPTED_ENV_TUTORIAL.md](ENCRYPTED_ENV_TUTORIAL.md) - API setup guide
   - [REORGANIZATION_SUMMARY.md](REORGANIZATION_SUMMARY.md) - Recent changes

2. **Check the code:**
   - Agent implementations: `agents/`
   - API endpoints: `app.py`
   - Configuration: `config.py`

3. **Test components:**
   ```bash
   python3 tools/check_dependencies.py
   python3 -c "from agents import AgentFactory; print('✓ Imports OK')"
   ```

---

**Happy coding! 🚀**
