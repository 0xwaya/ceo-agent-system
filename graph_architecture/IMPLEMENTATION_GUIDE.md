# Hierarchical Graph-Based Multi-Agent System — v0.3 Implementation Guide

## 🎯 Overview

This system implements a **3-tier LLM-driven hierarchical multi-agent architecture** using LangGraph with:

- ✅ **Prompt Expert Agent** — Node 0, LLM-backed intent parser converts raw user input to structured routing signals
- ✅ **CEO as LLM orchestrator** — Builds `dispatch_plan` from Prompt Expert output; never hard-codes agents
- ✅ **Conditional dispatch loop** — `dispatch_orchestrator` iterates plan, only required Tier-2 agents run
- ✅ **6 Tier-2 domain directors** — CFO, Engineer, Researcher, Legal, Martech, Security (each LLM-backed)
- ✅ **7 Tier-3 execution specialists** — UX/UI, WebDev, SoftEng, Branding, Content, Campaign, SocialMedia
- ✅ **Centralised LLM nodes** — `llm_nodes.py` owns all LLM calls; `TIER2_NODE_MAP` / `TIER3_NODE_MAP` registries
- ✅ **Role-gated tool registry** — `tools.py` enforces domain permissions before any tool executes
- ✅ **Strict role boundaries** — Role-based guards, RBAC domain permissions
- ✅ **Checkpoint persistence** — Resume from any point, crash recovery
- ✅ **Human-in-the-loop** — Approval gate after consolidation

---

## 📁 Directory Structure

```
graph_architecture/
├── README.md                  # Architecture overview
├── IMPLEMENTATION_GUIDE.md    # This file
├── SUMMARY.md                 # Feature summary & changelog
├── TUTORIAL.py                # Interactive tutorials
│
├── schemas.py                 # All Pydantic models, TypedDicts, enums
├── prompt_expert.py           # Node 0 — LLM intent parser + keyword fallback
├── llm_nodes.py               # All LLM node functions + TIER2/TIER3_NODE_MAP
├── tools.py                   # Role-gated tool registry
├── checkpointer.py            # Persistence layer
├── guards.py                  # RBAC guards + domain permissions
├── approval_nodes.py          # Human-in-the-loop workflow
├── main_graph.py              # Master dispatch-loop graph
│
└── subgraphs/
    ├── cfo_subgraph.py          # Finance domain
    ├── engineer_subgraph.py     # Engineering + Tier-3 hints
    ├── researcher_subgraph.py   # Research & analysis
    ├── legal_subgraph.py        # Compliance & regulatory [NEW v0.3]
    ├── martech_subgraph.py      # Marketing + Branding/Content/Campaign/Social [NEW v0.3]
    └── security_subgraph.py     # Security audit & threat model [NEW v0.3]
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install langgraph langgraph-checkpoint-sqlite pydantic
```

### 2. Basic Execution (v0.3)

```python
from graph_architecture.main_graph import execute_multi_agent_system

result = execute_multi_agent_system(
    company_name="Acme Corp",
    industry="Technology",
    location="San Francisco, CA",
    total_budget=100000.0,
    target_days=90,
    objectives=[
        "Launch SaaS platform",
        "Establish market presence",
        "Build sales pipeline"
    ],
    # Natural-language command — Prompt Expert parses this into routing signals
    user_raw_input="Build a SaaS product with focus on security and a full marketing launch.",
    use_checkpointing=True
)

print(result["final_summary"])
```

### 3. Run Tutorial

```bash
# Run all tutorials
python3 graph_architecture/TUTORIAL.py

# Run specific tutorial
python3 graph_architecture/TUTORIAL.py 1  # Basic execution
python3 graph_architecture/TUTORIAL.py 4  # Approvals
```

---

## 🏗️ Architecture Deep Dive

### Hierarchical Structure

```
┌────────────────────────────┐
│       CEO AGENT            │ ← Root orchestrator
│  (Strategic decisions)     │
└──────────────┬─────────────┘
               │
       ┌───────┴────────┬────────────┐
       ▼                ▼            ▼
┌─────────────┐  ┌─────────────┐  ┌──────────────┐
│ CFO SUBGRAPH│  │ ENGINEER    │  │  RESEARCHER  │
│  (Finance)  │  │  SUBGRAPH   │  │   SUBGRAPH   │
└─────────────┘  └─────────────┘  └──────────────┘
       │                │                 │
       └────────────────┴─────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │  CEO SUMMARIES   │ ← Only summaries flow up
              └──────────────────┘
```

