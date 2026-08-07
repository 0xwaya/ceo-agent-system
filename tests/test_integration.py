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

    def test_full_analysis_flow(self, test_client, sample_company_info):
        """Test complete analysis workflow"""
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

    def test_agent_execution_flow(self, test_client):
        """Test agent execution workflow"""
        # 1. Execute an agent
        response = test_client.post(
            "/api/agent/execute/branding",
            json={
                "task": "Design brand identity",
                "company_info": {"name": "Test Corp", "industry": "Tech", "location": "CA"},
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
