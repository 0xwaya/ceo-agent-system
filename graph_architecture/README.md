# Hierarchical Graph-Based Multi-Agent Architecture — v0.3

> **v0.3** introduces a full 3-tier LangGraph redesign: LLM-driven dispatch, a Prompt Expert agent, 6 Tier-2 domain directors, and 7 Tier-3 execution specialists.

## Overview

This directory contains the implementation of a **hierarchical, graph-based multi-agent system** using LangGraph with:

- **Prompt Expert** (Node 0): Parses raw user input into structured routing signals before CEO sees it
- **CEO Agent** (Tier 1): LLM-driven root orchestrator — builds a `dispatch_plan` and loops through it
- **Domain Directors** (Tier 2): CFO · Engineer · Researcher · Legal · Martech · Security — each an LLM-backed subgraph
- **Execution Specialists** (Tier 3): UX/UI · WebDev · SoftEng · Branding · Content · Campaign · SocialMedia — orchestrated inside their Tier-2 parent

## Architecture Principles

### 1. Hierarchical Structure
```
Prompt Expert (Node 0 — intent parser)
    └─► CEO (Tier 1 — strategic orchestrator)
            ├── CFO            (Tier 2 — Finance)
            ├── Engineer       (Tier 2 — Engineering)
            │       ├── UX/UI Design  (Tier 3)
            │       ├── Web Dev       (Tier 3)
            │       └── Software Eng  (Tier 3)
            ├── Researcher     (Tier 2 — Research)
            ├── Legal          (Tier 2 — Compliance)
            ├── Martech        (Tier 2 — Marketing)
            │       ├── Branding      (Tier 3)
            │       ├── Content       (Tier 3)
            │       ├── Campaign      (Tier 3)
            │       └── Social Media  (Tier 3)
            └── Security       (Tier 2 — Audit)
```

### 2. Communication Model
- **LLM-driven dispatch**: CEO's `dispatch_plan` list is built from Prompt Expert output, not hard-coded
- **Conditional dispatch loop**: `dispatch_orchestrator` iterates `dispatch_plan[current_dispatch_index]` — only required agents run
- **Summaries upstream**: Tier-2/3 agents push executive summaries to `agent_outputs`; CEO never sees raw internals
- **Tier-3 hints**: Prompt Expert sets `needs_ux_design`, `needs_branding`, etc. — Tier-2 subgraphs read these to activate specialists
- **Explicit hierarchy**: No agent can bypass the chain

### 3. Persistence & Checkpointing
- **Checkpoint at every node**: State saved at key graph transitions
- **Resumable workflows**: Long-running tasks can pause/resume
- **Failure recovery**: Restore from last checkpoint after crashes
- **Audit trail**: Every transition logged for debugging

### 4. Role-Based Guards
- **Entry guards**: Validate requester role before subgraph entry
- **Scope validation**: Ensure tasks match agent domain
- **Authorization checks**: Enforce approval chains for sensitive actions
- **Violation logging**: Track and reject unauthorized access

### 5. Human-in-the-Loop
- **Approval nodes**: User confirmation required for critical decisions
- **Budget approvals**: Any expenditure requires user consent
- **Risk escalation**: High-risk actions flagged for review
- **Interrupt mechanism**: User can pause/modify execution

## Directory Structure

```
graph_architecture/
├── README.md                    # This file
├── IMPLEMENTATION_GUIDE.md      # Implementation guide
├── SUMMARY.md                   # Feature summary
├── TUTORIAL.py                  # Interactive tutorials
├── requirements.txt             # Dependencies
│
├── schemas.py                   # All Pydantic models, TypedDicts, enums (v0.3)
├── prompt_expert.py             # Node 0 — intent parser + routing decision builder
├── llm_nodes.py                 # All LLM-backed node functions (Tier 1–3)
├── tools.py                     # Graph-wired tool registry with role enforcement
├── checkpointer.py              # Persistence layer (SQLite / PostgreSQL)
├── guards.py                    # RBAC: Domain enum, DOMAIN_PERMISSIONS, entry guards
├── approval_nodes.py            # Human-in-the-loop approval nodes
├── main_graph.py                # Master orchestration graph (v0.3 dispatch loop)
│
└── subgraphs/
    ├── cfo_subgraph.py          # CFO — Finance domain
    ├── engineer_subgraph.py     # Engineer — with Tier-3 UX/WebDev/SoftEng routing
    ├── researcher_subgraph.py   # Researcher — market & competitive analysis
    ├── legal_subgraph.py        # Legal — compliance & regulatory  [NEW v0.3]
    ├── martech_subgraph.py      # Martech — strategy + Tier-3 specialists [NEW v0.3]
    └── security_subgraph.py     # Security — threat model & audit  [NEW v0.3]
```

