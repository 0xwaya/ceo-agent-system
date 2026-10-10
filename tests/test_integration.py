"""
Integration tests for SocketIO events
"""

import pytest


class TestSocketIOEvents:
    """Test Socket.IO real-time communication"""

    def test_socket_connection(self, test_socketio_client):
        """Test Socket.IO connection"""
        assert test_socketio_client.is_connected()


class TestIntegrationFlows:
    """Integration tests for complete workflows"""

    def test_full_analysis_flow(self, test_client, sample_company_info, monkeypatch):
        """Test complete analysis workflow"""
        import app as app_module

        monkeypatch.setattr(app_module, "_prompt_expert_node", lambda state: {})
        monkeypatch.setattr(
            app_module,
            "ceo_analyze",
            lambda state: {
                **state,
                "identified_tasks": [
                    {
                        "task_id": "mvp",
                        "task_name": "Launch MVP",
                        "description": "Plan the supplied MVP objective",
                        "required_expertise": "web_development",
                        "priority": "HIGH",
                    }
                ],
                "budget_allocated": {"web_development": 500},
                "risks": [],
            },
        )
        # 1. Request analysis
        response = test_client.post("/api/ceo/analyze", json=sample_company_info)

        assert response.status_code == 200
        data = response.json

        if data.get("success"):
            # 2. Verify tasks were identified
            assert "tasks" in data
            assert len(data["tasks"]) > 0

            # 3. Verify budget was allocated
            assert "budget_allocation" in data

            # 4. Verify risks were identified
            assert "risks" in data

    def test_agent_execution_flow(self, test_client, monkeypatch):
        """Test agent execution workflow"""
        monkeypatch.setattr(
            "graph_architecture.llm_nodes.branding_llm_node",
            lambda state: {
                "branding_output": {"brand_summary": "Identity for Test Corp"},
            },
        )
        # 1. Execute an agent
        response = test_client.post(
            "/api/agent/execute/branding",
            json={
                "task": "Design brand identity",
                "company_info": {
                    "name": "Test Corp",
                    "industry": "Tech",
                    "location": "CA",
                    "budget": 5000,
                    "timeline": 90,
                },
            },
        )

        assert response.status_code == 200
        data = response.json

        # 2. Verify execution result
        assert "result" in data or "success" in data

        if "result" in data:
            result = data["result"]
            assert "agent_type" in result
            assert result["agent_type"] == "branding"
            assert "status" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
