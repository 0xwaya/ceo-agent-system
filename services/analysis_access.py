"""Persistent per-account trial reservations shared by synchronous and queued analyses."""

from contextlib import closing
import os
from pathlib import Path
import sqlite3


class SubscriptionRequired(RuntimeError):
    pass


class AnalysisInProgress(RuntimeError):
    pass


class AnalysisAccess:
    def __init__(self, path=None):
        root = Path(
            os.getenv("APP_RUNTIME_DIR", Path(__file__).resolve().parents[1] / "data/runtime")
        )
        self.path = Path(path or root / "analysis-access.sqlite3")
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with closing(self.connect()) as db, db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS trials("
                "owner TEXT PRIMARY KEY, job TEXT UNIQUE NOT NULL, status TEXT NOT NULL)"
            )
        self.path.chmod(0o600)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        return db

    def reconcile(self, owner, jobs):
        with closing(self.connect()) as db:
            row = db.execute(
                "SELECT job FROM trials WHERE owner=? AND status='running'", (owner,)
            ).fetchone()
        if row:
            job = jobs.get(row["job"], owner)
            if job["status"] in {"succeeded", "failed", "cancelled", "interrupted"}:
                self.finish(job["id"], job["status"] == "succeeded")

    def claim(self, owner, job, jobs):
        from services.billing_service import billing_service

        self.reconcile(owner, jobs)
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM trials WHERE owner=?", (owner,)).fetchone()
            if row and row["status"] == "running":
                raise AnalysisInProgress("Your free analysis is already in progress")
            if billing_service.has_active_membership(owner):
                return False
            if row:
                raise SubscriptionRequired(
                    "Your free analysis is complete. Subscribe to run another analysis."
                )
            db.execute("INSERT INTO trials VALUES(?,?,'running')", (owner, job))
        return True

    def is_free(self, owner, job):
        with closing(self.connect()) as db:
            return bool(
                db.execute(
                    "SELECT 1 FROM trials WHERE owner=? AND job=? AND status='running'",
                    (owner, job),
                ).fetchone()
            )

    def finish(self, job, success):
        with closing(self.connect()) as db, db:
            if success:
                return bool(
                    db.execute(
                        "UPDATE trials SET status='used' WHERE job=? AND status='running'", (job,)
                    ).rowcount
                )
            db.execute("DELETE FROM trials WHERE job=? AND status='running'", (job,))
        return False

    def status(self, owner, jobs):
        from services.billing_service import billing_service

        self.reconcile(owner, jobs)
        with closing(self.connect()) as db:
            row = db.execute("SELECT status FROM trials WHERE owner=?", (owner,)).fetchone()
        return {
            "free_analysis_available": row is None,
            "free_analysis_in_progress": bool(row and row["status"] == "running"),
            "free_analysis_used": bool(row and row["status"] == "used"),
            "active_membership": billing_service.has_active_membership(owner),
        }