## Key Files

### schemas.py
Defines JSON schemas for:
- Shared state structure
- Message queue format
- Checkpoint format
- Agent communication protocol

### checkpointer.py
Implements persistence using LangGraph's checkpoint API:
- SqliteSaver for local development
- PostgreSQL adapter for production
- Checkpoint metadata and recovery

### guards.py
Role-based access control:
- `validate_agent_role()`
- `check_authorization()`
- `enforce_hierarchy()`
- `log_violations()`

### main_graph.py
Master orchestration graph:
- CEO as root node
- Conditional routing to subgraphs
- Summary consolidation
- Terminate/re-route logic

## Design Patterns

### 1. Subgraph Pattern
Each specialized domain is a complete subgraph:
```python
cfo_subgraph = StateGraph(CFOSubgraphState)
cfo_subgraph.add_node("analyze_budget", analyze_budget_node)
cfo_subgraph.add_node("validate_costs", validate_costs_node)
cfo_subgraph.add_conditional_edges("analyze_budget", route_cfo_workflow)

# CEO graph includes CFO as a subgraph node
ceo_graph.add_node("cfo", cfo_subgraph.compile())
```

### 2. Message Queue Pattern
Asynchronous communication between agents:
```python
{
  "from": "engineer",
  "to": "researcher",
  "type": "spec_request",
  "payload": {...},
  "timestamp": "2026-02-13T10:00:00Z",
  "priority": "high"
}
```

### 3. Checkpoint Pattern
State saved at every transition:
```python
{
  "node_id": "cfo_analyze_budget",
  "agent_role": "cfo",
  "shared_state_snapshot": {...},
  "pending_messages": [...],
  "tool_context": {...},
  "timestamp": "2026-02-13T10:00:00Z"
}
```

### 4. Guard Pattern
Entry validation for every subgraph:
```python
def cfo_entry_guard(state):
    if state["requester_role"] != "ceo":
        raise GuardRailViolation("Only CEO can invoke CFO")
    return state
```

## Usage

### Basic Execution (v0.3)
```python
from graph_architecture.main_graph import execute_multi_agent_system

result = execute_multi_agent_system(
    company_name="Acme Corp",
    industry="Software & Technology",
    location="San Francisco, CA",
    total_budget=100_000.0,
    target_days=90,
    objectives=["Launch SaaS platform", "Establish market presence"],
    # Free-text command — drives Prompt Expert → CEO dispatch_plan
    user_raw_input="Build a SaaS product with security audit and marketing strategy.",
    use_checkpointing=True,
)
print(result["final_summary"])
```

### Build Graph Directly
```python
from graph_architecture.main_graph import build_master_graph
from graph_architecture.checkpointer import create_checkpointer

checkpointer = create_checkpointer("sqlite", "./checkpoints.db")
graph = build_master_graph(checkpointer=checkpointer)
config = {"configurable": {"thread_id": "session-123"}}
result = graph.invoke(initial_state, config=config)
```

### Resume from Checkpoint
```python
# Get state at specific checkpoint
state = graph.get_state(config)
print(f"Current node: {state.next}")
print(f"Checkpoint: {state.checkpoint}")

# Continue from last checkpoint
result = graph.invoke(None, config=config)
```

### Human-in-the-Loop Approval
```python
# Graph pauses at approval node
state = graph.get_state(config)
if state.next == "approval_required":
    # User reviews pending action
    approval = {"approved": True, "notes": "Looks good"}

    # Update state and continue
    graph.update_state(config, approval, as_node="approval_required")
    result = graph.invoke(None, config=config)
```

## Multi-Tenant Support

Each tenant gets isolated execution:
```python
config = {
    "configurable": {
        "thread_id": f"tenant-{tenant_id}-session-{session_id}",
        "checkpoint_ns": tenant_id
    }
}
```

## Monitoring & Debugging

### View Execution Flow
```python
# Get full execution history
history = graph.get_state_history(config)
for state in history:
    print(f"Node: {state.checkpoint['node_id']}")
    print(f"Time: {state.checkpoint['timestamp']}")
    print(f"Messages: {len(state.values['pending_messages'])}")
```

### Replay Execution
```python
# Time-travel to specific checkpoint
checkpoint_id = "checkpoint-42"
state = graph.get_state(config, checkpoint_id=checkpoint_id)
```

## Next Steps

1. **Implement specialized tools** for each subgraph
2. **Add observability** with telemetry and tracing
3. **Scale horizontally** with distributed checkpointing
4. **Add versioning** for graph schema evolution
5. **Implement circuit breakers** for fault tolerance
