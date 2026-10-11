"""Approved source generation and offline handoff to a future isolated runner."""

import ast
import hashlib
import json

from pydantic import BaseModel, ConfigDict, Field

from services.state_builder import CFOStateBuilder


class SourceFile(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    path: str
    content: str = Field(min_length=1, max_length=60000)


class SourceBundle(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    files: list[SourceFile] = Field(min_length=3, max_length=3)


def validate_source_bundle(data):
    bundle = SourceBundle.model_validate(data)
    names = [file.path for file in bundle.files]
    if len(set(names)) != 3 or set(names) != {"tool.py", "test_tool.py", "README.md"}:
        raise ValueError("Build must contain exactly tool.py, test_tool.py and README.md")
    if sum(len(file.content.encode("utf-8")) for file in bundle.files) > 120000:
        raise ValueError("Build source exceeds 120000 bytes")
    for file in bundle.files:
        if "\x00" in file.content:
            raise ValueError("Source contains a null byte")
        if file.path.endswith(".py"):
            # Parsing verifies syntax only: generated source is never imported or executed.
            ast.parse(file.content, filename=file.path)
    return bundle


def generate_source(payload):
    from graph_architecture.llm_nodes import _call_structured, _get_llm
    from services.artifact_service import artifact_service

    state = CFOStateBuilder.create_from_request(payload["scenario"])
    prompt = (
        "Generate actual complete Python CLI source, not an architecture report. "
        "Return only JSON with files:[{path,content}]. Exactly three files: tool.py, "
        "test_tool.py, README.md. Use Python standard library only, unittest tests "
        "with real assertions and explicit expected outputs. No installation, network "
        "access, credentials, subprocesses, or external actions. Document CLI usage "
        "and scope limitations. Source has not been executed; never claim tests passed."
    )
    data = _call_structured(_get_llm(max_tokens=6000), prompt, json.dumps({"scenario": state}))
    bundle = validate_source_bundle(data)
    result = {
        "execution_mode": "source_files",
        "status": "source_generated",
        "tests_status": "not_run",
        "external_actions_executed": False,
        "source_files": [file.model_dump() for file in bundle.files],
        "deliverables": [file.path for file in bundle.files],
    }
    receipt = artifact_service.persist_agent_execution(
        agent_type="python_build",
        agent_name="Python Source Build",
        task="; ".join(state["strategic_objectives"]),
        company_info=state,
        result=result,
    )
    return {
        **{key: value for key, value in result.items() if key != "source_files"},
        "artifacts": receipt["artifacts"],
        "artifact_run_id": receipt["run_id"],
    }


def prepare_runner_request(store, job):
    """Create a reviewable request; no remote runner or execution is implemented."""
    from services.artifact_service import artifact_service

    source = store.get(job["payload"]["source_job"], job["owner"])
    if source["kind"] != "build" or source["status"] != "succeeded":
        raise ValueError("A succeeded source build is required")
    entries = source["result"]["artifacts"]
    expected = job["payload"]["source_artifacts"]
    if entries != expected:
        raise ValueError("Build receipt changed after test-request proposal")
    for entry in entries:
        artifact_service.authorized_file(entry["path"], job["owner"])
    receipt_hash = hashlib.sha256(
        json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    request = {
        "protocol_version": 1,
        "source_job": source["id"],
        "source_receipt_sha256": receipt_hash,
        "files": [
            {"path": entry["path"], "sha256": entry["sha256"], "size_bytes": entry["size_bytes"]}
            for entry in entries
            if entry["title"] in {"tool.py", "test_tool.py", "README.md"}
        ],
        "test_command": [
            "python3",
            "-I",
            "-m",
            "unittest",
            "discover",
            "-s",
            ".",
            "-p",
            "test_tool.py",
        ],
        "isolation_requirements": {
            "disposable_worker": True,
            "network": "deny_all_including_instance_metadata",
            "credentials": "none",
            "uid": "non_root",
            "cpu_count": 1,
            "memory_mib": 512,
            "process_limit": 32,
            "wall_seconds": 60,
            "output_bytes": 1048576,
            "workspace_bytes": 16777216,
            "host_mounts": "none",
        },
        "runner_status": "not_configured",
        "tests_status": "not_run",
    }
    if len(request["files"]) != 3:
        raise ValueError("Source receipt does not contain the required three build files")
    return request
