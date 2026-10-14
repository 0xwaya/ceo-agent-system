"""Offline CFO oversight scenarios and real LangGraph approval boundaries."""

from copy import deepcopy
from pathlib import Path
import subprocess

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Overwrite

from graph_architecture import main_graph
from graph_architecture.cfo_skepticism import cfo_skepticism_review, route_after_skepticism
from graph_architecture.schemas import create_initial_shared_state


@pytest.fixture
def state():
    return {
        **create_initial_shared_state("Test Co", "Software", "Ohio", 1000, 30, ["Plan"]),
        "dispatch_plan": ["cfo", "engineer"],
        "current_dispatch_index": 2,
        "executive_decisions": [
            {"decision_id": "d1", "decision": "Plan a site", "rationale": "Meet objective"}
        ],
        "agent_outputs": [
            {
                "agent": "cfo",
                "summary": {"recommendation": "approve", "key_numbers": {"total_budget": 100}},
            },
            {"agent": "engineer", "summary": {"execution_mode": "local_artifacts"}},
        ],
    }


def reviewed(state):
    update = cfo_skepticism_review(state)
    return {**state, **update}


def test_clean_pass(state):
    result = reviewed(state)
    assert result["cfo_flags"] == []
    assert result["pending_approvals"] == []
    assert route_after_skepticism(result) == "consolidate"


@pytest.mark.parametrize("approved", [False, True])
def test_irreversible_action_requires_matching_approval(state, approved):
    state["agent_outputs"][1]["summary"]["actions"] = [
        {"action_id": "delete", "irreversible": True, "approval_request_id": "approval-1"}
    ]
    state["approved_actions"] = ["approval-1"] if approved else ["unrelated-approval"]
    result = reviewed(state)
    assert bool(result["cfo_flags"]) is not approved
    assert route_after_skepticism(result) == ("consolidate" if approved else "approval")
    if not approved:
        assert result["cfo_flags"][0]["code"] == "unapproved_irreversible_action"
        assert result["pending_approvals"][0].risk_level == "critical"


def test_spend_overrun(state):
    state["budget_spent"] = {"engineer": 101}
    result = reviewed(state)
    assert result["cfo_flags"][0]["code"] == "spend_overrun"
    assert result["cfo_skepticism_report"]["tracked_spend"] == 101
    assert route_after_skepticism(result) == "approval"


def test_exact_approved_boundary_and_decimal_costs(state):
    state["agent_outputs"][0]["summary"]["key_numbers"]["total_budget"] = 0.3
    state["agent_outputs"][1]["summary"]["actions"] = [{"cost": 0.1}, {"cost": 0.2}]
    assert reviewed(state)["cfo_flags"] == []
    assert reviewed(state)["cfo_skepticism_report"]["tracked_spend"] == 0.3


def test_external_action_has_its_own_zero_cost_flag(state):
    state["agent_outputs"][1]["summary"]["budget_used"] = 10
    state["agent_outputs"][1]["summary"]["actions"] = [
        {"action_id": "publish", "external_side_effect": True, "cost": 0}
    ]
    result = reviewed(state)
    assert result["cfo_flags"][0]["code"] == "untracked_external_cost"


def test_external_side_effect_without_cost(state):
    state["agent_outputs"][1]["summary"]["external_actions_executed"] = True
    result = reviewed(state)
    assert result["cfo_flags"][0]["code"] == "untracked_external_cost"
    assert route_after_skepticism(result) == "approval"
    report = main_graph.ceo_generate_final_report_node(result)["final_summary"]
    assert "outputs report external actions" in report
    assert "zero tracked cost" in report
    assert "No deployment, purchases" not in report


def test_ceo_decision_without_rationale(state):
    state["executive_decisions"][0]["rationale"] = " "
    result = reviewed(state)
    assert result["cfo_flags"][0]["code"] == "missing_ceo_rationale"
    assert result["pending_approvals"][0].risk_level == "medium"
    assert route_after_skepticism(result) == "consolidate"


def test_unknown_dispatch_role(state):
    state["dispatch_plan"].append("unrecognized")
    state["current_dispatch_index"] = 2
    assert main_graph.route_dispatch(state) == "cfo_skepticism_review"
    result = reviewed(state)
    assert result["cfo_flags"][0]["code"] == "unknown_dispatch_role"
    assert route_after_skepticism(result) == "approval"