### Communication Rules

1. **CEO** can communicate with any agent (downward delegation)
2. **Subordinates** send summaries to CEO (upward reporting)
3. **Peers** can coordinate laterally (Engineer ↔ Researcher)
4. **Raw data** stays within subgraphs (never sent to CEO)
5. **All communication** logged for audit trail

---

## 🔐 Security & Governance

### Role-Based Guards

```python
from graph_architecture.guards import SubgraphEntryGuard, AgentRole, Domain

# CFO subgraph entry guard
cfo_guard = SubgraphEntryGuard(
    allowed_roles={AgentRole.CEO},  # Only CEO can invoke
    domain=Domain.FINANCE
)

# Validate entry
state = cfo_guard.validate_entry(state, requester_role=AgentRole.CEO)
```

### Authorization Levels (Updated v0.3)

| Role       | Tier | Level        | Can Do |
|------------|------|--------------|--------|
| CEO        | 1    | EXECUTIVE    | Strategic decisions, build dispatch_plan, delegate to all Tier-2 |
| CFO        | 2    | SUPERVISORY  | Budget analysis, compliance, financial reporting |
| Security   | 2    | SUPERVISORY  | Threat modelling, audit, compliance gap analysis |
| Engineer   | 2    | OPERATIONAL  | Technical architecture, delegates to UX/WebDev/SoftEng |
| Researcher | 2    | OPERATIONAL  | Market research, competitor analysis |
| Legal      | 2    | OPERATIONAL  | Regulatory compliance, contract review |
| Martech    | 2    | OPERATIONAL  | Marketing strategy, delegates to Branding/Content/Campaign/Social |
| UX/UI      | 3    | OPERATIONAL  | Design systems, wireframes, accessibility |
| WebDev     | 3    | OPERATIONAL  | Frontend, React, landing pages |
| SoftEng    | 3    | OPERATIONAL  | Code review, software architecture |
| Branding   | 3    | OPERATIONAL  | Brand identity, visual guidelines |
| Content    | 3    | OPERATIONAL  | Blog, copy, editorial |
| Campaign   | 3    | OPERATIONAL  | Paid campaigns, funnels |
| SocialMedia| 3    | OPERATIONAL  | Social channels, engagement |

### Guard Rail Violations

Violations are **automatically logged** and **execution blocked**:

```python
{
    "timestamp": "2026-02-13T10:00:00Z",
    "agent_role": "engineer",
    "violation_type": "unauthorized_access",
    "severity": "critical",
    "message": "Engineer attempted to access finance domain"
}
```

---

## 💾 Checkpointing & Persistence

### Enable Checkpointing

```python
from graph_architecture.checkpointer import create_checkpointer
from graph_architecture.main_graph import build_master_graph

# Create SQLite checkpointer
checkpointer = create_checkpointer("sqlite", "./data/checkpoints.sqlite")

# Build graph with checkpointing
graph = build_master_graph(checkpointer=checkpointer)

# Execute with thread ID
config = {"configurable": {"thread_id": "session-123"}}
result = graph.invoke(initial_state, config=config)
```

### Resume from Checkpoint

```python
from graph_architecture.checkpointer import CheckpointRecovery

# Get latest state
state = CheckpointRecovery.get_latest_checkpoint(graph, "session-123")

# Resume execution
result = CheckpointRecovery.resume_from_checkpoint(graph, "session-123")
```

### Production Deployment (PostgreSQL)

```python
checkpointer = create_checkpointer(
    "postgres",
    "postgresql://user:pass@localhost:5432/checkpoints"
)
```

---

## ✋ Human-in-the-Loop Approvals

### Add Approval Checkpoint

```python
from graph_architecture.approval_nodes import (
    create_budget_approval_request,
    RiskLevel
)

# Create approval request
approval = create_budget_approval_request(
    action="Purchase enterprise software license",
    cost=10000.0,
    rationale="Required for team scaling",
    risk_level=RiskLevel.MEDIUM,
    auto_decline_hours=48  # Auto-decline if not approved in 48h
)

# Add to state
state["pending_approvals"].append(approval)
```

### Graph Interrupts

Graph execution **pauses at approval nodes**:

```python
# Graph will interrupt at "approval" node
graph = build_master_graph(
    checkpointer=checkpointer,
    interrupt_before=["approval"]  # Pause here
)

# Execute - will stop at approval
result = graph.invoke(state, config=config)

# Check if waiting for approval
current_state = graph.get_state(config)
if current_state.next == "approval":
    print("Waiting for user approval")

    # User provides approval
    approval_response = {
        "request_id": "approval-xyz",
        "approved": True,
        "notes": "Approved with conditions"
    }

    # Update state and continue
    graph.update_state(config, {"approval_response": approval_response})
    result = graph.invoke(None, config=config)  # Resume
```

