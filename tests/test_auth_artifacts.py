"""Offline authentication, revocation, CSRF, role and artifact boundaries."""

import re
from pathlib import Path

import pytest

import app as app_module
from services.auth_service import AuthStore


@pytest.fixture
def accounts(monkeypatch, tmp_path):
    monkeypatch.setitem(app_module.app.config, "ACCOUNT_AUTH_ENABLED", True)
    store = AuthStore(tmp_path / "auth")
    store.create("admin@example.test", "test-password-admin-only", "admin")
    store.create("reviewer@example.test", "test-password-reviewer-only", "reviewer")
    monkeypatch.setattr(app_module, "_auth_store", store)
    return store


def login(client, email="admin@example.test", password="test-password-admin-only"):
    page = client.get("/login")
    csrf = re.search(r'name="csrf" value="([^"]+)"', page.text)[1]
    response = client.post("/login", data={"email": email, "password": password, "csrf": csrf})
    assert response.status_code == 302
    with client.session_transaction() as session:
        return session["csrf"]


def test_anonymous_has_no_rest_dashboard_or_static_artifact_access(accounts, test_client):
    for path in ["/api/jobs/anything", "/api/logs", "/api/artifacts/runs", "/api/scenario/current"]:
        assert test_client.get(path).status_code == 401
    assert test_client.get("/").status_code == 302
    assert test_client.get("/static/generated_outputs/old/result.json").status_code == 404
    assert (
        test_client.post("/api/graph/execute", headers={"X-API-Key": "anything"}).status_code == 401
    )
    socket = app_module.socketio.test_client(app_module.app, flask_test_client=test_client)
    assert not socket.is_connected()


def test_login_csrf_rotation_logout_and_socket_revocation(accounts, test_client):
    assert test_client.post("/login", data={}).status_code == 403
    test_client.get("/login")
    with test_client.session_transaction() as session:
        original_csrf = session["csrf"]
        session["_id"] = "legacy-browser"
    csrf = login(test_client)
    assert csrf != original_csrf
    with test_client.session_transaction() as session:
        assert "_id" not in session
    assert test_client.post("/api/chat/clear", json={}).status_code == 403
    assert test_client.get("/api/scenario/current").status_code == 200
    socket = app_module.socketio.test_client(
        app_module.app, flask_test_client=test_client, auth={"csrf": csrf}
    )
    assert socket.is_connected()
    assert test_client.post("/logout", headers={"X-CSRF-Token": csrf}).status_code == 302
    assert test_client.get("/api/scenario/current").status_code == 401
    socket.emit("ai_chat_request", {"message": "Do not invoke a model"})
    assert not socket.is_connected()


def test_cookie_protection_and_account_scoped_browser_storage(accounts, test_client):
    response = test_client.get("/login")
    cookie = response.headers["Set-Cookie"]
    assert "HttpOnly" in cookie and "SameSite=Strict" in cookie
    login(test_client)
    body = test_client.get("/").text
    assert '<meta name="account-id" content="">' not in body
    script = (Path(__file__).resolve().parents[1] / "static/js/app.js").read_text()
    assert "ceo_agent_scenario:${ACCOUNT_SCOPE}" in script
    assert "ceo_active_job:${ACCOUNT_SCOPE}" in script


def test_reviewer_admin_boundaries_and_revoke(accounts, test_client):
    csrf = login(test_client, "reviewer@example.test", "test-password-reviewer-only")
    assert test_client.get("/api/logs").status_code == 403
    assert test_client.get("/debug").status_code == 403
    for path in ("/api/builds/propose", "/api/builds/test/propose-tests"):
        assert test_client.post(path, json={}, headers={"X-CSRF-Token": csrf}).status_code == 403
    assert (
        test_client.post(
            "/api/connectors/local-export", json={}, headers={"X-CSRF-Token": csrf}
        ).status_code
        == 403
    )
    assert (
        test_client.post(
            "/api/settings/update", json={}, headers={"X-CSRF-Token": csrf}
        ).status_code
        == 403
    )
    assert (
        test_client.post(
            "/api/jobs/test/approve", json={}, headers={"X-CSRF-Token": csrf}
        ).status_code
        == 403
    )
    accounts.revoke("reviewer@example.test")
    assert test_client.get("/api/scenario/current").status_code == 401


def test_failed_login_throttles_without_provider_calls(accounts):
    for _ in range(5):
        with pytest.raises(ValueError, match="Invalid"):
            accounts.login("unknown@example.test", "incorrect-password", "127.0.0.2")
    with pytest.raises(PermissionError):
        accounts.login("admin@example.test", "test-password-admin-only", "127.0.0.2")


def test_private_artifact_owner_hash_and_download(accounts, test_client):
    login(test_client)
    with app_module.app.test_request_context("/"):
        from flask import g

        token = accounts.login("admin@example.test", "test-password-admin-only", "127.0.0.3")
        g.account = accounts.resolve(token)
        bundle = app_module.artifact_service.persist_agent_execution(
            agent_type="ceo",
            agent_name="CEO",
            task="Menu",
            company_info={"name": "Test"},
            result={"execution_mode": "local_artifacts", "summary": "Actual test output"},
        )
    entry = bundle["artifacts"][0]
    assert test_client.get(entry["url"]).status_code == 200
    response = test_client.get(entry["url"])
    assert response.headers["Content-Disposition"].startswith("attachment")
    assert response.headers["Cache-Control"] == "no-store"
    assert test_client.get("/api/artifacts/runs").json["count"] == 1
    with app_module.app.test_client() as other:
        login(other, "reviewer@example.test", "test-password-reviewer-only")
        assert other.get(entry["url"]).status_code == 404
        assert other.get("/api/artifacts/runs").json["count"] == 0
    path = app_module.artifact_service.static_root / entry["path"]
    path.write_text("modified")
    assert test_client.get(entry["url"]).status_code == 404
    assert test_client.get("/api/artifacts/file/../../.env").status_code == 404


def test_account_cli_requires_explicit_creation(accounts):
    result = app_module.app.test_cli_runner().invoke(
        args=["create-account", "--email", "new@example.test"],
        input="long-local-password-only\nlong-local-password-only\n",
    )
    assert result.exit_code == 0
    assert "Account created" in result.output
    assert "long-local-password-only" not in result.output


def test_login_disabled_is_local_only_and_keeps_static_artifacts_denied(
    accounts, test_client, monkeypatch
):
    monkeypatch.setitem(app_module.app.config, "ACCOUNT_AUTH_ENABLED", False)
    response = test_client.get("/login")
    assert response.status_code == 302 and response.headers["Location"] == "/"
    assert test_client.get("/api/agents/available").status_code == 200
    assert (
        test_client.get(
            "/api/agents/available", environ_overrides={"REMOTE_ADDR": "192.0.2.10"}
        ).status_code
        == 403
    )
    assert test_client.get("/static/generated_outputs/old/result.json").status_code == 404
