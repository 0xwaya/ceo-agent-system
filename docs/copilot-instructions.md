# Copilot Instructions

## Project Overview

This is a LangGraph project. LangGraph is a library for building stateful, multi-actor applications with LLMs.

## Architecture

### Key Components

- **Graph Definition**: Define state machines with nodes (functions) and edges (transitions)
- **State Management**: Use TypedDict or Pydantic models for state schema
- **Checkpointing**: Persist graph state for resumability and time-travel debugging

### Core Patterns

- Define graphs using `StateGraph` with typed state
- Nodes are functions that take state and return updates
- Use `add_node()`, `add_edge()`, and `add_conditional_edges()` to build graphs
- Compile graphs with `.compile()` before execution

## Development Workflow

### Setup

```bash
# Install dependencies
pip install langgraph langchain-core

# For checkpointing support
pip install langgraph-checkpoint-sqlite
```

### Running Graphs

- Use `.invoke()` for single execution
- Use `.stream()` for streaming outputs
- Pass checkpoint configuration for persistence

## Code Conventions

### State Definition

- Use TypedDict with Annotated fields for state schema
- Leverage reducers (e.g., `operator.add`) for list accumulation
- Keep state flat and serializable

### Node Functions

- Accept full state as input
- Return partial state updates (dict)
- Use descriptive function names that indicate their purpose

### Error Handling

- Wrap LLM calls in try/except blocks
- Use error nodes in the graph for graceful degradation
- Log errors with context for debugging

## Testing

- Test individual node functions in isolation
- Verify graph structure before runtime
- Use mocked LLMs for deterministic testing

## Key Files

- Graph definitions typically in `graphs/` or `src/`
- State schemas often in `state.py` or `schemas.py`
- Configuration in `config.py` or `.env`

## Common Patterns

### Human-in-the-Loop

```python
# Use interrupt_before or interrupt_after
graph.add_node("human_review", human_review_node)
graph.compile(interrupt_before=["human_review"])
```

### Conditional Routing

```python
# Define router function
def route(state):
    return "continue" if state["count"] < 5 else "end"

graph.add_conditional_edges("node", route)
```

### Parallel Execution

- Use Send API for dynamic parallelism
- Map-reduce patterns for batch processing

## External Dependencies

- LangChain for LLM integrations
- Checkpoint stores (SQLite, Postgres) for persistence
- Vector stores for retrieval patterns

---

_Note: This file should be updated as the project evolves with specific patterns and conventions unique to your implementation._
