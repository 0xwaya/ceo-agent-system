"""Single-process durable job queue. Interrupted work is never silently replayed."""

import json
import sqlite3
import threading
import logging
import os
import math
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def timestamp():
    return datetime.now(timezone.utc).isoformat()


class JobStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.parent.chmod(0o700)
        with closing(self.connect()) as db, db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS jobs(
                    id TEXT PRIMARY KEY, owner TEXT NOT NULL, kind TEXT NOT NULL,
                    status TEXT NOT NULL, payload TEXT NOT NULL, result TEXT,
                    error TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    max_tokens INTEGER NOT NULL, max_cost REAL NOT NULL,
                    tokens INTEGER NOT NULL DEFAULT 0, cost REAL NOT NULL DEFAULT 0,
                    reserved_tokens INTEGER NOT NULL DEFAULT 0,
                    reserved_cost REAL NOT NULL DEFAULT 0,
                    cancel_requested INTEGER NOT NULL DEFAULT 0
                );
            """
            )
        self.path.chmod(0o600)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def usage_limits():
        from services.billing_service import billing_service

        max_cost = float(
            os.getenv("API_JOB_MAX_COST_USD", "5" if billing_service.enabled() else "1")
        )
        max_tokens = int(
            os.getenv("API_JOB_MAX_TOKENS", "100000" if billing_service.enabled() else "20000")
        )
        if not math.isfinite(max_cost) or max_cost <= 0 or max_tokens <= 0:
            raise ValueError("Positive finite job spending and token limits are required")
        return max_cost, max_tokens

    def create(self, owner, kind, payload, approval=False):
        max_cost, max_tokens = self.usage_limits()
        identifier = uuid4().hex
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            pending = db.execute(
                "SELECT COUNT(*) FROM jobs WHERE owner=? "
                "AND status IN('queued','running','awaiting_approval')",
                (owner,),
            ).fetchone()[0]
            if pending >= 100:
                raise ValueError("Pending job limit reached")
            db.execute(
                "INSERT INTO jobs(id,owner,kind,status,payload,created_at,updated_at,"
                "max_tokens,max_cost) VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    identifier,
                    owner,
                    kind,
                    "running"
                    if kind == "usage"
                    else ("awaiting_approval" if approval else "queued"),
                    json.dumps(payload),
                    timestamp(),
                    timestamp(),
                    max_tokens,
                    max_cost,
                ),
            )
        return self.get(identifier, owner)

    def get(self, identifier, owner):
        with closing(self.connect()) as db:
            row = db.execute(
                "SELECT * FROM jobs WHERE id=? AND owner=?", (identifier, owner)
            ).fetchone()
        if row is None:
            raise LookupError("Job not found")
        result = dict(row)
        for field in ("payload", "result"):
            result[field] = json.loads(result[field]) if result[field] else None
        return result

    def recover(self):
        with closing(self.connect()) as db, db:
            db.execute(
                "UPDATE jobs SET status='interrupted',error=?,updated_at=? WHERE status='running'",
                (
                    "Worker stopped; inspect partial artifacts before submitting new work",
                    timestamp(),
                ),
            )

    def claim(self):
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM jobs WHERE status='queued' "
                "AND kind IN('graph','export','build','test_request') "
                "ORDER BY created_at LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            db.execute(
                "UPDATE jobs SET status='running',updated_at=? WHERE id=?",
                (timestamp(), row["id"]),
            )
        return self.get(row["id"], row["owner"])

    def finish(self, job, result=None, error=None):
        with closing(self.connect()) as db, db:
            db.execute(
                "UPDATE jobs SET status=CASE WHEN cancel_requested=1 THEN 'cancelled' "
                "ELSE ? END,result=?,error=?,updated_at=? WHERE id=?",
                (
                    "failed" if error else "succeeded",
                    json.dumps(result),
                    error,
                    timestamp(),
                    job["id"],
                ),
            )
        if job["kind"] in {"graph", "usage"}:
            from services.analysis_access import AnalysisAccess

            completed = self.get(job["id"], job["owner"])
            AnalysisAccess().finish(job["id"], completed["status"] == "succeeded")

    def begin_operation(self, owner):
        return self.create(owner, "usage", {})

    def approve(self, identifier, owner):
        with closing(self.connect()) as db, db:
            changed = db.execute(
                "UPDATE jobs SET status='queued',updated_at=? "
                "WHERE id=? AND owner=? AND status='awaiting_approval'",
                (timestamp(), identifier, owner),
            ).rowcount
        if not changed:
            raise ValueError("Job is not awaiting approval")

    def cancel(self, identifier, owner):
        with closing(self.connect()) as db, db:
            changed = db.execute(
                "UPDATE jobs SET cancel_requested=1,status=CASE "
                "WHEN status='running' THEN status ELSE 'cancelled' END,updated_at=? "
                "WHERE id=? AND owner=? AND status IN('queued','awaiting_approval','running')",
                (timestamp(), identifier, owner),
            ).rowcount
        if not changed:
            raise ValueError("Job cannot be cancelled")

    def reserve(self, job, tokens, cost):
        with closing(self.connect()) as db, db:
            changed = db.execute(
                "UPDATE jobs SET reserved_tokens=reserved_tokens+?,reserved_cost=reserved_cost+? "
                "WHERE id=? AND status='running' AND cancel_requested=0 "
                "AND tokens+reserved_tokens+?<=max_tokens "
                "AND cost+reserved_cost+?<=max_cost",
                (tokens, cost, job["id"], tokens, cost),
            ).rowcount
        if not changed:
            raise RuntimeError("Job cancelled or API token/cost limit reached")

    def settle(self, job, reserved_tokens, reserved_cost, tokens, cost):
        with closing(self.connect()) as db, db:
            db.execute(
                "UPDATE jobs SET reserved_tokens=reserved_tokens-?,reserved_cost=reserved_cost-?,"
                "tokens=tokens+?,cost=cost+? WHERE id=?",
                (reserved_tokens, reserved_cost, tokens, cost, job["id"]),
            )
        if tokens > reserved_tokens or cost > reserved_cost:
            raise RuntimeError("Provider exceeded reserved usage; job stopped")


class JobWorker:
    def __init__(self, store, execute):
        self.store = store
        self.execute = execute
        self.lock = threading.Lock()
        self.thread = None
        self.wake = threading.Event()

    def start(self):
        with self.lock:
            if self.thread is None:
                self.thread = threading.Thread(target=self.run, daemon=True)
                self.thread.start()
            self.wake.set()

    def run(self):
        while True:
            self.wake.wait(1)
            self.wake.clear()
            job = self.store.claim()
            if job is None:
                continue
            try:
                result = self.execute(job)
                self.store.finish(job, result=result)
            except Exception as exc:
                logging.getLogger(__name__).exception("Durable job failed: %s", job["id"])
                self.store.finish(job, error=str(exc))
