"""Offline regression tests for scenario fidelity and verified local execution."""

import hashlib
import json
import subprocess
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

import app as app_module
from exceptions import ValidationError, AnalysisError
from services.state_builder import CFOStateBuilder
from services.artifact_service import ArtifactService
from services.analysis_service import StrategicPlan, analyze_strategic_state
from graph_architecture import main_graph, llm_nodes


@pytest.fixture
def scenario():
    return {
        "company_name": "Orbit Bakery",
        "industry": "Food",
        "location": "Columbus",
        "budget": 2400,
        "timeline": 42,
        "objectives": ["Design a menu website"],
    }


@pytest.fixture
def artifacts(tmp_path, monkeypatch):
    service = ArtifactService(tmp_path / "static")
    monkeypatch.setattr("services.agent_service.artifact_service", service)
    monkeypatch.setattr(app_module, "artifact_service", service)
    return service


def test_empty_state_has_no_presets():
    state = CFOStateBuilder.create_initial_state()
    assert state["company_name"] == ""
    assert state["total_budget"] == 0
    assert state["target_completion_days"] == 0
    assert state["strategic_objectives"] == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("budget", None),
        ("budget", 0),
        ("budget", -1),
        ("budget", float("nan")),
        ("budget", float("inf")),
        ("budget", True),
        ("timeline", None),
        ("timeline", 0),
        ("timeline", 2.5),
        ("objectives", []),
        ("objectives", "not a list"),
        ("company_name", "   "),
    ],
)
def test_invalid_scenario_rejected(scenario, field, value):
    scenario[field] = value
    with pytest.raises(ValidationError):
        CFOStateBuilder.create_from_request(scenario)


def test_nested_and_graph_contracts_preserve_values(scenario):
    nested = CFOStateBuilder.create_from_request({"company_info": scenario})
    canonical = {
        **scenario,
        "total_budget": scenario["budget"],
        "target_days": scenario["timeline"],
    }
    canonical.pop("budget")
    canonical.pop("timeline")
    flat = CFOStateBuilder.create_from_request(canonical)
    assert nested == flat
    assert flat["total_budget"] == 2400
    assert flat["target_completion_days"] == 42


def test_scenarios_are_browser_session_scoped(test_client, scenario):
    response = test_client.post("/api/scenario/current", json=scenario)
    assert response.status_code == 200
    with app_module.app.test_client() as other:
        assert other.get("/api/scenario/current").json["scenario"]["company_name"] == ""
    assert (
        test_client.get("/api/scenario/current").json["scenario"]["company_name"]
        == scenario["company_name"]
    )


def test_analysis_is_validated_and_objective_specific(monkeypatch, scenario):
    from services import analysis_service

    plan = StrategicPlan(
        identified_tasks=[
            {
                "task_id": "menu-1",
                "task_name": "Menu page",
                "description": "Design the bakery menu page",
                "required_expertise": "web_development",
                "objective_index": 0,
                "priority": "HIGH",
                "estimated_budget": 700,
                "estimated_days": 10,
                "requires_payment": False,
            }
        ],
        risks=[],
        recommendations=[],
        discovery_questions=["What menu items are available?"],
        executive_summary="Create the requested menu website.",
    )
    captured = []

    class Model:
        def with_structured_output(self, schema):
            assert schema is StrategicPlan
            return self

        def invoke(self, messages):
            captured.append(json.loads(messages[1][1]))
            return plan

    monkeypatch.setattr(analysis_service, "_get_llm", lambda **kwargs: Model())
    state = CFOStateBuilder.create_from_request(scenario)
    result = analyze_strategic_state(state)
    assert captured[0]["strategic_objectives"] == scenario["objectives"]
    assert result["identified_tasks"][0]["status"] == "planned"
    assert result["budget_allocated"] == {"web_development": 700}
    plan.identified_tasks[0].objective_index = 2
    with pytest.raises(AnalysisError):
        analyze_strategic_state(state)
    plan.identified_tasks[0].objective_index = 0
    plan.identified_tasks[0].estimated_budget = 2401
    with pytest.raises(AnalysisError):
        analyze_strategic_state(state)


def test_model_failures_never_substitute_presets():
    with pytest.raises(RuntimeError, match="no preset"):
        llm_nodes._call_structured(None, "", "")


