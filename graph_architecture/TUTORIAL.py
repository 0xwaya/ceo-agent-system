"""
Complete Tutorial: Hierarchical Graph-Based Multi-Agent System
================================================================

This tutorial demonstrates how to use the hierarchical multi-agent system
architecture with LangGraph, featuring:

1. CEO orchestrator as root node
2. Specialized subgraphs (CFO, Engineer, Researcher)
3. Checkpoint-based persistence
4. Role-based guards and governance
5. Human-in-the-loop approvals
6. Multi-tenant support

Follow along to understand each component and how they work together.
"""

import logging
from typing import Dict, Any
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# PART 1: BASIC EXECUTION
# ============================================================================


def tutorial_1_basic_execution():
    """
    Tutorial 1: Basic execution without checkpointing
    """
    print("\n" + "=" * 80)
    print("TUTORIAL 1: Basic Execution")
    print("=" * 80)

    from graph_architecture.main_graph import execute_multi_agent_system

    result = execute_multi_agent_system(
        company_name="Acme Corporation",
        industry="E-commerce",
        location="New York, NY",
        total_budget=50000.0,
        target_days=60,
        objectives=[
            "Launch online marketplace",
            "Build payment infrastructure",
            "Establish brand presence",
        ],
        use_checkpointing=False,  # No persistence
    )

    print("\n✅ Execution completed!")
    print(f"Phases completed: {result.get('completed_phases', [])}")
    print(f"Final summary available: {bool(result.get('final_summary'))}")

    return result


# ============================================================================
# PART 2: CHECKPOINTING AND PERSISTENCE
# ============================================================================


def tutorial_2_checkpointing():
    """
    Tutorial 2: Using checkpointing for resumable workflows
    """
    print("\n" + "=" * 80)
    print("TUTORIAL 2: Checkpointing and Persistence")
    print("=" * 80)

    from graph_architecture.main_graph import build_master_graph
    from graph_architecture.checkpointer import create_checkpointer
    from graph_architecture.schemas import create_initial_shared_state, CEOState

    # Create checkpointer
    checkpointer = create_checkpointer("sqlite", "./data/tutorial_checkpoints.sqlite")

    # Build graph with checkpointing
    graph = build_master_graph(checkpointer=checkpointer)

    # Create initial state
    initial_state = create_initial_shared_state(
        company_name="StartupCo",
        industry="FinTech",
        location="Austin, TX",
        total_budget=75000.0,
        target_days=90,
        objectives=["Launch mobile app", "Acquire first 1000 users"],
    )

    ceo_state = CEOState(
        **initial_state, executive_decisions=[], delegation_log=[], subgraph_summaries=[]
    )

    # Execute with thread ID
    thread_id = "tutorial-session-001"
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\n📍 Executing with thread ID: {thread_id}")
    result = graph.invoke(ceo_state, config=config)

    print("\n✅ Execution completed and checkpointed!")

    # Demonstrate checkpoint retrieval
    print("\n📖 Retrieving execution history...")
    from graph_architecture.checkpointer import CheckpointRecovery

    history = CheckpointRecovery.get_execution_history(graph, thread_id, limit=5)
    print(f"Found {len(history)} checkpoints")

    return result, thread_id


def tutorial_2b_resume_from_checkpoint():
    """
    Tutorial 2b: Resume execution from checkpoint
    """
    print("\n" + "=" * 80)
    print("TUTORIAL 2B: Resume from Checkpoint")
    print("=" * 80)

    from graph_architecture.main_graph import build_master_graph
    from graph_architecture.checkpointer import create_checkpointer, CheckpointRecovery

    # Use same checkpointer and thread
    checkpointer = create_checkpointer("sqlite", "./data/tutorial_checkpoints.sqlite")
    graph = build_master_graph(checkpointer=checkpointer)

    thread_id = "tutorial-session-001"

    print(f"\n🔄 Resuming from thread: {thread_id}")

    # Get current state
    latest_state = CheckpointRecovery.get_latest_checkpoint(graph, thread_id)

    if latest_state:
        print(f"Current phase: {latest_state.get('current_phase', 'unknown')}")
        print(f"Completed phases: {len(latest_state.get('completed_phases', []))}")

        # Resume execution
        result = CheckpointRecovery.resume_from_checkpoint(graph, thread_id)
        print("\n✅ Resumed and completed!")
    else:
        print("❌ No checkpoint found")


# ============================================================================
# PART 3: ROLE-BASED GUARDS
# ============================================================================


