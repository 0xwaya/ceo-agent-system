"""Named local accounts, revocable sessions, and same-origin request protection."""

import hashlib
import logging
import secrets
import sqlite3
import time
from contextlib import closing
from pathlib import Path

import click
from flask import g, has_request_context, jsonify, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

logger = logging.getLogger(__name__)


class AuthStore:
    def __init__(self, root):
        self.path = Path(root) / "accounts.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path.parent.chmod(0o700)
        with closing(self.connect()) as db, db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS accounts(
                    id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL, role TEXT NOT NULL, enabled INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions(
                    token TEXT PRIMARY KEY, account TEXT NOT NULL, expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS attempts(
                    key TEXT PRIMARY KEY, count INTEGER NOT NULL, expires REAL NOT NULL);
                """
            )
        self.path.chmod(0o600)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def create(self, email, password, role):
        email = email.strip().lower()
        if "@" not in email or len(email) > 254 or role not in {"admin", "reviewer"}:
            raise ValueError("Valid email and admin/reviewer role required")
        if len(password) < 14 or len(password) > 256:
            raise ValueError("Password must contain 14 to 256 characters")
        with closing(self.connect()) as db, db:
            db.execute(
                "INSERT INTO accounts VALUES(?,?,?,?,1)",
                (secrets.token_hex(16), email, generate_password_hash(password), role),
            )

    def revoke(self, email):
        with closing(self.connect()) as db, db:
            account = db.execute(
                "SELECT id FROM accounts WHERE email=?", (email.strip().lower(),)
            ).fetchone()
            if account is None:
                raise ValueError("Account not found")
            db.execute("UPDATE accounts SET enabled=0 WHERE id=?", (account["id"],))
            db.execute("DELETE FROM sessions WHERE account=?", (account["id"],))

    def login(self, email, password, address):
        if len(email) > 254 or len(password) > 256:
            raise ValueError("Invalid credentials")
        now = time.time()
        key = hashlib.sha256(address.encode()).hexdigest()
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM attempts WHERE expires<=?", (now,))
            attempt = db.execute("SELECT count FROM attempts WHERE key=?", (key,)).fetchone()
            if attempt and attempt["count"] >= 5:
                raise PermissionError("Too many login attempts; try again in 15 minutes")
            db.execute(
                "INSERT INTO attempts VALUES(?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1",
                (key, now + 900),
            )
        with closing(self.connect()) as db:
            account = db.execute(
                "SELECT * FROM accounts WHERE email=?", (email.strip().lower(),)
            ).fetchone()
        # Use the same expensive password check for unknown accounts.
        valid = check_password_hash(account["password"] if account else _DUMMY_HASH, password)
        if not account or not valid or not account["enabled"]:
            logger.warning("Rejected account login")
            raise ValueError("Invalid credentials")
        token = secrets.token_urlsafe(32)
        with closing(self.connect()) as db, db:
            db.execute("DELETE FROM sessions WHERE expires<=?", (now,))
            db.execute(
                "INSERT INTO sessions VALUES(?,?,?)", (_digest(token), account["id"], now + 28800)
            )
        return token

    def resolve(self, token):
        if not isinstance(token, str):
            return None
        with closing(self.connect()) as db:
            account = db.execute(
                "SELECT a.id,a.email,a.role FROM accounts a JOIN sessions s ON a.id=s.account "
                "WHERE s.token=? AND s.expires>? AND a.enabled=1",
                (_digest(token), time.time()),
            ).fetchone()
        return dict(account) if account else None

    def logout(self, token):
        with closing(self.connect()) as db, db:
            db.execute("DELETE FROM sessions WHERE token=?", (_digest(token),))


def _digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


_DUMMY_HASH = generate_password_hash(secrets.token_urlsafe(32))


def install_auth(app, store_getter):
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        SESSION_COOKIE_SECURE=app.config.get("SESSION_COOKIE_SECURE", False),
    )

    def csrf():
        if not has_request_context():
            return ""
        if "csrf" not in session:
            session["csrf"] = secrets.token_urlsafe(32)
        return session["csrf"]

    app.jinja_env.globals["csrf_token"] = csrf

    @app.before_request
    def authorize():
        # Stripe has no browser session; the billing route verifies the signed raw body.
        if request.path == "/api/billing/webhook" and request.method == "POST":
            return None
        # Historical artifacts never have a trustworthy owner.
        if request.path.startswith("/static/generated_outputs"):
            return jsonify(success=False, error="Public artifact access is disabled"), 404
        if not app.config["ACCOUNT_AUTH_ENABLED"]:
            if request.remote_addr not in {"127.0.0.1", "::1"}:
                return jsonify(success=False, error="Login-disabled access is localhost-only"), 403
            return None
        public = request.endpoint == "static" or request.path in {"/login"}
        if request.path.startswith("/socket.io"):
            return None  # Socket.IO validates the account on every event.
        g.account = store_getter().resolve(session.get("auth_token"))
        if not public and not g.account:
            if request.path.startswith("/api/"):
                return jsonify(success=False, error="Login required"), 401
            return redirect("/login")
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            supplied = request.headers.get("X-CSRF-Token") or request.form.get("csrf")
            expected = session.get("csrf")
            if not supplied or not expected or not secrets.compare_digest(supplied, expected):
                logger.warning("Rejected request without a valid CSRF token")
                return jsonify(success=False, error="Invalid CSRF token"), 403
        if g.account and g.account["role"] != "admin":
            if request.path == "/api/connectors/local-export":
                return jsonify(success=False, error="Tester export approval policy is on hold"), 403
            if (
                not public
                and not request.path.startswith("/api/")
                and request.path not in {"/", "/graph", "/reports", "/logout"}
            ):
                return jsonify(success=False, error="Admin access required"), 403
            if request.path.endswith("/approve"):
                return jsonify(success=False, error="Admin approval required"), 403
            allowed = (
                "/api/graph/execute",
                "/api/ceo/analyze",
                "/api/agents/available",
                "/api/scenario/current",
                "/api/chat/message",
                "/api/chat/clear",
                "/api/connectors/local-export",
            )
            prefixes = (
                "/api/jobs/",
                "/api/memory/",
                "/api/artifacts/",
                "/api/agent/execute/",
                "/api/billing/",
            )
            if request.path.startswith("/api/") and not (
                request.path in allowed or request.path.startswith(prefixes)
            ):
                return jsonify(success=False, error="Admin access required"), 403

    @app.after_request
    def private_response(response):
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if not app.config["ACCOUNT_AUTH_ENABLED"]:
            return redirect("/")
        error = None
        if request.method == "POST":
            try:
                token = store_getter().login(
                    request.form.get("email", ""),
                    request.form.get("password", ""),
                    request.remote_addr or "unknown",
                )
            except PermissionError as exc:
                return render_template("login.html", error=str(exc)), 429
            except ValueError as exc:
                error = str(exc)
            else:
                session.clear()
                session["auth_token"] = token
                csrf()
                return redirect("/")
        return render_template("login.html", error=error), 401 if error else 200

    @app.post("/logout")
    def logout():
        token = session.get("auth_token")
        if token:
            store_getter().logout(token)
        session.clear()
        return redirect("/login")

    @app.cli.command("create-account")
    @click.option("--email", required=True)
    @click.option("--role", type=click.Choice(["admin", "reviewer"]), default="admin")
    def create_account(email, role):
        """Explicit local provisioning only; no registration or email whitelist."""
        password = click.prompt("Password", hide_input=True, confirmation_prompt=True)
        try:
            store_getter().create(email, password, role)
        except (ValueError, sqlite3.IntegrityError) as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo("Account created. No remote access was enabled.")

    @app.cli.command("revoke-account")
    @click.option("--email", required=True)
    def revoke_account(email):
        """Disable an account and revoke all its sessions."""
        try:
            store_getter().revoke(email)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo("Account disabled; sessions revoked.")

    return csrf
