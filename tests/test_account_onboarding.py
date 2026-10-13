"""Offline account setup, trial atomicity, subscription and website wiring."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import re
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace
from uuid import uuid4

import pytest
from langchain_core.messages import HumanMessage

import app as app_module
from services.analysis_access import AnalysisAccess, AnalysisInProgress, SubscriptionRequired
from services.auth_service import AuthStore
from services.billing_service import BillingService
from services.job_service import JobStore
from services.usage_service import UsageCallback


@pytest.fixture
def account_store(tmp_path, monkeypatch):
    store = AuthStore(tmp_path / "auth")
    monkeypatch.setattr(app_module, "_auth_store", store)
    monkeypatch.setitem(app_module.app.config, "ACCOUNT_AUTH_ENABLED", True)
    billing = BillingService(tmp_path / "billing.sqlite3")
    monkeypatch.setattr("services.billing_service.billing_service", billing)
    monkeypatch.setattr("services.billing_routes.billing_service", billing)
    monkeypatch.setattr(app_module, "billing_service", billing)
    return store


def form_token(client, path):
    response = client.get(path)
    assert response.status_code == 200
    return re.search(r'name="csrf" value="([^"]+)"', response.text)[1]


def sign_in(client, email="customer@example.test"):
    csrf = form_token(client, "/login")
    response = client.post(
        "/login",
        data={"email": email, "password": "long-test-account-password", "csrf": csrf},
    )
    assert response.status_code == 302
    with client.session_transaction() as session:
        return {"X-CSRF-Token": session["csrf"]}


def test_browser_setup_is_protected_one_use_and_closes(account_store, test_client):
    csrf = form_token(test_client, "/setup")
    data = {
        "email": "operator@example.test",
        "password": "long-test-account-password",
        "confirmation": "long-test-account-password",
        "csrf": csrf,
    }
    assert test_client.post("/setup", data=data).status_code == 400
    code = account_store.prepare_setup()
    data["setup_code"] = code
    assert test_client.post("/setup", data=data).status_code == 302
    assert account_store.has_admin()
    assert test_client.get("/setup").status_code == 403
    with pytest.raises(ValueError, match="already exists"):
        account_store.prepare_setup()
    with closing(account_store.connect()) as db:
        row = db.execute("SELECT * FROM accounts").fetchone()
        assert row["role"] == "admin"
        assert row["password"] != data["password"]
        assert db.execute("SELECT * FROM setup").fetchone() is None


def test_expired_setup_code_and_concurrent_bootstrap(account_store):
    code = account_store.prepare_setup()
    with closing(account_store.connect()) as db, db:
        db.execute("UPDATE setup SET expires=0")
    with pytest.raises(ValueError, match="invalid or expired"):
        account_store.create("one@example.test", "long-test-account-password", "admin", code)
    code = account_store.prepare_setup()

    def create(index):
        try:
            account_store.create(
                f"admin{index}@example.test", "long-test-account-password", "admin", code
            )
            return True
        except ValueError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(create, range(2))) == 1


def test_signup_never_grants_admin_and_requires_csrf(account_store, test_client):
    assert test_client.get("/signup").headers["Location"] == "/setup"
    account_store.create("operator@example.test", "long-test-account-password", "admin")
    csrf = form_token(test_client, "/signup")
    data = {
        "email": "customer@example.test",
        "password": "long-test-account-password",
        "confirmation": "long-test-account-password",
        "role": "admin",
    }
    assert test_client.post("/signup", data=data).status_code == 403
    data["csrf"] = csrf
    assert test_client.post("/signup", data=data).status_code == 302
    headers = sign_in(test_client)
    assert test_client.get("/api/logs").status_code == 403
    assert test_client.get("/api/account/access").json["free_analysis_available"]
    assert test_client.post("/api/chat/message", json={}, headers=headers).status_code == 402
    assert (
        test_client.post("/api/agent/execute/branding", json={}, headers=headers).status_code == 402
    )


def test_free_analysis_evidence_and_repeat_gate(
    account_store, test_client, sample_company_info, monkeypatch
):
    account_store.create("customer@example.test", "long-test-account-password", "customer")
    headers = sign_in(test_client)
    seen = []
    evidence = {
        "status": "fetched",
        "url": "https://example.com/",
        "text": "Custom stone counters",
        "warning": "",
    }
    monkeypatch.setattr(app_module, "fetch_homepage", lambda url: evidence)
    monkeypatch.setattr(app_module, "_prompt_expert_node", lambda state: seen.append(state) or {})
    monkeypatch.setattr(app_module, "ceo_analyze", lambda state: seen.append(state) or state)
    assert test_client.post("/api/ceo/analyze", json={}, headers=headers).status_code == 400
    assert test_client.get("/api/account/access").json["free_analysis_available"]
    payload = {**sample_company_info, "website": "example.com"}
    response = test_client.post("/api/ceo/analyze", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json["free_analysis_completed"]
    assert response.json["website_evidence"]["text"] == evidence["text"]
    assert all(state["website_evidence"] == evidence for state in seen)
    assert (
        test_client.get("/api/scenario/current").json["scenario"]["website"]
        == "https://example.com/"
    )
    assert test_client.get("/api/account/access").json["free_analysis_used"]
    for endpoint in ["/api/ceo/analyze", "/api/cfo/analyze"]:
        response = test_client.post(endpoint, json=payload, headers=headers)
        assert response.status_code == 402
        assert response.json["code"] == "subscription_required"
    assert len(seen) == 2


def test_failed_analysis_does_not_consume_trial(
    account_store, test_client, sample_company_info, monkeypatch
):
    account_store.create("customer@example.test", "long-test-account-password", "customer")
    headers = sign_in(test_client)
    monkeypatch.setattr(app_module, "_prompt_expert_node", lambda state: {})

    def fail(state):
        raise RuntimeError("Offline provider failure")

    monkeypatch.setattr(app_module, "ceo_analyze", fail)
    response = test_client.post("/api/ceo/analyze", json=sample_company_info, headers=headers)
    assert response.status_code == 500
    assert test_client.get("/api/account/access").json["free_analysis_available"]


def test_trial_is_atomic_persistent_account_scoped_and_recovers(account_store, tmp_path):
    jobs = JobStore(tmp_path / "jobs.sqlite3")
    access = AnalysisAccess()
    first = jobs.begin_operation("alice")
    second = jobs.begin_operation("alice")

    def claim(job):
        try:
            return access.claim("alice", job["id"], jobs)
        except AnalysisInProgress:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(claim, [first, second])) == 1
    winner = first if access.is_free("alice", first["id"]) else second
    jobs.finish(winner, error="Provider failure")
    assert AnalysisAccess().status("alice", jobs)["free_analysis_available"]
    assert access.claim("alice", second["id"], jobs)
    jobs.finish(second, result={})
    with pytest.raises(SubscriptionRequired):
        AnalysisAccess().claim("alice", first["id"], jobs)
    bob = jobs.begin_operation("bob")
    assert access.claim("bob", bob["id"], jobs)
    jobs.recover()
    assert access.status("bob", jobs)["free_analysis_available"]


def test_only_verified_current_active_memberships_pass(account_store, tmp_path):
    from services.billing_service import billing_service

    access = AnalysisAccess()
    jobs = JobStore(tmp_path / "jobs.sqlite3")
    first = jobs.begin_operation("alice")
    access.claim("alice", first["id"], jobs)
    jobs.finish(first, result={})
    with closing(billing_service.connect()) as db, db:
        billing_service._wallet(db, "alice")
        db.execute(
            "UPDATE billing_wallets SET subscription='sub_test',status='active',expires=? "
            "WHERE workspace='alice'",
            (int(time.time()) + 3600,),
        )
    next_job = jobs.begin_operation("alice")
    assert not access.claim("alice", next_job["id"], jobs)
    for status in ["past_due", "unpaid", "canceled", "incomplete", "review_required"]:
        with closing(billing_service.connect()) as db, db:
            db.execute("UPDATE billing_wallets SET status=?", (status,))
        with pytest.raises(SubscriptionRequired):
            access.claim("alice", next_job["id"], jobs)
    with closing(billing_service.connect()) as db, db:
        db.execute("UPDATE billing_wallets SET status='active',expires=0")
    with pytest.raises(SubscriptionRequired):
        access.claim("alice", next_job["id"], jobs)


def test_free_run_waives_wallet_not_usage_limits(account_store, tmp_path, monkeypatch):
    from config import OPENAI_MODEL
    from services.billing_service import billing_service

    monkeypatch.setenv("BILLING_ENABLED", "true")
    monkeypatch.setenv("API_JOB_MAX_TOKENS", "20000")
    monkeypatch.setenv("PRICED_MODEL", OPENAI_MODEL)
    monkeypatch.setenv("MODEL_INPUT_USD_PER_MILLION", "10")
    monkeypatch.setenv("MODEL_OUTPUT_USD_PER_MILLION", "30")
    jobs = JobStore(tmp_path / "jobs.sqlite3")
    job = jobs.begin_operation("alice")
    AnalysisAccess().claim("alice", job["id"], jobs)
    callback = UsageCallback(jobs, job)
    run_id = uuid4()
    callback.on_chat_model_start(
        {},
        [[HumanMessage(content="stone counters")]],
        run_id=run_id,
        invocation_params={"max_tokens": 100},
    )
    assert jobs.get(job["id"], "alice")["reserved_cost"] > 0
    assert not callback.billing_reservations
    callback.on_llm_end(
        SimpleNamespace(llm_output={"token_usage": {"prompt_tokens": 10, "completion_tokens": 5}}),
        run_id=run_id,
    )
    assert jobs.get(job["id"], "alice")["cost"] > 0
    assert billing_service.get_balance("alice")["balance_usd"] == 0
    with pytest.raises(RuntimeError, match="limit"):
        callback.on_chat_model_start(
            {},
            [[HumanMessage(content="x" * 20001)]],
            run_id=uuid4(),
            invocation_params={"max_tokens": 100},
        )


def test_graph_reserves_before_queue_and_shares_trial(
    account_store, test_client, sample_company_info, monkeypatch
):
    account_store.create("customer@example.test", "long-test-account-password", "customer")
    headers = sign_in(test_client)
    runtime = app_module.get_runtime()
    monkeypatch.setattr(runtime.worker, "start", lambda: None)
    payload = {
        "company_name": sample_company_info["company_name"],
        "industry": sample_company_info["industry"],
        "location": sample_company_info["location"],
        "total_budget": 5000,
        "target_days": 90,
        "objectives": ["Review website"],
        "website": "https://example.com",
    }
    response = test_client.post("/api/graph/execute", json=payload, headers=headers)
    assert response.status_code == 202
    with test_client.session_transaction() as session:
        owner = account_store.resolve(session["auth_token"])["id"]
    job = runtime.store.get(response.json["job_id"], owner)
    assert job["status"] == "queued"
    assert job["payload"]["website"] == "https://example.com/"
    assert AnalysisAccess().is_free(owner, job["id"])
    response = test_client.post("/api/ceo/analyze", json=sample_company_info, headers=headers)
    assert response.status_code == 409
    runtime.store.cancel(job["id"], owner)
    assert test_client.get("/api/account/access").json["free_analysis_available"]
    response = test_client.post("/api/graph/execute", json=payload, headers=headers)
    assert response.status_code == 202
    claimed = runtime.store.claim()
    assert claimed["id"] == response.json["job_id"]
    monkeypatch.setattr(runtime, "graph_execute", lambda **kwargs: {"artifacts": []})
    result = runtime.execute(claimed)
    assert result["free_analysis_completed"]
    runtime.store.finish(claimed, result=result)
    assert test_client.post("/api/graph/execute", json=payload, headers=headers).status_code == 402


def test_frontend_sends_website_and_shows_trial_popup_once():
    script = (Path(__file__).resolve().parents[1] / "static/js/app.js").read_text()
    functions = "\n".join(
        start + script.split(start, 1)[1].split(end, 1)[0]
        for start, end in [
            ("async function analyzeObjectives()", "async function runFullOrchestration()"),
            ("async function runFullOrchestration()", "async function executeAgent("),
            ("async function executeAgent(", "async function viewAgentDetails("),
            ("async function showTrialComplete(", "async function fetchWalletBalance()"),
        ]
    )
    harness = """