---

## 🏢 Multi-Tenant Support

### Isolated Execution

```python
from graph_architecture.checkpointer import MultiTenantCheckpointer

mt_checkpointer = MultiTenantCheckpointer(base_checkpointer)

# Tenant 1
config_1 = mt_checkpointer.create_tenant_config(
    tenant_id="customer-001",
    session_id="session-abc"
)
result_1 = graph.invoke(state_1, config=config_1)

# Tenant 2 (completely isolated)
config_2 = mt_checkpointer.create_tenant_config(
    tenant_id="customer-002",
    session_id="session-xyz"
)
result_2 = graph.invoke(state_2, config=config_2)
```

### Tenant Data Management

```python
# List sessions for tenant
sessions = mt_checkpointer.list_tenant_sessions(graph, "customer-001")

# Delete tenant data (GDPR compliance)
mt_checkpointer.delete_tenant_data("customer-001")
```

---

## 🔍 Debugging & Observability

### Execution History

```python
# Get full execution history
history = graph.get_state_history(config)

for state_snapshot in history:
    print(f"Node: {state_snapshot.next}")
    print(f"Phase: {state_snapshot.values['current_phase']}")
    print(f"Budget: ${state_snapshot.values['budget_remaining']}")
    print("---")
```

### Export Checkpoint

```python
from graph_architecture.checkpointer import export_checkpoint

# Export to JSON
export_checkpoint(
    graph,
    thread_id="session-123",
    output_file="./debug_checkpoint.json"
)
```

### Replay to Specific Checkpoint

```python
# Time-travel to checkpoint
state = CheckpointRecovery.replay_to_checkpoint(
    graph,
    thread_id="session-123",
    checkpoint_id="ckpt-abc123"
)
```

---

## 📊 Message Queue Pattern

### Inter-Agent Messages

```python
from graph_architecture.schemas import create_message, MessageType, AgentRole

# Engineer requests spec from Researcher
message = create_message(
    from_agent=AgentRole.ENGINEER,
    to_agent=AgentRole.RESEARCHER,
    message_type=MessageType.SPEC_REQUEST,
    payload={
        "feature": "AR visualization",
        "requirements": ["WebGL support", "mobile-friendly"]
    },
    priority=TaskPriority.HIGH,
    correlation_id="req-12345"
)

# Add to message queue
state["pending_messages"].append(message)
```

### Summary Messages (to CEO)

```python
from graph_architecture.schemas import SummaryMessage, TaskStatus

# CFO sends summary to CEO
summary = SummaryMessage(
    agent_role=AgentRole.CFO,
    task_id="financial_analysis",
    status=TaskStatus.COMPLETED,
    key_findings=[
        "Budget utilization at 65%",
        "Projected completion on schedule"
    ],
    risks=[],
    recommendations=["Continue current allocation"],
    budget_used=32500.0,
    next_steps=["Monitor Q2 spending"],
    raw_data_available=True  # Raw data exists but not sent
)

state["agent_outputs"].append({
    "agent": "cfo",
    "summary": summary.model_dump()
})
```

---

## 🧪 Testing

### Unit Test Subgraph

```python
from graph_architecture.subgraphs.cfo_subgraph import build_cfo_subgraph
from graph_architecture.schemas import create_initial_shared_state

# Create test state
state = create_initial_shared_state(
    company_name="Test Corp",
    industry="Test",
    location="Test, CA",
    total_budget=10000,
    target_days=30,
    objectives=["Test objective"]
)

# Run CFO subgraph
cfo_graph = build_cfo_subgraph()
result = cfo_graph.invoke(state)

# Assertions
assert result["executive_summary"] != ""
assert "budget_remaining" in result
```

### Integration Test

```python
def test_full_workflow():
    result = execute_multi_agent_system(
        company_name="Integration Test",
        industry="SaaS",
        location="NYC",
        total_budget=50000,
        target_days=60,
        objectives=["Test goal"],
        use_checkpointing=False
    )

    assert result["current_phase"] == "complete"
    assert len(result["completed_phases"]) > 0
    assert result["final_summary"] != ""
```

---

## 🔄 Adding New Subgraphs

### 1. Define Subgraph State

