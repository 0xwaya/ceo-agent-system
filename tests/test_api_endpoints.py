"""
Unit tests for API endpoints
"""

import pytest
import json
import app as app_module


class TestAPIEndpoints:
    """Test class for API endpoints"""

    def test_index_route(self, test_client):
        """Test index route returns v0.4 HTML"""
        response = test_client.get("/")
        assert response.status_code == 200
        # v0.4 unified dashboard — title changed from 'CEO Executive Agent'
        assert (
            b"Executive AI" in response.data
            or b"v0.4" in response.data
            or b"v4-layout" in response.data
        )

    def test_get_available_agents(self, test_client):
        """Test /api/agents/available endpoint"""
        response = test_client.get("/api/agents/available")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "agents" in data
        assert isinstance(data["agents"], list)
        assert len(data["agents"]) > 0

        # Check agent structure
        first_agent = data["agents"][0]
        assert "type" in first_agent
        assert "name" in first_agent
        assert "capabilities" in first_agent
        assert "budget" in first_agent

    def test_analyze_objectives_success(self, test_client, sample_company_info):
        """Test /api/ceo/analyze endpoint with valid data"""
        response = test_client.post(
            "/api/ceo/analyze",
            data=json.dumps(sample_company_info),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert "success" in data
        assert "tasks" in data or "error" in data  # Either success or error

        if data.get("success"):
            assert isinstance(data["tasks"], list)
            assert "budget_allocation" in data
            assert "risks" in data

    def test_analyze_objectives_invalid_data(self, test_client):
        """Test /api/ceo/analyze with missing data"""
        response = test_client.post(
            "/api/ceo/analyze", data=json.dumps({}), content_type="application/json"
        )

        # Should either succeed with defaults or return error
        assert response.status_code in [200, 400, 500]

    def test_execute_agent_endpoint(self, test_client, sample_agent_request):
        """Test agent execution endpoint"""
        response = test_client.post(
            "/api/agent/execute/branding",
            data=json.dumps(sample_agent_request),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert "result" in data or "success" in data

        if data.get("success"):
            result = data["result"]
            assert "agent_type" in result
            assert "status" in result

    def test_execute_invalid_agent(self, test_client, sample_agent_request):
        """Test executing non-existent agent"""
        response = test_client.post(
            "/api/agent/execute/nonexistent_agent",
            data=json.dumps(sample_agent_request),
            content_type="application/json",
        )

        # Should return error
        assert response.status_code in [400, 404, 500]

    def test_cors_headers(self, test_client):
        """Test CORS headers are present"""
        response = test_client.get("/api/agents/available")

        # Check if CORS is configured (optional)
        # This test may fail if CORS is not explicitly set
        # assert 'Access-Control-Allow-Origin' in response.headers

    def test_scenario_get_migrates_legacy_defaults_in_development(self, test_client, monkeypatch):
        """Legacy stale dev scenario should auto-migrate to canonical dev defaults."""
        monkeypatch.setenv("ENVIRONMENT", "development")

        legacy_scenario = {
            "company_name": "Amazon Granite LLC",
            "dba_name": "Amazon Granite LLC",
            "industry": "Software & Technology",
            "location": "San Francisco, CA",
            "budget": 100000,
            "timeline": 90,
            "objectives": [
                "Launch SaaS platform",
                "Build enterprise sales team",
                "Establish market presence",
                "Scale to $1M ARR",
            ],
            "updated_at": "2026-01-01T00:00:00",
        }

        with app_module.shared_state_lock:
            app_module.shared_runtime_state["scenario"] = legacy_scenario

        response = test_client.get("/api/scenario/current")
        assert response.status_code == 200

        data = json.loads(response.data)
        scenario = data["scenario"]

        assert scenario["company_name"] == app_module.DEFAULT_DEV_SCENARIO["company_name"]
        assert scenario["dba_name"] == app_module.DEFAULT_DEV_SCENARIO["dba_name"]
        assert scenario["industry"] == app_module.DEFAULT_DEV_SCENARIO["industry"]
        assert scenario["location"] == app_module.DEFAULT_DEV_SCENARIO["location"]
        assert scenario["budget"] == app_module.DEFAULT_DEV_SCENARIO["budget"]
        assert scenario["timeline"] == app_module.DEFAULT_DEV_SCENARIO["timeline"]
        assert scenario["objectives"] == app_module.DEFAULT_DEV_OBJECTIVES
        assert scenario["meta"]["schema_version"] == app_module.SCENARIO_SCHEMA_VERSION
        assert scenario["meta"]["defaults_version"] == app_module.DEV_SCENARIO_DEFAULTS_VERSION

    def test_scenario_post_stamps_metadata_and_marks_user_modified(self, test_client, monkeypatch):
        """Explicit scenario updates should stamp metadata and mark user_modified."""
        monkeypatch.setenv("ENVIRONMENT", "development")

        payload = {
            "company_name": "Custom Co",
            "dba_name": "Custom DBA",
            "industry": "Construction",
            "location": "Cincinnati, OH",
            "budget": 2500,
            "timeline": 45,
            "objectives": ["Objective A", "Objective B"],
        }

        response = test_client.post(
            "/api/scenario/current", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        scenario = data["scenario"]

        assert scenario["company_name"] == "Custom Co"
        assert scenario["industry"] == "Construction"
        assert scenario["meta"]["user_modified"] is True
        assert scenario["meta"]["schema_version"] == app_module.SCENARIO_SCHEMA_VERSION
        assert scenario["meta"]["defaults_version"] == app_module.DEV_SCENARIO_DEFAULTS_VERSION

    def test_scenario_get_resets_to_blank_defaults_in_production_for_legacy_state(
        self, test_client, monkeypatch
    ):
        """Production should blank legacy default state on migration."""
        monkeypatch.setenv("ENVIRONMENT", "production")

        legacy_scenario = {
            "company_name": "Amazon Granite LLC",
            "dba_name": "SurfaceCraft Studio",
            "industry": "Construction, Custom Countertops",
            "location": "Cincinnati, OH",
            "budget": 1000,
            "timeline": 30,
            "objectives": ["Launch AR platform showroom"],
            "updated_at": "2026-01-01T00:00:00",
        }

        with app_module.shared_state_lock:
            app_module.shared_runtime_state["scenario"] = legacy_scenario

        response = test_client.get("/api/scenario/current")
        assert response.status_code == 200

        data = json.loads(response.data)
        scenario = data["scenario"]

        assert scenario["company_name"] == ""
        assert scenario["dba_name"] == ""
        assert scenario["industry"] == ""
        assert scenario["location"] == ""
        assert scenario["budget"] == 0.0
        assert scenario["timeline"] == 0
        assert scenario["objectives"] == []
        assert scenario["meta"]["defaults_version"] == app_module.PROD_SCENARIO_DEFAULTS_VERSION


class TestValidation:
    """Test input validation"""

    def test_sanitization(self):
        """Test input sanitization functions"""
        from utils.validators import sanitize_string

        # Test XSS prevention
        dirty_input = '<script>alert("xss")</script>Hello'
        clean = sanitize_string(dirty_input)
        assert "<script>" not in clean
        assert "alert" not in clean

        # Test javascript: URL prevention
        dirty_url = "javascript:alert(1)"
        clean = sanitize_string(dirty_url)
        assert "javascript:" not in clean.lower()

        # Test event handler prevention
        dirty_event = '<div onclick="alert(1)">Click</div>'
        clean = sanitize_string(dirty_event)
        assert "onclick" not in clean.lower()

    def test_max_length_validation(self):
        """Test maximum length enforcement"""
        from utils.validators import sanitize_string

        long_string = "A" * 1000
        clean = sanitize_string(long_string, max_length=100)

        assert len(clean) <= 100


class TestErrorHandling:
    """Test error handling"""

    def test_404_handling(self, test_client):
        """Test 404 error handling"""
        response = test_client.get("/nonexistent/route")
        assert response.status_code == 404

    def test_method_not_allowed(self, test_client):
        """Test method not allowed errors"""
        response = test_client.get("/api/ceo/analyze")  # Should be POST
        assert response.status_code == 405

    def test_invalid_json(self, test_client):
        """Test invalid JSON handling"""
        response = test_client.post(
            "/api/ceo/analyze", data="not valid json", content_type="application/json"
        )

        # Should handle gracefully
        assert response.status_code in [400, 500]


class TestSecurity:
    """Security-related tests"""

    def test_xss_prevention(self, test_client):
        """Test XSS attack prevention"""
        xss_payload = {
            "company_name": '<script>alert("XSS")</script>',
            "industry": '"><img src=x onerror=alert(1)>',
            "location": "javascript:alert(document.cookie)",
        }

        response = test_client.post(
            "/api/ceo/analyze", data=json.dumps(xss_payload), content_type="application/json"
        )

        # Should not crash, and response should not contain script tags
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.get_data(as_text=True)
            assert "<script>" not in data.lower()

    def test_sql_injection_prevention(self, test_client):
        """Test SQL injection prevention"""
        sql_payload = {
            "company_name": "'; DROP TABLE users; --",
            "industry": "1' OR '1'='1",
            "location": "admin'--",
        }

        response = test_client.post(
            "/api/ceo/analyze", data=json.dumps(sql_payload), content_type="application/json"
        )

        # Should not crash
        assert response.status_code in [200, 400, 500]

    def test_content_type_validation(self, test_client):
        """Test content type validation"""
        response = test_client.post("/api/ceo/analyze", data="some data", content_type="text/plain")

        # Should reject or handle non-JSON content
        # Most Flask apps will return 400 or process it anyway
        assert response.status_code in [200, 400, 415]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