const assert = require('node:assert/strict');
const ACCOUNT_SCOPE = 'customer';
const scenario = {company_name:'Stone',industry:'Manufacturing',location:'Ohio',
    budget:5000,timeline:90,objectives:['Review website'],website:'https://example.com/'};
const state = {};
const stored = new Map();
const localStorage = {getItem:key=>stored.get(key),setItem:(key,value)=>stored.set(key,value)};
const ACTIVE_JOB_STORAGE_KEY = 'job';
const persistScenarioToStorage = () => scenario;
const validateScenarioForExecution = () => true;
const updateStatus = () => {};
const addLogEntry = () => {};
const addChatMessage = () => {};
const displayTasks = () => {};
const updateBudgetDisplay = () => {};
const displayAnalysisReport = () => {};
const showWebsiteEvidence = () => {};
const highlightAgent = () => {};
const watchDurableJob = () => {};
let popups = 0;
const openTopUpModal = async () => {popups++};
const requests = [];
const fetch = async (url, options) => {
    requests.push({url,payload:JSON.parse(options.body)});
    return {ok:true,status:200,json:async()=>url==='/api/ceo/analyze'
        ? {success:true,tasks:[],budget_allocation:{},free_analysis_completed:true}
        : {success:true,thread_id:'graph',job_id:'graph'}};
};
"""
    harness += (
        functions
        + """
(async () => {
    await analyzeObjectives();
    await analyzeObjectives();
    assert.equal(popups, 1);
    await runFullOrchestration();
    await executeAgent('ceo');
    assert.equal(requests.length, 4);
    requests.forEach(({payload})=>assert.equal(payload.website, scenario.website));
})().catch(error=>{console.error(error);process.exitCode=1});
"""
    )
    result = subprocess.run(["node", "-e", harness], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
