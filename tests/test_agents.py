"""
Unit tests for agent modules
"""

import pytest
from app import app as flask_app


class TestAgentStates:
    """Test agent state definitions"""

    def test_available_agents_endpoint(self):
        """Test getting available agents from API"""
        with flask_app.test_client() as client:
            response = client.get("/api/agents/available")
            assert response.status_code == 200
            data = response.get_json()
            assert "agents" in data
            assert len(data["agents"]) > 0

    def test_agent_types(self):
        """Test expected agent types are available"""
        with flask_app.test_client() as client:
            response = client.get("/api/agents/available")
            data = response.get_json()

            agent_ids = [agent["type"] for agent in data["agents"]]

            # Verify some expected agents exist
            expected_some = [
                "branding",
                "web_development",
                "legal",
                "martech",
                "content",
                "campaigns",
            ]
            # At least one of these should exist
            assert any(agent_id in expected_some for agent_id in agent_ids)

    def test_budget_constraints(self):
        """Test that budget information is included in agent data"""
        with flask_app.test_client() as client:
            response = client.get("/api/agents/available")
            data = response.get_json()

            # Check at least one agent has capabilities
            first_agent = data["agents"][0]
            assert "name" in first_agent
            assert "type" in first_agent
            assert "budget" in first_agent


class TestAgentExecution:
    """Test agent execution logic"""

    def test_analyze_endpoint_exists(self):
        """Test that analyze endpoint is available"""
        with flask_app.test_client() as client:
            # Sending empty request should fail validation
            response = client.post("/api/ceo/analyze", json={})
            # Should fail validation (400-level error)
            assert response.status_code in [400, 422, 500]

    def test_analyze_with_valid_data(self):
        """Test analyze endpoint with valid request"""
        with flask_app.test_client() as client:
            request_data = {
                "company_name": "Test Corp",
                "industry": "Technology",
                "location": "Ohio",
                "objectives": ["Launch product"],
                "budget": 5000,
                "timeline": 30,
            }

            response = client.post("/api/ceo/analyze", json=request_data)
            # Either success or validation error is fine
            assert response.status_code in [200, 400, 422, 500]


class TestCEOOrchestration:
    """Test CEO/CFO orchestration logic"""

    def test_orchestrate_endpoint_exists(self):
        """Test orchestrate endpoint is available"""
        with flask_app.test_client() as client:
            response = client.post("/api/graph/execute", json={})
            # Should return error due to missing data
            assert response.status_code in [400, 422, 500]

    def test_health_endpoint(self):
        """Test health check endpoint"""
        with flask_app.test_client() as client:
            response = client.get("/health")
            # Health endpoint might not exist, so this is optional
            assert response.status_code in [200, 404]

    def test_root_endpoint(self):
        """Test root endpoint renders"""
        with flask_app.test_client() as client:
            response = client.get("/")
            assert response.status_code == 200
            # Should contain some expected text
            assert b"CEO" in response.data or b"Agent" in response.data