def tutorial_3_guards():
    """
    Tutorial 3: Demonstrating role-based guards
    """
    print("\n" + "=" * 80)
    print("TUTORIAL 3: Role-Based Guards")
    print("=" * 80)

    from graph_architecture.guards import (
        SubgraphEntryGuard,
        Domain,
        AgentRole,
        validate_hierarchy,
        UnauthorizedAccessError,
    )
    from graph_architecture.schemas import create_initial_shared_state

    # Create CFO entry guard
    cfo_guard = SubgraphEntryGuard(allowed_roles={AgentRole.CEO}, domain=Domain.FINANCE)

    state = create_initial_shared_state(
        company_name="Test",
        industry="Test",
        location="Test",
        total_budget=10000,
        target_days=30,
        objectives=["Test"],
    )

    # Test: CEO can enter CFO subgraph
    print("\n✅ Test 1: CEO entering CFO subgraph")
    try:
        state = cfo_guard.validate_entry(state, requester_role=AgentRole.CEO)
        print("   Access granted!")
    except UnauthorizedAccessError as e:
        print(f"   Access denied: {e}")

    # Test: Engineer cannot enter CFO subgraph
    print("\n❌ Test 2: Engineer attempting to enter CFO subgraph")
    try:
        state = cfo_guard.validate_entry(state, requester_role=AgentRole.ENGINEER)
        print("   Access granted!")
    except UnauthorizedAccessError as e:
        print(f"   Access denied (expected): {e.violation_type}")

    # Test: Hierarchy validation
    print("\n✅ Test 3: Communication hierarchy")

    # CEO can talk to CFO (downward)
    valid = validate_hierarchy(AgentRole.CEO, AgentRole.CFO)
    print(f"   CEO → CFO: {'✅ Allowed' if valid else '❌ Denied'}")

    # CFO can talk to CEO (upward)
    valid = validate_hierarchy(AgentRole.CFO, AgentRole.CEO)
    print(f"   CFO → CEO: {'✅ Allowed' if valid else '❌ Denied'}")

    # Engineer can talk to Researcher (lateral)
    valid = validate_hierarchy(AgentRole.ENGINEER, AgentRole.RESEARCHER)
    print(f"   Engineer → Researcher: {'✅ Allowed' if valid else '❌ Denied'}")


# ============================================================================
# PART 4: HUMAN-IN-THE-LOOP APPROVALS
# ============================================================================


def tutorial_4_approvals():
    """
    Tutorial 4: Human-in-the-loop approval workflows
    """
    print("\n" + "=" * 80)
    print("TUTORIAL 4: Human-in-the-Loop Approvals")
    print("=" * 80)

    from graph_architecture.approval_nodes import (
        create_budget_approval_request,
        create_risk_escalation_request,
        create_batch_approval_summary,
    )
    from graph_architecture.schemas import create_initial_shared_state, RiskLevel

    # Create initial state
    state = create_initial_shared_state(
        company_name="ApprovalDemo",
        industry="SaaS",
        location="Seattle, WA",
        total_budget=100000,
        target_days=120,
        objectives=["Build product", "Launch marketing"],
    )

    # Create approval requests
    print("\n📝 Creating approval requests...")

    # Budget approval
    budget_approval = create_budget_approval_request(
        action="Purchase enterprise CRM license",
        cost=5000.0,
        rationale="Need CRM for sales team scaling",
        risk_level=RiskLevel.MEDIUM,
        auto_decline_hours=48,
    )

    state["pending_approvals"].append(budget_approval)

    # Risk escalation
    risk_approval = create_risk_escalation_request(
        action="Deploy to production without full QA",
        risk_level=RiskLevel.HIGH,
        rationale="Customer demo scheduled, need early access",
        estimated_cost=0,
    )

    state["pending_approvals"].append(risk_approval)

    # Generate batch summary
    summary = create_batch_approval_summary(state)

    print(f"\n📋 Approval Summary:")
    print(f"   Total pending: {summary['total_pending']}")
    print(f"   Total cost: ${summary['total_cost']:,.2f}")
    print(f"   By risk level: {summary['by_risk_level']}")

    print("\n📬 Pending Approvals:")
    for req in summary["requests"]:
        print(f"\n   [{req['request_id']}]")
        print(f"   Action: {req['action']}")
        print(f"   Cost: ${req['cost']:,.2f}")
        print(f"   Risk: {req['risk_level']}")

    # Simulate approval
    print("\n✅ Simulating approval of budget request...")
    from graph_architecture.approval_nodes import process_approval_response

    approval_response = {
        "request_id": budget_approval.request_id,
        "approved": True,
        "notes": "Approved with condition: 1-year contract only",
    }

    state = process_approval_response(state, approval_response)

    print(f"   Approved actions: {len(state.get('approved_actions', []))}")
    print(f"   Pending approvals: {len(state.get('pending_approvals', []))}")


# ============================================================================
# PART 5: MULTI-TENANT ISOLATION
# ============================================================================


