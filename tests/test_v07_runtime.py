"""Offline upstream memory, durable state, approval, and metering regressions."""

import hashlib
import socket
from types import SimpleNamespace
from uuid import uuid4

import pytest
from langchain_core.messages import HumanMessage

import app as app_module
from services.job_service import JobStore
from services.memory_service import MemoryService, scenario_key
from services.runtime_service import RuntimeService
from services.usage_service import UsageCallback, active_usage


def test_upstream_memory_offline_persists_isolates_and_deletes(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Memory must not use the network")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    memory = MemoryService(tmp_path / "memory")
    key = scenario_key("alice", "ceo", {"objectives": ["Menu"]})
    other = scenario_key("bob", "ceo", {"objectives": ["Menu"]})
    memory.remember(key, "Our menu contains sourdough", "Use the supplied sourdough menu")
    restarted = MemoryService(tmp_path / "memory")
    assert "sourdough" in restarted.recall(key, "sourdough")[0]
    assert restarted.recall(other, "sourdough") == []
    assert restarted.recall(key, "sourdough", max_chars=1) == []
    restarted.clear(key)
    assert restarted.recall(key, "sourdough") == []


def test_scope_changes_only_on_actual_context_change():
    a = scenario_key("a", "ceo", {"budget": 1, "updated_at": "now"})
    assert a == scenario_key("a", "ceo", {"budget": 1, "updated_at": "later"})
    assert a != scenario_key("a", "ceo", {"budget": 2})
    assert a != scenario_key("a", "cfo", {"budget": 1})


def test_durable_recovery_preserves_queued_and_never_replays_running(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite3")
    running = store.create("a", "graph", {})
    assert store.claim()["id"] == running["id"]
    queued = store.create("a", "graph", {})
    restarted = JobStore(tmp_path / "jobs.sqlite3")
    restarted.recover()
    assert restarted.get(running["id"], "a")["status"] == "interrupted"
    assert restarted.claim()["id"] == queued["id"]
    with pytest.raises(LookupError):
        restarted.get(queued["id"], "b")


def test_cancel_and_approval_transitions(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite3")
    job = store.create("a", "export", {}, approval=True)
    assert store.claim() is None
    with pytest.raises(ValueError):
        store.approve(job["id"], "b")
    store.approve(job["id"], "a")
    with pytest.raises(ValueError):
        store.approve(job["id"], "a")
    claimed = store.claim()
    store.cancel(job["id"], "a")
    with pytest.raises(RuntimeError):
        store.reserve(claimed, 1, 0.01)
    store.finish(claimed, result={})
    assert store.get(job["id"], "a")["status"] == "cancelled"


@pytest.fixture
def meter(tmp_path, monkeypatch):
    from config import OPENAI_MODEL

    monkeypatch.setenv("PRICED_MODEL", OPENAI_MODEL)
    monkeypatch.setenv("MODEL_INPUT_USD_PER_MILLION", "10")
    monkeypatch.setenv("MODEL_OUTPUT_USD_PER_MILLION", "30")
    store = JobStore(tmp_path / "jobs.sqlite3")
    job = store.begin_operation("a")
    return store, job, UsageCallback(store, job)


def start_call(callback, text="menu"):
    identifier = uuid4()
    callback.on_chat_model_start(
        {},
        [[HumanMessage(content=text)]],
        run_id=identifier,
        invocation_params={"max_tokens": 600},
    )
    return identifier


def test_exact_usage_settlement(meter):
    store, job, callback = meter
    identifier = start_call(callback)
    callback.on_llm_end(
        SimpleNamespace(
            llm_output={"token_usage": {"prompt_tokens": 100, "completion_tokens": 20}}
        ),
        run_id=identifier,
    )
    result = store.get(job["id"], "a")
    assert result["tokens"] == 120
    assert result["cost"] == pytest.approx(0.0016)
    assert result["reserved_tokens"] == 0
    assert result["reserved_cost"] == pytest.approx(0)


def test_limits_before_provider_call(meter):
    store, job, callback = meter
    with pytest.raises(RuntimeError, match="limit"):
        start_call(callback, "x" * 20001)
    assert store.get(job["id"], "a")["reserved_tokens"] == 0
    store.reserve(job, 1, 1.0)
    with pytest.raises(RuntimeError, match="limit"):
        start_call(callback)


def test_uncertain_usage_retains_reservations(meter):
    store, job, callback = meter
    identifier = start_call(callback)
    with pytest.raises(RuntimeError, match="usage missing"):
        callback.on_llm_end(
            SimpleNamespace(llm_output={}, generations=[[SimpleNamespace(message=None)]]),
            run_id=identifier,
        )
    assert store.get(job["id"], "a")["reserved_tokens"] > 0
    identifier = start_call(callback)
    callback.on_llm_error(RuntimeError("transport"), run_id=identifier)
    assert store.get(job["id"], "a")["reserved_cost"] > 0


def test_missing_or_wrong_model_pricing_blocks_calls(meter, monkeypatch):
    _, _, callback = meter
    monkeypatch.setenv("PRICED_MODEL", "wrong")
    with pytest.raises(RuntimeError, match="exact active model"):
        start_call(callback)
    from config import OPENAI_MODEL

    monkeypatch.setenv("PRICED_MODEL", OPENAI_MODEL)
    monkeypatch.setenv("MODEL_INPUT_USD_PER_MILLION", "")
    with pytest.raises(RuntimeError, match="pricing"):
        start_call(callback)


def test_context_resets_and_usage_operations_are_persisted(tmp_path):
    runtime = RuntimeService(tmp_path, lambda **kwargs: {})
    with runtime.operation("a"):
        assert active_usage.get() is not None
    assert active_usage.get() is None
    with pytest.raises(RuntimeError):
        with runtime.operation("a"):
            raise RuntimeError("failed")
    assert active_usage.get() is None


def test_export_approval_receipt_and_mutation_rejection(tmp_path, monkeypatch):
    from services.artifact_service import ArtifactService

    static = tmp_path / "static"
    artifact = static / "generated_outputs" / "test" / "summary.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("scenario-specific plan")
    monkeypatch.setattr("services.artifact_service.artifact_service", ArtifactService(static))
    runtime = RuntimeService(tmp_path / "runtime", lambda **kwargs: {})
    source = runtime.store.create("a", "graph", {})
    runtime.store.claim()
    runtime.store.finish(
        source,
        result={
            "artifacts": [
                {
                    "path": "generated_outputs/test/summary.md",
                    "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                }
            ]
        },
    )
    export = runtime.propose_export("a", source["id"])
    assert runtime.store.claim() is None
    runtime.store.approve(export["id"], "a")
    claimed = runtime.store.claim()
    receipt = runtime.execute(claimed)
    assert receipt["external_actions_executed"] is False
    assert receipt["size_bytes"] > 0
    runtime.store.finish(claimed, result=receipt)
    with pytest.raises(LookupError):
        runtime.propose_export("b", source["id"])
    artifact.write_text("changed")
    with pytest.raises(ValueError, match="changed"):
        runtime.export(claimed)
    assert not (runtime.root / "exports" / f'{claimed["id"]}.tmp').exists()


def test_job_api_owner_scope_and_memory_policy(test_client, monkeypatch):
    runtime = app_module.get_runtime()
    monkeypatch.setattr(runtime.worker, "start", lambda: None)
    with test_client.session_transaction() as session:
        session["_id"] = "alice"
    job = runtime.store.create("alice", "graph", {})
    assert test_client.get(f'/api/jobs/{job["id"]}').status_code == 200
    with app_module.app.test_client() as other:
        assert other.get(f'/api/jobs/{job["id"]}').status_code == 404
    payload = {"agent": "ceo", "scenario": {"company_name": "Menu"}, "enabled": True}
    assert test_client.post("/api/memory/policy", json=payload).json["enabled"]
    assert test_client.post("/api/memory/status", json=payload).json["enabled"]
    assert test_client.post("/api/memory/clear", json=payload).status_code == 200
    assert not test_client.post("/api/memory/status", json=payload).json["enabled"]


def test_callback_gate_runs_before_generation_and_records_actual_usage(meter, monkeypatch):
    from langchain_openai import ChatOpenAI
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.outputs import ChatResult, ChatGeneration
    from langchain_core.messages import AIMessage

    store, job, callback = meter
    calls = []

    def generate(self, messages, **kwargs):
        calls.append(messages)
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content="Plan"))],
            llm_output={"token_usage": {"prompt_tokens": 100, "completion_tokens": 20}},
        )

    monkeypatch.setattr(ChatOpenAI, "_generate", generate)
    model = ChatOpenAI(api_key="offline-placeholder", max_tokens=600, callbacks=[callback])
    BaseChatModel.invoke(model, [HumanMessage(content="menu")])
    assert len(calls) == 1
    assert store.get(job["id"], "a")["tokens"] == 120
    monkeypatch.setenv("PRICED_MODEL", "wrong")
    with pytest.raises(RuntimeError, match="pricing"):
        BaseChatModel.invoke(model, [HumanMessage(content="menu")])
    assert len(calls) == 1


