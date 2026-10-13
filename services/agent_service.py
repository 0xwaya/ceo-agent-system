"""Shared local-artifact execution for graph and individual-agent controls."""

from typing import Any, Dict, Optional

from exceptions import AgentNotFoundError
from graph_architecture import llm_nodes
from graph_architecture.privacy import privacy_scrub_node
from services.artifact_service import artifact_service
from services.state_builder import CFOStateBuilder
from config import APP_VERSION


_NODE_NAMES = {
    "ceo": "ceo_llm_analyze_node",
    "cto": "cto_llm_architecture_node",
    "cfo": "cfo_llm_summarize_node",
    "engineer": "engineer_llm_architect_node",
    "researcher": "researcher_llm_synthesize_node",
    "legal": "legal_llm_compliance_node",
    "martech": "martech_llm_strategy_node",
    "security": "security_llm_audit_node",
    "ux_design": "ux_design_llm_node",
    "web_development": "webdev_llm_node",
    "software_eng": "software_eng_llm_node",
    "branding": "branding_llm_node",
    "content": "content_llm_node",
    "campaigns": "campaign_llm_node",
    "social_media": "social_media_llm_node",
}
SUPPORTED_AGENTS = tuple(_NODE_NAMES) + ("prompt_expert",)


def run_agent_node(agent_type: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute one model-backed node and persist its actual output files."""
    if agent_type == "prompt_expert":
        from graph_architecture.prompt_expert import prompt_expert_node

        update = prompt_expert_node(state)
    elif agent_type in _NODE_NAMES:
        update = getattr(llm_nodes, _NODE_NAMES[agent_type])(state)
    else:
        raise AgentNotFoundError(f"Unsupported agent: {agent_type}")
    output_fields = {
        key: value
        for key, value in update.items()
        if key.endswith("_output") or key == "llm_routing_decision"
    }
    if not output_fields or not all(
        isinstance(value, dict) and value for value in output_fields.values()
    ):
        raise RuntimeError(f"{agent_type} did not return a usable structured output")
    output = next(iter(output_fields.values()))
    result = {
        **output,
        "agent_type": agent_type,
        "status": "artifacts_generated",
        "execution_mode": "local_artifacts",
        "external_actions_executed": False,
        "spend_verified": False,
        "version": APP_VERSION,
        "website_evidence": state.get("website_evidence", {}),
    }
    bundle = artifact_service.persist_agent_execution(
        agent_type=agent_type,
        agent_name=agent_type.replace("_", " ").title(),
        task="; ".join(state["strategic_objectives"]),
        company_info={
            "company_name": state["company_name"],
            "dba_name": state.get("dba_name") or state["company_name"],
            "industry": state["industry"],
            "location": state["location"],
            "website": state.get("website", ""),
        },
        result=result,
    )
    record = {
        "agent": agent_type,
        "summary": result,
        "artifacts": bundle["artifacts"],
        "artifact_run_id": bundle["run_id"],
    }
    return {**update, "agent_outputs": [record]}


class AgentExecutionService:
    def execute_agent(
        self,
        agent_type: str,
        task_description: str,
        company_info: Dict[str, Any],
        requirements: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        state = CFOStateBuilder.create_from_request(
            {
                **company_info,
                "objectives": (requirements or {}).get("objectives") or [task_description],
            }
        )
        state.update(privacy_scrub_node(state))
        from services.website_service import fetch_homepage

        state["website_evidence"] = fetch_homepage(state["website"])
        update = run_agent_node(agent_type, state)
        record = update["agent_outputs"][0]
        return {
            "success": True,
            "result": {
                **record["summary"],
                "artifacts": record["artifacts"],
                "artifact_run_id": record["artifact_run_id"],
            },
        }