def tutorial_5_multi_tenant():
    """
    Tutorial 5: Multi-tenant execution
    """
    print("\n" + "=" * 80)
    print("TUTORIAL 5: Multi-Tenant Isolation")
    print("=" * 80)

    from graph_architecture.checkpointer import create_checkpointer, MultiTenantCheckpointer
    from graph_architecture.main_graph import build_master_graph
    from graph_architecture.schemas import create_initial_shared_state, CEOState

    # Create multi-tenant checkpointer
    base_checkpointer = create_checkpointer("sqlite", "./data/multitenant.sqlite")
    mt_checkpointer = MultiTenantCheckpointer(base_checkpointer)

    # Build graph
    graph = build_master_graph(checkpointer=base_checkpointer)

    # Execute for multiple tenants
    tenants = [
        {"tenant_id": "customer-001", "company": "Acme Corp"},
        {"tenant_id": "customer-002", "company": "TechStart Inc"},
        {"tenant_id": "customer-003", "company": "InnovateCo"},
    ]

    print("\n🏢 Executing for multiple tenants...")

    for tenant in tenants:
        tenant_id = tenant["tenant_id"]
        company = tenant["company"]

        print(f"\n   Tenant: {tenant_id} ({company})")

        # Create tenant-specific config
        config = mt_checkpointer.create_tenant_config(tenant_id=tenant_id, session_id="session-001")

        print(f"   Thread ID: {config['configurable']['thread_id']}")

        # Create state
        state = create_initial_shared_state(
            company_name=company,
            industry="Technology",
            location="San Francisco, CA",
            total_budget=50000,
            target_days=90,
            objectives=["Launch product"],
        )

        ceo_state = CEOState(
            **state, executive_decisions=[], delegation_log=[], subgraph_summaries=[]
        )

        # Execute (isolated per tenant)
        result = graph.invoke(ceo_state, config=config)

        print(f"   ✅ Completed: {len(result.get('completed_phases', []))} phases")

    print("\n✅ All tenants executed with isolation!")


# ============================================================================
# PART 6: DEBUGGING AND OBSERVABILITY
# ============================================================================


def tutorial_6_debugging():
    """
    Tutorial 6: Debugging with execution history
    """
    print("\n" + "=" * 80)
    print("TUTORIAL 6: Debugging and Observability")
    print("=" * 80)

    from graph_architecture.main_graph import build_master_graph
    from graph_architecture.checkpointer import create_checkpointer
    from graph_architecture.schemas import create_initial_shared_state, CEOState

    # Create graph with checkpointing
    checkpointer = create_checkpointer("sqlite", "./data/debug.sqlite")
    graph = build_master_graph(checkpointer=checkpointer)

    # Execute
    state = create_initial_shared_state(
        company_name="DebugCo",
        industry="Software",
        location="Boston, MA",
        total_budget=30000,
        target_days=45,
        objectives=["Build MVP"],
    )

    ceo_state = CEOState(**state, executive_decisions=[], delegation_log=[], subgraph_summaries=[])

    thread_id = "debug-session"
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\n▶️  Executing with debug tracking...")
    result = graph.invoke(ceo_state, config=config)

    # Get execution history
    print(f"\n🔍 Analyzing execution history...")

    history = []
    for state_snapshot in graph.get_state_history(config):
        history.append(
            {
                "checkpoint_id": state_snapshot.metadata.get("checkpoint_id", "unknown"),
                "next_node": state_snapshot.next,
                "phase": state_snapshot.values.get("current_phase", "unknown"),
            }
        )

    print(f"\n📊 Execution Flow ({len(history)} steps):")
    for i, step in enumerate(history[:10], 1):  # Show first 10
        print(f"   {i}. Phase: {step['phase']}, Next: {step['next_node']}")

    # Export checkpoint
    print(f"\n💾 Exporting checkpoint...")
    from graph_architecture.checkpointer import export_checkpoint

    export_data = export_checkpoint(graph, thread_id, output_file="./data/exported_checkpoint.json")

    print(f"   Exported to: ./data/exported_checkpoint.json")
    print(f"   State keys: {list(export_data.get('state', {}).keys())[:5]}...")


# ============================================================================
# RUN ALL TUTORIALS
# ============================================================================


def run_all_tutorials():
    """
    Run all tutorials in sequence
    """
    print("\n" + "=" * 80)
    print("HIERARCHICAL MULTI-AGENT SYSTEM - COMPLETE TUTORIAL")
    print("=" * 80)

    tutorials = [
        ("Basic Execution", tutorial_1_basic_execution),
        ("Checkpointing", tutorial_2_checkpointing),
        ("Role-Based Guards", tutorial_3_guards),
        ("Human Approvals", tutorial_4_approvals),
        ("Multi-Tenant", tutorial_5_multi_tenant),
        ("Debugging", tutorial_6_debugging),
    ]

    for name, tutorial_func in tutorials:
        try:
            print(f"\n\n{'='*80}")
            print(f"Starting: {name}")
            print(f"{'='*80}")
            tutorial_func()
            print(f"\n✅ {name} completed successfully!")
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            import traceback

            traceback.print_exc()

    print("\n\n" + "=" * 80)
    print("ALL TUTORIALS COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    # Run individual tutorials or all
    import sys

    if len(sys.argv) > 1:
        tutorial_num = sys.argv[1]

        tutorials = {
            "1": tutorial_1_basic_execution,
            "2": tutorial_2_checkpointing,
            "2b": tutorial_2b_resume_from_checkpoint,
            "3": tutorial_3_guards,
            "4": tutorial_4_approvals,
            "5": tutorial_5_multi_tenant,
            "6": tutorial_6_debugging,
        }

        if tutorial_num in tutorials:
            tutorials[tutorial_num]()
        else:
            print(f"Unknown tutorial: {tutorial_num}")
            print(f"Available: {', '.join(tutorials.keys())}")
    else:
        # Run all
        run_all_tutorials()
