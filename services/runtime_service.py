"""Private local job, approval, and memory API integration."""

import hashlib
import logging
import importlib
import os
import zipfile
from contextlib import contextmanager
from contextlib import closing
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file

from services.job_service import JobStore, JobWorker
from services.memory_service import MemoryService, scenario_key
from services.usage_service import UsageCallback, active_usage
from exceptions import ValidationError

logger = logging.getLogger(__name__)


class RuntimeService:
    def __init__(self, root, graph_execute):
        self.root = Path(root)
        self.store = JobStore(self.root / "jobs.sqlite3")
        self.store.recover()
        self.memory = MemoryService(self.root / "memory")
        self.graph_execute = graph_execute
        self.worker = JobWorker(self.store, self.execute)
        with closing(self.store.connect()) as db, db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS memory_policy(key TEXT PRIMARY KEY, enabled INTEGER)"
            )

    def memory_enabled(self, key):
        with closing(self.store.connect()) as db:
            row = db.execute("SELECT enabled FROM memory_policy WHERE key=?", (key,)).fetchone()
        return bool(row and row["enabled"])

    def set_memory(self, key, enabled):
        if enabled:
            importlib.import_module("mempalace.backends.sqlite_exact")
        with closing(self.store.connect()) as db, db:
            db.execute(
                "INSERT INTO memory_policy VALUES(?,?) ON CONFLICT(key) "
                "DO UPDATE SET enabled=excluded.enabled",
                (key, int(enabled)),
            )

    def submit(self, owner, payload):
        job = self.store.create(owner, "graph", payload)
        self.worker.start()
        return job

    @contextmanager
    def operation(self, owner):
        if active_usage.get() is not None:
            yield
            return
        job = self.store.begin_operation(owner)
        token = active_usage.set(UsageCallback(self.store, job))
        try:
            yield
        except Exception as exc:
            self.store.finish(job, error=str(exc))
            raise
        else:
            self.store.finish(job, result={"operation": "model_call"})
        finally:
            active_usage.reset(token)

    def execute(self, job):
        if job["kind"] == "export":
            return self.export(job)
        if job["kind"] == "test_request":
            from services.build_service import prepare_runner_request

            return prepare_runner_request(self.store, job)
        callback = UsageCallback(self.store, job)
        token = active_usage.set(callback)
        try:
            if job["kind"] == "build":
                from services.build_service import generate_source

                return generate_source(job["payload"])
            result = self.graph_execute(**job["payload"], thread_id=f'{job["owner"]}:{job["id"]}')
            return result
        finally:
            active_usage.reset(token)

    def propose_export(self, owner, source_id):
        source = self.store.get(source_id, owner)
        if source["status"] != "succeeded" or source["kind"] not in {"graph", "build"}:
            raise ValueError("Only a succeeded graph or source-build job can be exported")
        if not (source["result"] or {}).get("artifacts"):
            raise ValueError("No artifacts to export")
        return self.store.create(owner, "export", {"source_job": source_id}, approval=True)

    def export(self, job):
        source = self.store.get(job["payload"]["source_job"], job["owner"])
        from services.artifact_service import artifact_service

        artifact_root = artifact_service.output_root.resolve()
        export_dir = self.root / "exports"
        export_dir.mkdir(mode=0o700, exist_ok=True)
        output = export_dir / f'{job["id"]}.zip'
        temporary = output.with_suffix(".tmp")
        try:
            with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as bundle:
                for index, entry in enumerate(source["result"]["artifacts"]):
                    path = (artifact_service.static_root / entry["path"]).resolve()
                    if not path.is_relative_to(artifact_root) or not path.is_file():
                        raise ValueError("Artifact outside the allowed output directory")
                    content = path.read_bytes()
                    if hashlib.sha256(content).hexdigest() != entry["sha256"]:
                        raise ValueError("Artifact changed since execution; export rejected")
                    bundle.writestr(f"{index:03d}_{path.name}", content)
            temporary.chmod(0o600)
            os.replace(temporary, output)
        finally:
            temporary.unlink(missing_ok=True)
        return {
            "connector": "local_export",
            "external_actions_executed": False,
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "size_bytes": output.stat().st_size,
            "source_job": source["id"],
        }


