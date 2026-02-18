"""
Pytest configuration and fixtures for CEO Executive Agent tests
"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env before importing app so OPENAI_API_KEY and other vars are available
try:
    from dotenv import load_dotenv

    _env_path = Path(__file__).parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path, override=True)
except ImportError:
    pass

from app import app, socketio
from flask import Flask


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
        "company_info": {"name": "Test Company", "industry": "Tech", "location": "California"},
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
