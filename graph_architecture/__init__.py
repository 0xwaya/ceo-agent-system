"""
Hierarchical Graph-Based Multi-Agent System

Production-ready multi-agent architecture using LangGraph with:
- CEO orchestrator
- Specialized subgraphs (CFO, Engineer, Researcher)
- Checkpoint-based persistence
- Role-based guards
- Human-in-the-loop approvals
- Multi-tenant support
"""

__version__ = "1.0.0"

# Core components
from graph_architecture.main_graph import build_master_graph, execute_multi_agent_system

from graph_architecture.schemas import (
    SharedState,
    CEOState,
    CFOSubgraphState,
    AgentRole,
    MessageType,
    TaskPriority,
    RiskLevel,
    create_initial_shared_state,
    create_message,
)

from graph_architecture.checkpointer import (
    create_checkpointer,
    CheckpointManager,
    CheckpointRecovery,
    MultiTenantCheckpointer,
)

from graph_architecture.guards import (
    SubgraphEntryGuard,
    Domain,
    AuthorizationLevel,
    validate_agent_role,
    validate_domain_access,
    validate_hierarchy,
)

from graph_architecture.approval_nodes import (
    human_approval_node,
    create_budget_approval_request,
    create_risk_escalation_request,
    process_approval_response,
)

# Subgraphs
from graph_architecture.subgraphs.cfo_subgraph import build_cfo_subgraph

__all__ = [
    # Main
    "build_master_graph",
    "execute_multi_agent_system",
    # Schemas
    "SharedState",
    "CEOState",
    "CFOSubgraphState",
    "AgentRole",
    "MessageType",
    "TaskPriority",
    "RiskLevel",
    "create_initial_shared_state",
    "create_message",
    # Checkpointing
    "create_checkpointer",
    "CheckpointManager",
    "CheckpointRecovery",
    "MultiTenantCheckpointer",
    # Guards
    "SubgraphEntryGuard",
    "Domain",
    "AuthorizationLevel",
    "validate_agent_role",
    "validate_domain_access",
    "validate_hierarchy",
    # Approvals
    "human_approval_node",
    "create_budget_approval_request",
    "create_risk_escalation_request",
    "process_approval_response",
    # Subgraphs
    "build_cfo_subgraph",
]


# Quick start example
def quick_start():
    """
    Quick start example for hierarchical multi-agent system
    """
    print(
        """
    Hierarchical Multi-Agent System - Quick Start
    ============================================

    # 1. Basic execution
    from graph_architecture import execute_multi_agent_system

    result = execute_multi_agent_system(
        company_name="Acme Corp",
        industry="Technology",
        location="San Francisco, CA",
        total_budget=100000.0,
        target_days=90,
        objectives=["Launch product", "Build brand"],
        use_checkpointing=True
    )

    # 2. Advanced usage with checkpointing
    from graph_architecture import build_master_graph, create_checkpointer

    checkpointer = create_checkpointer("sqlite", "./checkpoints.db")
    graph = build_master_graph(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "session-123"}}
    result = graph.invoke(initial_state, config=config)

    # 3. Run tutorials
    python3 graph_architecture/TUTORIAL.py

    # See IMPLEMENTATION_GUIDE.md for complete documentation
    """
    )


if __name__ == "__main__":
    quick_start()