def test_langgraph_nodes_inherit_usage_context(meter):
    from langgraph.graph import StateGraph, START, END

    _, _, callback = meter
    observed = []

    def node(state):
        observed.append(active_usage.get())
        return state

    graph = StateGraph(dict)
    graph.add_node("test", node)
    graph.add_edge(START, "test")
    graph.add_edge("test", END)
    token = active_usage.set(callback)
    try:
        graph.compile().invoke({"value": "offline"})
    finally:
        active_usage.reset(token)
    assert observed == [callback]


def test_opt_in_chat_retrieves_prior_exchanges_without_context_leak(monkeypatch):
    runtime = app_module.get_runtime()
    scenario = {"company_name": "Menu", "budget": 50, "objectives": ["Website"]}
    key = scenario_key("alice", "ceo", scenario)
    runtime.set_memory(key, True)
    messages = []

    class Model:
        def invoke(self, items):
            messages.append(items)
            return SimpleNamespace(content="Use sourdough")

    monkeypatch.setattr(app_module, "_get_llm_for_chat", lambda: Model())
    app_module.llm_chat_response(("alice", "ceo"), "ceo", "sourdough menu", scenario)
    app_module._CHAT_SESSIONS.clear()
    app_module.llm_chat_response(("alice", "ceo"), "ceo", "sourdough", scenario)
    assert "Retrieved earlier exchanges" in messages[-1][0].content
    app_module.llm_chat_response(("bob", "ceo"), "ceo", "sourdough", scenario)
    assert "Retrieved earlier exchanges" not in messages[-1][0].content


@pytest.mark.parametrize("payload", [[1], {"scenario": []}, {"agent": ""}, {"agent": 1}])
def test_memory_rejects_invalid_shape(test_client, monkeypatch, payload):
    runtime = app_module.get_runtime()
    monkeypatch.setattr(runtime.worker, "start", lambda: None)
    assert test_client.post("/api/memory/status", json=payload).status_code == 400


def test_usage_operations_are_never_claimed_by_background_worker(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite3")
    job = store.begin_operation("a")
    assert job["status"] == "running"
    assert store.claim() is None


def test_recent_chat_context_is_bounded_without_opt_in(monkeypatch):
    scenario = {"company_name": "Menu", "objectives": ["Website"]}
    observed = []

    class Model:
        def invoke(self, messages):
            observed.append(messages)
            return SimpleNamespace(content="Plan")

    monkeypatch.setattr(app_module, "_get_llm_for_chat", lambda: Model())
    for index in range(8):
        app_module.llm_chat_response(("a", "ceo"), "ceo", str(index), scenario)
    assert len(observed[-1]) == 10  # System, four exchanges, current message.
    assert not app_module.get_runtime().memory.root.exists()
