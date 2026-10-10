"""
Pytest configuration and fixtures for CEO Executive Agent tests
"""

import pytest
import sys
import os
import importlib
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Tests must never load private credentials or make paid provider calls.
os.environ["OPENAI_API_KEY"] = ""
os.environ["SECRET_KEY"] = "offline-test-session-key"
os.environ["ENABLE_AUTH"] = "False"
os.environ["APP_ENV"] = "testing"

app_module = importlib.import_module("app")
app, socketio = app_module.app, app_module.socketio


@pytest.fixture(autouse=True)
def block_live_model_calls(monkeypatch):
    from langchain_openai import ChatOpenAI

    def blocked(*args, **kwargs):
        raise AssertionError("Live model calls are disabled in tests")

    monkeypatch.setattr(ChatOpenAI, "invoke", blocked)


@pytest.fixture(autouse=True)
def isolate_runtime_state(monkeypatch, tmp_path):
    import app as app_module
    from services.artifact_service import ArtifactService

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("APP_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setattr(app_module, "_runtime", None)
    monkeypatch.setattr(app_module, "_auth_store", None)
    monkeypatch.setitem(app_module.app.config, "ACCOUNT_AUTH_ENABLED", False)
    monkeypatch.setattr(
        app_module,
        "shared_runtime_state",
        {
            "scenario": app_module._get_default_scenario_for_environment(),
            "scenarios": {},
            "last_orchestration_report": None,
        },
    )
    monkeypatch.setattr(app_module, "_CHAT_SESSIONS", {})
    service = ArtifactService(tmp_path / "static")
    monkeypatch.setattr(app_module, "artifact_service", service)
    monkeypatch.setattr("services.agent_service.artifact_service", service)
    monkeypatch.setattr("services.artifact_service.artifact_service", service)


@pytest.fixture
def test_client():
    """Flask test client"""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.test_client() as client:
        yield client


@pytest.fixture
def test_socketio_client(test_client):
    """Socket.IO test client"""
    client = socketio.test_client(app, flask_test_client=test_client)
    yield client
    if client.is_connected():
        client.disconnect()


@pytest.fixture
def sample_company_info():
    """Sample company information for testing"""
    return {
        "company_name": "Test Company Inc",
        "industry": "Technology",
        "location": "San Francisco, CA",
        "budget": 5000,
        "timeline": 90,
        "objectives": ["Launch MVP", "Validate market fit"],
    }


@pytest.fixture
def sample_agent_request():
    """Sample agent execution request"""
    return {
        "task": "Create brand identity",
        "company_info": {
            "name": "Test Company",
            "industry": "Tech",
            "location": "California",
            "budget": 5000,
            "timeline": 90,
        },
    }


@pytest.fixture
def mock_agent_response():
    """Mock agent execution response"""
    return {
        "agent_type": "branding",
        "status": "executed",
        "deliverables": [
            "Logo design with 3 color variations",
            "Brand guidelines document",
            "Typography system",
        ],
        "budget_used": 150,
        "timeline": [
            {"phase": "Research", "description": "Market analysis"},
            {"phase": "Design", "description": "Logo concepts"},
            {"phase": "Delivery", "description": "Final assets"},
        ],
    }
