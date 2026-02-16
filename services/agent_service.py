"""
Agent Execution Service
Handles agent deployment and execution logic
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from agents.specialized_agents import AgentFactory
from services.state_builder import CFOStateBuilder
from utils.constants import AppConstants
from exceptions import AgentNotFoundError, ExecutionError

logger = logging.getLogger(__name__)


class AgentExecutionService:
    """
    Service for agent execution operations
    Centralizes agent deployment logic with polymorphism
    """

    def __init__(self):
        """Initialize agent execution service"""
        self.factory = AgentFactory()
        self.state_builder = CFOStateBuilder()

    def execute_agent(
        self,
        agent_type: str,
        task_description: str,
        company_info: Dict[str, Any],
        requirements: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a specific specialized agent

        Args:
            agent_type: Type of agent to execute
            task_description: Task description
            company_info: Company information
            requirements: Optional additional requirements

        Returns:
            Execution result dictionary

        Raises:
            AgentNotFoundError: If agent type is invalid
            ExecutionError: If execution fails
        """
        logger.info(f"Executing {agent_type} agent", extra={"task": task_description})

        try:
            # Validate agent type
            if not AppConstants.is_valid_agent_type(agent_type):
                raise AgentNotFoundError(f"Invalid agent type: {agent_type}")

            # Create agent
            agent = self.factory.create_agent(agent_type)

            # Ensure company_info has required fields
            company_info = self._normalize_company_info(company_info)

            # Create base result
            result = {
                "agent_type": agent_type,
                "agent_name": agent.name,
                "status": "executed",
                "timestamp": datetime.now().isoformat(),
                "execution_mode": "AI_PERFORMED",
                "budget_used": 0,
            }

            # Execute agent-specific logic
            agent_result = self._execute_agent_method(
                agent, agent_type, task_description, company_info, requirements or {}
            )

            # Merge results
            result.update(agent_result)

            logger.info(
                f"{agent_type} agent executed successfully. "
                f"Budget used: ${result.get('budget_used', 0)}"
            )

            return {"success": True, "result": result}

        except AgentNotFoundError:
            logger.error(f"Agent not found: {agent_type}")
            raise
        except Exception as e:
            logger.error(f"Agent execution failed: {str(e)}", exc_info=True)
            raise ExecutionError(f"Failed to execute {agent_type} agent: {str(e)}")

    def _normalize_company_info(self, company_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize company info to include all required fields

        Args:
            company_info: Company information dictionary

        Returns:
            Normalized company info
        """
        normalized = company_info.copy()

        # Ensure 'name' field exists
        if not normalized.get("name"):
            normalized["name"] = normalized.get("company_name", "Company")

        # Ensure 'dba_name' field exists
        if not normalized.get("dba_name"):
            normalized["dba_name"] = normalized.get("name", "Company")

        # Ensure 'industry' field exists
        if not normalized.get("industry"):
            normalized["industry"] = "General Business"

        # Ensure 'location' field exists
        if not normalized.get("location"):
            normalized["location"] = "United States"

        return normalized

    def _execute_agent_method(
        self,
        agent: Any,
        agent_type: str,
        task_description: str,
        company_info: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute agent-specific method

        Args:
            agent: Agent instance
            agent_type: Agent type
            task_description: Task description
            company_info: Company information
            requirements: Additional requirements

        Returns:
            Agent-specific result dictionary
        """
        result = {}

        if agent_type == "branding" and hasattr(agent, "design_concepts"):
            state = {
                "task_description": task_description,
                "company_info": company_info,
                "research_findings": [],
                "design_concepts": [],
                "recommendations": [],
                "deliverables": [],
                "status": "initializing",
                "budget_used": 0,
                "timeline_days": 30,
            }
            concepts_result = agent.design_concepts(state)
            result["deliverables"] = concepts_result.get("deliverables", [])
            result["budget_used"] = concepts_result.get("budget_used", 0)

        elif agent_type == "web_development" and hasattr(agent, "analyze_requirements"):
            state = {
                "task_description": task_description,
                "requirements": requirements or company_info,
                "tech_stack": [],
                "architecture_design": "",
                "ar_features": [],
                "development_phases": [],
                "testing_results": [],
                "deliverables": [],
                "status": "initializing",
                "budget_used": 0,
                "timeline_days": 60,
            }
            web_result = agent.analyze_requirements(state)
            result["tech_stack"] = web_result.get("tech_stack", [])
            result["budget_used"] = web_result.get("budget_used", 0)

        elif agent_type == "martech" and hasattr(agent, "configure_stack"):
            state = {
                "task_description": task_description,
                "current_systems": [],
                "recommended_stack": [],
                "integrations": [],
                "automation_workflows": [],
                "implementation_plan": "",
                "status": "initializing",
                "budget_used": 0,
                "timeline_days": 30,
            }
            martech_result = agent.configure_stack(state)
            result["stack"] = martech_result.get("recommended_stack", [])
            result["budget_used"] = martech_result.get("budget_used", 0)

        elif agent_type == "content" and hasattr(agent, "produce_content"):
            state = {
                "task_description": task_description,
                "content_types": [],
                "production_schedule": [],
                "assets_created": [],
                "distribution_plan": "",
                "seo_strategy": "",
                "status": "initializing",
                "budget_used": 0,
                "timeline_days": 30,
            }
            content_result = agent.produce_content(state)
            result["assets"] = content_result.get("assets_created", [])
            result["budget_used"] = content_result.get("budget_used", 0)

        elif agent_type == "campaigns" and hasattr(agent, "launch_campaigns"):
            state = {
                "task_description": task_description,
                "channels": [],
                "audience_targeting": [],
                "creative_assets": [],
                "budget_allocation": [],
                "performance_metrics": [],
                "status": "initializing",
                "budget_used": 0,
                "timeline_days": 30,
            }
            campaign_result = agent.launch_campaigns(state)
            result["campaigns"] = campaign_result.get("channels", [])
            result["budget_used"] = campaign_result.get("budget_used", 0)

        elif agent_type == "legal" and hasattr(agent, "file_documents"):
            state = {
                "task_description": task_description,
                "jurisdiction": company_info.get("location", "United States"),
                "filings_required": [],
                "compliance_checklist": [],
                "documents_prepared": [],
                "risks_identified": [],
                "status": "initializing",
                "budget_used": 0,
                "timeline_days": 14,
            }
            legal_result = agent.file_documents(state)
            result["documents"] = legal_result.get("documents_prepared", [])
            result["budget_used"] = legal_result.get("budget_used", 0)

        elif agent_type == "security" and hasattr(agent, "run_security_review"):
            state = {
                "task_description": task_description,
                "company_info": company_info,
                "requirements": requirements,
            }
            security_result = agent.run_security_review(state)
            result["findings"] = security_result.get("findings", [])
            result["learning_sources"] = security_result.get("learning_sources", {})
            result["upgrades_identified"] = security_result.get("upgrades_identified", [])
            result["next_actions"] = security_result.get("next_actions", [])
            result["budget_used"] = 0

        return result

    def get_available_agents(self) -> list[Dict[str, Any]]:
        """
        Get list of available agents

        Returns:
            List of agent information dictionaries
        """
        from agents.agent_guard_rails import AgentGuardRail, AgentDomain

        agents = []

        for agent_type in self.factory.get_available_agents():
            try:
                agent = self.factory.create_agent(agent_type)
                domain_name = AppConstants.get_agent_domain(agent_type)
                guard_rail = AgentGuardRail(AgentDomain[domain_name])

                agents.append(
                    {
                        "type": agent_type,
                        "name": agent.name,
                        "capabilities": agent.capabilities,
                        "budget": guard_rail.budget_constraint.max_budget
                        if guard_rail.budget_constraint
                        else 0,
                        "status": "available",
                    }
                )
            except Exception as e:
                logger.warning(f"Error loading agent {agent_type}: {e}")

        return agents