@pytest.mark.parametrize("checkpointing", [False, True])
def test_graph_uses_modern_nodes_and_verified_files(
    monkeypatch, scenario, artifacts, tmp_path, checkpointing
):
    from graph_architecture.checkpointer import create_checkpointer

    savers = []

    def temporary_checkpointer(*args):
        saver = create_checkpointer("sqlite", str(tmp_path / "nested" / "checkpoints.sqlite"))
        savers.append(saver)
        return saver

    monkeypatch.setattr(main_graph, "create_checkpointer", temporary_checkpointer)
    expert = {
        "needs_web_development": True,
        "requires_engineering": True,
        "requires_financial_analysis": True,
    }
    monkeypatch.setattr(
        main_graph, "prompt_expert_node", lambda state: {"prompt_expert_output": expert}
    )
    monkeypatch.setattr(
        main_graph,
        "ceo_llm_analyze_node",
        lambda state: {
            "llm_routing_decision": {
                "dispatch_plan": ["engineer", "cfo"],
                "rationale": "Menu website within budget",
            },
        },
    )
    for name, key in [
        ("cto_llm_architecture_node", "cto_architecture_output"),
        ("cfo_llm_summarize_node", "cfo_llm_output"),
        ("engineer_llm_architect_node", "engineer_llm_output"),
        ("webdev_llm_node", "webdev_output"),
    ]:
        monkeypatch.setattr(
            llm_nodes,
            name,
            lambda state, key=key: {
                key: {
                    "summary": f"Plan for {state['company_name']}",
                    "recommendations": [],
                },
            },
        )
    result = main_graph.execute_multi_agent_system(
        company_name=scenario["company_name"],
        industry=scenario["industry"],
        location=scenario["location"],
        total_budget=scenario["budget"],
        target_days=scenario["timeline"],
        objectives=scenario["objectives"],
        use_checkpointing=checkpointing,
        thread_id="offline-run",
    )
    assert result["thread_id"] == "offline-run"
    assert result["dispatch_plan"] == ["cfo", "engineer"]
    assert [item["agent"] for item in result["agent_outputs"]] == [
        "cto",
        "cfo",
        "engineer",
        "web_development",
    ]
    assert result["external_actions_executed"] is False
    assert result["budget_spent"] == {}
    assert result["completed_tasks"] == []
    assert result["artifacts"]
    assert not any(
        entry["path"].endswith((".svg", ".html", ".mmd")) for entry in result["artifacts"]
    )
    if checkpointing:
        assert (tmp_path / "nested" / "checkpoints.sqlite").is_file()
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            savers[0].conn.execute("SELECT 1")
    for entry in result["artifacts"]:
        content = (artifacts.static_root / entry["path"]).read_bytes()
        assert len(content) == entry["size_bytes"] > 0
        assert hashlib.sha256(content).hexdigest() == entry["sha256"]


def test_graph_endpoint_passes_canonical_values(test_client, monkeypatch, scenario):
    calls = []
    monkeypatch.setattr(
        app_module,
        "execute_multi_agent_system",
        lambda **kwargs: calls.append(kwargs) or {"agent_outputs": []},
    )

    runtime = app_module.get_runtime()
    monkeypatch.setattr(runtime.worker, "start", lambda: None)
    payload = {
        **scenario,
        "total_budget": scenario["budget"],
        "target_days": scenario["timeline"],
    }
    payload.pop("budget")
    payload.pop("timeline")
    response = test_client.post("/api/graph/execute", json=payload)
    assert response.status_code == 202
    job = runtime.store.claim()
    runtime.execute(job)
    assert calls[0]["total_budget"] == scenario["budget"]
    assert calls[0]["target_days"] == scenario["timeline"]
    assert ":" in calls[0]["thread_id"]
    assert test_client.post("/api/graph/execute", json=scenario).status_code == 400


def test_chat_context_and_memory_do_not_leak(monkeypatch, test_client, scenario):
    messages = []

    class Chat:
        def invoke(self, items):
            messages.append(items)
            return SimpleNamespace(content="A menu website plan")

    monkeypatch.setattr(app_module, "_get_llm_for_chat", lambda: Chat())
    payload = {"message": "Plan the menu", "scenario": scenario, "agent": "ceo"}
    assert test_client.post("/api/chat/message", json=payload).status_code == 200
    assert scenario["objectives"][0] in messages[0][0].content
    assert test_client.post("/api/chat/message", json=payload).status_code == 200
    assert len(messages[-1]) == 4
    payload["scenario"] = {**scenario, "company_name": "Different business"}
    assert test_client.post("/api/chat/message", json=payload).status_code == 200
    assert len(messages[-1]) == 2
    assert test_client.post("/api/chat/clear", json={"agent": "ceo"}).json["cleared"]
    test_client.post("/api/chat/message", json=payload)
    assert len(messages[-1]) == 2