```python
class EngineerSubgraphState(TypedDict):
    # Inherits SharedState fields
    code_files: Annotated[List[Dict], operator.add]
    test_results: Annotated[List[Dict], operator.add]
    implementation_summary: str
```

### 2. Create Nodes

```python
def engineer_code_generation_node(state: EngineerSubgraphState):
    # Generate code
    return {"code_files": [{"file": "main.py", "content": "..."}]}

def engineer_testing_node(state: EngineerSubgraphState):
    # Run tests
    return {"test_results": [{"test": "unit", "passed": True}]}
```

### 3. Build Subgraph

```python
def build_engineer_subgraph():
    subgraph = StateGraph(EngineerSubgraphState)

    subgraph.add_node("generate", engineer_code_generation_node)
    subgraph.add_node("test", engineer_testing_node)

    subgraph.add_edge(START, "generate")
    subgraph.add_edge("generate", "test")
    subgraph.add_edge("test", END)

    return subgraph.compile()
```

### 4. Add to Main Graph

```python
def build_master_graph(checkpointer=None):
    graph = StateGraph(CEOState)

    # Add subgraph as node
    engineer_subgraph = build_engineer_subgraph()
    graph.add_node("engineer_subgraph", engineer_subgraph)

    # Add routing
    graph.add_edge("route_subgraph", "engineer_subgraph")
    graph.add_edge("engineer_subgraph", "consolidate")

    return graph.compile(checkpointer=checkpointer)
```

---

## 📈 Performance Optimization

### Parallel Subgraph Execution

For independent subgraphs, execute in parallel:

```python
from concurrent.futures import ThreadPoolExecutor

def execute_parallel_subgraphs(state):
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit subgraphs
        cfo_future = executor.submit(cfo_subgraph.invoke, state)
        engineer_future = executor.submit(engineer_subgraph.invoke, state)
        researcher_future = executor.submit(researcher_subgraph.invoke, state)

        # Collect results
        results = {
            "cfo": cfo_future.result(),
            "engineer": engineer_future.result(),
            "researcher": researcher_future.result()
        }

    return results
```

### Checkpoint Pruning

Limit checkpoint storage:

```python
# Keep only last 10 checkpoints per thread
def prune_checkpoints(thread_id, keep_last=10):
    history = get_execution_history(graph, thread_id, limit=100)

    if len(history) > keep_last:
        # Delete old checkpoints
        for old_checkpoint in history[keep_last:]:
            delete_checkpoint(old_checkpoint["checkpoint_id"])
```

---

## 🎓 Best Practices

### 1. State Management
- ✅ Use immutable state (Pydantic models)
- ✅ Keep state minimal (only what's needed)
- ✅ Use reducers for list fields (`operator.add`)

### 2. Error Handling
- ✅ Validate all inputs
- ✅ Log exceptions to state
- ✅ Provide recovery mechanisms

### 3. Security
- ✅ Enforce role boundaries
- ✅ Validate all message sources
- ✅ Require approvals for sensitive actions
- ✅ Audit all state transitions

### 4. Performance
- ✅ Use checkpointing for long workflows
- ✅ Parallelize independent subgraphs
- ✅ Prune old checkpoints
- ✅ Index frequently queried state fields

### 5. Testing
- ✅ Unit test each node
- ✅ Integration test full workflows
- ✅ Test guard rail violations
- ✅ Test checkpoint recovery

---

## 🚧 Roadmap

- [ ] Complete Engineer subgraph implementation
- [ ] Complete Researcher subgraph implementation
- [ ] Add Legal agent subgraph
- [ ] Implement circuit breakers for fault tolerance
- [ ] Add distributed checkpointing (Redis)
- [ ] Implement graph versioning
- [ ] Add telemetry and observability (OpenTelemetry)
- [ ] Create web UI for approval workflows
- [ ] Add LLM integration for agent decision-making
- [ ] Implement cost tracking per agent

---

## 📚 Additional Resources

- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **Checkpointing Guide**: https://langchain-ai.github.io/langgraph/how-tos/persistence/
- **Subgraphs**: https://langchain-ai.github.io/langgraph/how-tos/subgraph/
- **Human-in-the-Loop**: https://langchain-ai.github.io/langgraph/how-tos/human-in-the-loop/

---

## 🤝 Contributing

See [CONTRIBUTING.md](../docs/CONTRIBUTING.md) for guidelines.

---

## 📄 License

See [LICENSE](../LICENSE) for details.

---

**Built with LangGraph** | **Production-Ready** | **Scalable** | **Secure**
