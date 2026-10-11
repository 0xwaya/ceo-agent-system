"""Source persistence and approvals never execute model-generated code."""

import json

import pytest

import app as app_module
from services.build_service import validate_source_bundle


@pytest.fixture
def bundle():
    return {
        "files": [
            {"path": "tool.py", "content": "def validate(value):\n    return bool(value)\n"},
            {
                "path": "test_tool.py",
                "content": (
                    "import unittest\nfrom tool import validate\n"
                    "class Tests(unittest.TestCase):\n"
                    "    def test_empty(self):\n        self.assertFalse(validate(''))\n"
                ),
            },
            {"path": "README.md", "content": "# Tool\nGenerated source; tests not run.\n"},
        ]
    }


@pytest.mark.parametrize(
    "path", ["../tool.py", "/tmp/tool.py", "subdir/tool.py", ".env", "bundle.json", "test.py"]
)
def test_build_rejects_unsafe_or_unexpected_paths(bundle, path):
    bundle["files"][0]["path"] = path
    with pytest.raises(ValueError):
        validate_source_bundle(bundle)


def test_build_rejects_duplicate_paths_and_invalid_syntax(bundle):
    bundle["files"][0]["path"] = "test_tool.py"
    with pytest.raises(ValueError):
        validate_source_bundle(bundle)
    bundle["files"][0]["path"] = "tool.py"
    bundle["files"][0]["content"] = "def invalid("
    with pytest.raises(SyntaxError):
        validate_source_bundle(bundle)


def test_source_is_parsed_not_executed(bundle, tmp_path):
    marker = tmp_path / "must-not-exist"
    bundle["files"][0]["content"] = f"open({str(marker)!r}, 'w').write('unsafe')\n"
    validate_source_bundle(bundle)
    assert not marker.exists()


def test_source_bundle_size_limit(bundle):
    for file in bundle["files"]:
        file["content"] = "#" + "a" * 45000
    with pytest.raises(ValueError, match="120000"):
        validate_source_bundle(bundle)


def test_approved_build_and_separate_runner_request(test_client, monkeypatch, bundle):
    from graph_architecture import llm_nodes

    runtime = app_module.get_runtime()
    monkeypatch.setattr(runtime.worker, "start", lambda: None)
    calls = []
    monkeypatch.setattr(llm_nodes, "_get_llm", lambda **kwargs: object())

    def generated(*args):
        calls.append(args)
        return bundle

    monkeypatch.setattr(llm_nodes, "_call_structured", generated)
    scenario = {
        "company_name": "Source test",
        "industry": "Software",
        "location": "Local",
        "budget": 2500,
        "timeline": 14,
        "objectives": ["Validate a CSV"],
    }
    response = test_client.post("/api/builds/propose", json={"scenario": scenario})
    assert response.status_code == 202
    job = response.json["job"]
    assert job["status"] == "awaiting_approval"
    assert runtime.store.claim() is None
    assert calls == []
    with app_module.app.test_client() as other:
        assert other.get(f'/api/jobs/{job["id"]}').status_code == 404
        assert other.post(f'/api/jobs/{job["id"]}/approve', json={}).status_code == 400
    assert test_client.post(f'/api/jobs/{job["id"]}/approve', json={}).status_code == 200
    claimed = runtime.store.claim()
    result = runtime.execute(claimed)
    runtime.store.finish(claimed, result=result)
    assert len(calls) == 1
    assert result["tests_status"] == "not_run"
    assert result["deliverables"] == ["tool.py", "test_tool.py", "README.md"]
    for file in bundle["files"]:
        entry = next(item for item in result["artifacts"] if item["title"] == file["path"])
        download = test_client.get(entry["url"])
        assert download.status_code == 200
        assert download.data.decode() == file["content"]
    test_response = test_client.post(f'/api/builds/{job["id"]}/propose-tests', json={})
    test_job = test_response.json["job"]
    assert test_job["status"] == "awaiting_approval"
    assert runtime.store.claim() is None
    assert test_client.get(f'/api/jobs/{test_job["id"]}/runner-request').status_code == 400
    test_client.post(f'/api/jobs/{test_job["id"]}/approve', json={})
    claimed = runtime.store.claim()
    request = runtime.execute(claimed)
    runtime.store.finish(claimed, result=request)
    assert request["tests_status"] == "not_run"
    assert request["runner_status"] == "not_configured"
    assert len(request["files"]) == 3
    assert request["isolation_requirements"]["credentials"] == "none"
    assert "deny_all" in request["isolation_requirements"]["network"]
    download = test_client.get(f'/api/jobs/{test_job["id"]}/runner-request')
    assert download.status_code == 200
    assert json.loads(download.data) == request
    assert len(calls) == 1  # Preparing the runner request makes no model or remote call.
    entry = next(item for item in result["artifacts"] if item["title"] == "tool.py")
    path = app_module.artifact_service.static_root / entry["path"]
    path.write_text("changed")
    with pytest.raises(ValueError, match="mismatch"):
        runtime.execute(claimed)
    export = runtime.propose_export(job["owner"], job["id"])
    assert export["status"] == "awaiting_approval"


def test_build_rejects_overrides_and_incomplete_scenarios(test_client):
    assert test_client.post("/api/builds/propose", json={"scenario": {}}).status_code == 400
    assert (
        test_client.post("/api/builds/propose", json={"scenario": {}, "command": "sh"}).status_code
        == 400
    )


def test_job_ui_never_claims_runner_tests_executed():
    import subprocess
    from pathlib import Path

    script = (Path(__file__).resolve().parents[1] / "static/js/app.js").read_text()
    function = script.split("async function watchDurableJob(identifier)", 1)[1]
    function = function.split("async function cancelCurrentJob", 1)[0]
    harness = """
const assert = require('node:assert/strict');
let jobPollTimer;
const state = {};
const elements = {};
const document = {getElementById: id => elements[id] ||= {}};
let job;
let statuses = [];
let reports = [];
const updateStatus = message => statuses.push(message);
const hideProgressBar = () => {};
const addChatMessage = message => {throw new Error(message)};
const runtimeRequest = async () => ({job});
const displayAgentReport = (agent, result, company) => reports.push({result,company});
"""
    harness += "async function watchDurableJob(identifier)" + function
    harness += """
(async () => {
    const base = {cost:0,tokens:0,max_cost:1,max_tokens:20000,
        reserved_tokens:0,reserved_cost:0};
    job = {...base,kind:'build',status:'awaiting_approval'};
    await watchDurableJob('proposal');
    assert.equal(elements.jobApprove.hidden,false);
    assert.equal(reports.length,0);
    job = {...base,kind:'build',status:'succeeded',
        payload:{scenario:{company_name:'Real source'}},
        result:{deliverables:['tool.py','test_tool.py','README.md']}};
    await watchDurableJob('build');
    assert.equal(elements.jobTests.hidden,false);
    assert.equal(reports[0].result.status,'Source generated · Tests NOT run');
    assert.equal(reports[0].company.company_name,'Real source');
    job = {...base,kind:'test_request',status:'succeeded'};
    await watchDurableJob('tests');
    assert.equal(reports.length,1);
    assert(statuses.at(-1).includes('Tests NOT run'));
    assert.equal(elements.runnerRequestLink.hidden,false);
    assert.equal(elements.runnerRequestLink.href,'/api/jobs/tests/runner-request');
})().catch(error => {console.error(error);process.exitCode=1;});
"""
    result = subprocess.run(["node", "-e", harness], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