def test_review_does_not_mutate_or_duplicate_state(state):
    state["budget_spent"] = {"engineer": 101}
    before = deepcopy(state)
    first = reviewed(state)
    assert state == before
    second = cfo_skepticism_review(first)
    assert second["cfo_flags"] == []
    assert second["pending_approvals"] == []
    assert second["cfo_skepticism_report"]["requires_approval"]


def test_planning_estimates_are_not_spend_or_actions(state):
    state["agent_outputs"][1]["summary"].update(
        estimated_cost=500, deployment_notes=["Propose deployment after approval"]
    )
    assert reviewed(state)["cfo_flags"] == []


def test_spend_is_not_double_counted_and_multiple_outputs_are_added(state):
    state["budget_spent"] = {"engineer": 60}
    state["agent_outputs"][1]["summary"]["budget_used"] = 60
    state["agent_outputs"][1]["summary"]["actions"] = [{"cost": 60}]
    assert reviewed(state)["cfo_skepticism_report"]["tracked_spend"] == 60
    state["agent_outputs"].append({"agent": "engineer", "summary": {"budget_used": 50}})
    assert reviewed(state)["cfo_skepticism_report"]["tracked_spend"] == 110
    assert reviewed(state)["cfo_flags"][0]["code"] == "spend_overrun"


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True, "100"])
def test_invalid_spend_fails_explicitly(state, value):
    state["budget_spent"] = {"engineer": value}
    with pytest.raises(ValueError, match="finite non-negative"):
        cfo_skepticism_review(state)


@pytest.mark.parametrize("recommendation", ["reject", "needs_more_info", "approve_with_conditions"])
def test_nonapproval_cannot_authorize_spend(state, recommendation):
    state["agent_outputs"][0]["summary"]["recommendation"] = recommendation
    state["budget_spent"] = {"engineer": 1}
    assert reviewed(state)["cfo_flags"][0]["code"] == "spend_overrun"


@pytest.mark.parametrize("checkpointing", [False, True])
def test_graph_stops_before_consolidation_and_report(monkeypatch, state, checkpointing):
    monkeypatch.setattr(main_graph, "privacy_scrub_node", lambda state: {})
    monkeypatch.setattr(main_graph, "prompt_expert_node", lambda state: {})
    monkeypatch.setattr(
        main_graph,
        "ceo_analyze_wrapper",
        lambda state: {"dispatch_plan": [], "current_dispatch_index": 0},
    )
    monkeypatch.setattr(main_graph, "run_agent_node", lambda *args: {})
    consolidated = []
    monkeypatch.setattr(
        main_graph,
        "ceo_consolidate_summaries_node",
        lambda state: consolidated.append(True) or {},
    )
    state["budget_spent"] = {"engineer": 101}
    graph = main_graph.build_master_graph(InMemorySaver() if checkpointing else None)
    config = {"configurable": {"thread_id": "cfo-test"}}
    result = graph.invoke(state, config)
    assert not consolidated
    assert not result["final_summary"]
    assert result["current_phase"] == "awaiting_approval"
    assert len(result["pending_approvals"]) == 1
    assert len(result["cfo_flags"]) == 1
    if checkpointing:
        assert graph.get_state(config).next == ("approval",)
        request_id = result["pending_approvals"][0].request_id
        graph.update_state(
            config,
            {"pending_approvals": Overwrite([]), "approved_actions": [request_id]},
        )
        result = graph.invoke(None, config)
        assert result["current_phase"] == "complete"
        assert "exceeds CFO approval" in result["final_summary"]
        assert "consolidation" not in result["completed_phases"]


def test_invalid_ceo_role_reaches_review_without_dispatch(monkeypatch, state):
    monkeypatch.setattr(
        main_graph,
        "ceo_llm_analyze_node",
        lambda state: {
            "llm_routing_decision": {
                "dispatch_plan": ["cfo", "unknown"],
                "rationale": "Review this plan",
            }
        },
    )
    state.update(main_graph.ceo_analyze_wrapper(state))
    assert main_graph.route_dispatch(state) == "cfo_skepticism_review"
    assert reviewed(state)["cfo_flags"][0]["code"] == "unknown_dispatch_role"


