# Hierarchical Graph-Based Multi-Agent Architecture

## Overview

This directory contains the implementation of a **hierarchical, graph-based multi-agent system** using LangGraph with:

- **CEO Agent**: Root orchestrator managing global objectives
- **CFO Subgraph**: Finance domain with budget analysis and compliance
- **Engineer Subgraph**: Code generation, refactoring, and testing
- **Researcher Subgraph**: Discovery and specification research

## Architecture Principles

### 1. Hierarchical Structure
```
CEO (Root Node)
├── CFO Subgraph (Finance Domain)
├── Engineer Subgraph (Code + Systems)
└── Researcher Subgraph (Discovery & Specs)
```

### 2. Communication Model
- **Asynchronous message queues** between agents
- **Summaries upstream**: Subordinates send executive summaries to CEO
- **Raw data stays local**: CFO processes data internally, returns insights only
- **Explicit routing**: No agent can bypass hierarchy

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
├── schemas.py                   # JSON schemas for state and messages
├── shared_state.py              # Global shared state definition
├── checkpointer.py              # Persistence layer implementation
├── guards.py                    # Role-based guard rails
├── nodes/
│   ├── ceo_nodes.py            # CEO orchestrator nodes
│   ├── cfo_nodes.py            # CFO subgraph nodes
│   ├── engineer_nodes.py       # Engineer subgraph nodes
│   └── researcher_nodes.py     # Researcher subgraph nodes
├── subgraphs/
│   ├── cfo_subgraph.py         # CFO workflow graph
│   ├── engineer_subgraph.py    # Engineer workflow graph
│   └── researcher_subgraph.py  # Researcher workflow graph
├── routing.py                   # Conditional edge routing logic
├── approval_nodes.py            # Human-in-the-loop approval nodes
└── main_graph.py               # Master graph composition

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

### Basic Execution
```python
from graph_architecture.main_graph import build_master_graph
from graph_architecture.checkpointer import create_checkpointer

# Create graph with checkpointing
checkpointer = create_checkpointer("sqlite", "./checkpoints.db")
graph = build_master_graph(checkpointer=checkpointer)

# Execute with thread for resumability
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