def test_graph_launch_tracks_durable_job():
    root = Path(__file__).resolve().parents[1]
    script = (root / "static/js/app.js").read_text()
    function = script.split("async function runFullOrchestration()", 1)[1]
    function = function.split("// Execute specific agent", 1)[0]
    harness = """
const assert = require('node:assert/strict');
const state = {};
const ACTIVE_JOB_STORAGE_KEY = 'ceo_active_job:test-account';
const saved = {};
const watched = [];
const localStorage = {setItem: (key, value) => saved[key] = value};
const watchDurableJob = id => watched.push(id);
const persistScenarioToStorage = () => ({company_name:'Test', objectives:['Menu']});
const addChatMessage = () => {};
const addLogEntry = () => {};
const fetch = async () => ({
    ok:true, json:async () => ({success:true, thread_id:'job-1', job_id:'job-1'})
});
"""
    harness += "async function runFullOrchestration()" + function
    harness += """
runFullOrchestration().then(() => {
    assert.equal(state.activeThreadId, 'job-1');
    assert.equal(saved[ACTIVE_JOB_STORAGE_KEY], 'job-1');
    assert.deepEqual(watched, ['job-1']);
});
"""
    result = subprocess.run(["node", "-e", harness], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_active_javascript_parses():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["node", "--check", str(root / "static/js/app.js")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_blank_dashboard_fields(test_client):
    html = test_client.get("/").get_data(as_text=True)
    assert "v0.8.0" in html
    assert 'value="1000"' not in html
    assert 'value="90"' not in html
    assert "Ohio Compliance" not in html
    assert "Next.js + AR Stack" not in html


def test_missing_sqlite_dependency_fails_explicitly(monkeypatch):
    from graph_architecture import checkpointer

    monkeypatch.setattr(checkpointer, "SQLITE_AVAILABLE", False)
    with pytest.raises(ImportError, match="SQLite checkpointer not available"):
        checkpointer.create_checkpointer("sqlite")


def test_socket_chat_failure_is_explicit(monkeypatch, scenario):
    events = []

    def failed(*args, **kwargs):
        raise RuntimeError("Model unavailable")

    monkeypatch.setattr(app_module, "llm_chat_response", failed)
    monkeypatch.setattr(app_module, "emit", lambda name, payload: events.append((name, payload)))
    with app_module.app.test_request_context():
        app_module.handle_ai_chat_request(
            {"message": "Plan the menu", "agent": "ceo", "scenario": scenario}
        )
    name, response = events[0]
    assert name == "ai_chat_response"
    assert response["error"] is True
    assert "no model response was generated" in response["message"]


def test_graph_request_is_persisted_before_worker_start(test_client, monkeypatch, scenario):
    runtime = app_module.get_runtime()
    monkeypatch.setattr(runtime.worker, "start", lambda: None)
    payload = {**scenario, "total_budget": scenario["budget"], "target_days": scenario["timeline"]}
    payload.pop("budget")
    payload.pop("timeline")
    response = test_client.post("/api/graph/execute", json=payload)
    assert response.status_code == 202
    assert runtime.store.claim()["payload"]["objectives"] == scenario["objectives"]


def test_checkpoint_connection_closes_on_graph_failure(monkeypatch, scenario, tmp_path):
    from graph_architecture.checkpointer import create_checkpointer

    saver = create_checkpointer("sqlite", str(tmp_path / "checkpoints.sqlite"))
    monkeypatch.setattr(main_graph, "create_checkpointer", lambda *args: saver)

    def failed(*args, **kwargs):
        raise RuntimeError("Graph failed")

    monkeypatch.setattr(main_graph, "build_master_graph", failed)
    with pytest.raises(RuntimeError, match="Graph failed"):
        main_graph.execute_multi_agent_system(
            company_name=scenario["company_name"],
            industry=scenario["industry"],
            location=scenario["location"],
            total_budget=scenario["budget"],
            target_days=scenario["timeline"],
            objectives=scenario["objectives"],
        )
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        saver.conn.execute("SELECT 1")