def test_durable_job_pauses_and_resumes_without_replaying_agents(monkeypatch, tmp_path):
    from graph_architecture.checkpointer import create_checkpointer
    from services.analysis_access import AnalysisAccess
    from services.billing_service import billing_service
    from services.runtime_service import RuntimeService

    monkeypatch.setenv("APP_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setattr(billing_service, "has_active_membership", lambda owner: False)
    monkeypatch.setattr(
        main_graph,
        "create_checkpointer",
        lambda *args: create_checkpointer("sqlite", str(tmp_path / "checkpoints.sqlite")),
    )
    monkeypatch.setattr(main_graph, "privacy_scrub_node", lambda state: {})
    monkeypatch.setattr(main_graph, "prompt_expert_node", lambda state: {})
    monkeypatch.setattr(
        main_graph,
        "ceo_analyze_wrapper",
        lambda state: {"dispatch_plan": [], "current_dispatch_index": 0},
    )
    calls = []

    def run_agent(role, state):
        calls.append(role)
        return {
            "agent_outputs": [
                {"agent": role, "summary": {"external_actions_executed": True}, "artifacts": []}
            ]
        }

    monkeypatch.setattr(main_graph, "run_agent_node", run_agent)
    runtime = RuntimeService(tmp_path / "runtime", main_graph.execute_multi_agent_system)
    payload = {
        "company_name": "Test Co",
        "industry": "Software",
        "location": "Ohio",
        "total_budget": 1000,
        "target_days": 30,
        "objectives": ["Plan"],
    }
    job = runtime.store.create("owner", "graph", payload)
    access = AnalysisAccess()
    assert access.claim("owner", job["id"], runtime.store)
    job = runtime.store.claim()
    result = runtime.execute(job)
    runtime.store.finish(job, result=result)
    job = runtime.store.get(job["id"], "owner")
    assert job["status"] == "awaiting_approval"
    assert job["result"]["cfo_flags"][0]["code"] == "untracked_external_cost"
    assert not job["result"]["final_summary"]
    assert access.status("owner", runtime.store)["free_analysis_in_progress"]
    with pytest.raises(ValueError, match="exact pending"):
        main_graph.resume_multi_agent_system(f"owner:{job['id']}", ["wrong-request"])
    runtime.store.approve(job["id"], "owner")
    job = runtime.store.claim()
    result = runtime.execute(job)
    runtime.store.finish(job, result=result)
    job = runtime.store.get(job["id"], "owner")
    assert job["status"] == "succeeded"
    assert job["result"]["external_actions_executed"]
    assert not job["result"]["approval_required"]
    assert job["result"]["cfo_flags"]
    assert access.status("owner", runtime.store)["free_analysis_used"]
    assert calls == ["cto"]


def test_dashboard_confirmation_describes_risks_not_execution():
    source = (Path(__file__).resolve().parents[1] / "static/js/app.js").read_text()
    function = source.split("async function approveCurrentJob()", 1)[1].split(
        "async function proposeBuildTests()", 1
    )[0]
    harness = """
const assert = require('node:assert/strict');
const state = {activeThreadId: 'job-1'};
const requests = [];
const job = {
    id: 'job-1', kind: 'graph', status: 'awaiting_approval',
    result: {pending_approvals: [{risk_level: 'high', rationale: 'Spend exceeds approval'}]}
};
async function runtimeRequest(path, body) { requests.push([path, body]); return {job}; }
function confirm(message) {
    assert.match(message, /Spend exceeds approval/);
    assert.match(message, /does NOT approve purchases/);
    assert.doesNotMatch(message, /isolated test request/);
    return true;
}
async function watchDurableJob(id) { assert.equal(id, 'job-1'); }
function addChatMessage(message) { throw Error(message); }
"""
    harness += "\nasync function approveCurrentJob()" + function
    harness += """
approveCurrentJob().then(() => {
    assert.equal(requests.length, 2);
    assert.equal(requests[1][0], '/api/jobs/job-1/approve');
}).catch(error => { console.error(error); process.exitCode = 1; });
"""
    result = subprocess.run(["node", "-e", harness], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