def runtime_blueprint(runtime_getter, owner_getter, normalize, protect):
    bp = Blueprint("runtime", __name__)

    def json_body():
        body = request.get_json() or {}
        if not isinstance(body, dict):
            raise ValueError("Request body must be a JSON object")
        return body

    def memory_scope(body):
        scenario = body.get("scenario", {})
        agent = body.get("agent", "ceo")
        if not isinstance(scenario, dict) or not isinstance(agent, str) or not agent.strip():
            raise ValueError("scenario must be an object and agent must be non-empty text")
        return scenario_key(owner_getter(), agent, normalize(scenario, scenario.get("objectives")))

    @bp.before_request
    def start_worker():
        runtime_getter().worker.start()

    @bp.errorhandler(LookupError)
    def missing(exc):
        return jsonify(success=False, error=str(exc)), 404

    @bp.errorhandler(ValueError)
    @bp.errorhandler(ValidationError)
    def invalid(exc):
        logger.warning("Invalid runtime request: %s", exc)
        return jsonify(success=False, error=str(exc)), 400

    @bp.errorhandler(ImportError)
    def unavailable(exc):
        logger.error("Memory dependency unavailable", exc_info=True)
        return jsonify(success=False, error="Install requirements-memory.txt to enable memory"), 503

    @bp.route("/api/jobs/<identifier>", methods=["GET"])
    @protect
    def status(identifier):
        job = runtime_getter().store.get(identifier, owner_getter())
        return jsonify(success=True, job=job)

    @bp.route("/api/jobs/<identifier>/cancel", methods=["POST"])
    @protect
    def cancel(identifier):
        runtime_getter().store.cancel(identifier, owner_getter())
        return jsonify(success=True)

    @bp.route("/api/builds/propose", methods=["POST"])
    @protect
    def propose_build():
        body = json_body()
        if set(body) != {"scenario"}:
            raise ValueError("Only scenario is accepted")
        from services.state_builder import CFOStateBuilder

        state = CFOStateBuilder.create_from_request(body["scenario"])
        scenario = {
            "company_name": state["company_name"],
            "industry": state["industry"],
            "location": state["location"],
            "budget": state["total_budget"],
            "timeline": state["target_completion_days"],
            "objectives": state["strategic_objectives"],
        }
        job = runtime_getter().store.create(
            owner_getter(), "build", {"scenario": scenario}, approval=True
        )
        return jsonify(success=True, job=job), 202

    @bp.route("/api/builds/<identifier>/propose-tests", methods=["POST"])
    @protect
    def propose_tests(identifier):
        if json_body():
            raise ValueError("Test requests do not accept command or runner overrides")
        runtime = runtime_getter()
        source = runtime.store.get(identifier, owner_getter())
        if source["kind"] != "build" or source["status"] != "succeeded":
            raise ValueError("A succeeded source build is required")
        job = runtime.store.create(
            owner_getter(),
            "test_request",
            {"source_job": identifier, "source_artifacts": source["result"]["artifacts"]},
            approval=True,
        )
        return jsonify(success=True, job=job), 202

    @bp.route("/api/jobs/<identifier>/runner-request", methods=["GET"])
    @protect
    def runner_request(identifier):
        job = runtime_getter().store.get(identifier, owner_getter())
        if job["kind"] != "test_request" or job["status"] != "succeeded":
            raise ValueError("Approved runner request is not ready")
        response = jsonify(job["result"])
        response.headers["Content-Disposition"] = 'attachment; filename="runner-request.json"'
        return response

    @bp.route("/api/connectors/local-export", methods=["POST"])
    @protect
    def propose():
        body = json_body()
        source = body.get("source_job")
        if not isinstance(source, str):
            raise ValueError("source_job is required")
        job = runtime_getter().propose_export(owner_getter(), source)
        return jsonify(success=True, job=job), 202

    @bp.route("/api/jobs/<identifier>/approve", methods=["POST"])
    @protect
    def approve(identifier):
        runtime = runtime_getter()
        runtime.store.approve(identifier, owner_getter())
        runtime.worker.start()
        return jsonify(success=True)

    @bp.route("/api/jobs/<identifier>/download", methods=["GET"])
    @protect
    def download(identifier):
        runtime = runtime_getter()
        job = runtime.store.get(identifier, owner_getter())
        if job["kind"] != "export" or job["status"] != "succeeded":
            raise ValueError("Export is not ready")
        path = runtime.root / "exports" / f"{identifier}.zip"
        if hashlib.sha256(path.read_bytes()).hexdigest() != job["result"]["sha256"]:
            raise ValueError("Export receipt mismatch")
        return send_file(path, as_attachment=True, download_name=f"{identifier}.zip")

    @bp.route("/api/memory/policy", methods=["POST"])
    @protect
    def policy():
        body = json_body()
        enabled = body.get("enabled")
        if not isinstance(enabled, bool):
            raise ValueError("enabled must be boolean")
        key = memory_scope(body)
        runtime_getter().set_memory(key, enabled)
        return jsonify(success=True, enabled=enabled)

    @bp.route("/api/memory/status", methods=["POST"])
    @protect
    def memory_status():
        key = memory_scope(json_body())
        return jsonify(success=True, enabled=runtime_getter().memory_enabled(key))

    @bp.route("/api/memory/clear", methods=["POST"])
    @protect
    def clear():
        key = memory_scope(json_body())
        runtime = runtime_getter()
        runtime.set_memory(key, False)
        runtime.memory.clear(key)
        return jsonify(success=True, enabled=False)

    return bp
