"""
CFO State Builder - Centralized state creation
Eliminates duplicate state creation code
"""

from typing import Dict, Any, List, Optional
from utils.constants import AppConstants


class CFOStateBuilder:
    """
    Factory class for creating CFO agent state
    Ensures consistent state structure across the application
    """

    @staticmethod
    def create_initial_state(
        company_name: str = None,
        industry: str = None,
        location: str = None,
        budget: float = None,
        timeline: int = None,
        objectives: List[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create initial CFO agent state

        Args:
            company_name: Company name
            industry: Business industry
            location: Company location
            budget: Total budget
            timeline: Timeline in days
            objectives: Strategic objectives
            **kwargs: Additional state fields

        Returns:
            Complete CFO agent state dictionary
        """
        state = {
            # Top-level company info (NOT nested - matches CFOAgentState schema)
            "company_name": company_name or AppConstants.DEFAULT_COMPANY_NAME,
            "industry": industry or AppConstants.DEFAULT_INDUSTRY,
            "location": location or AppConstants.DEFAULT_LOCATION,
            "business_goals": [],
            # Strategic objectives
            "strategic_objectives": objectives or AppConstants.DEFAULT_OBJECTIVES.copy(),
            # Budget management
            "total_budget": budget or AppConstants.DEFAULT_BUDGET,
            "budget_allocated": {},
            "budget_reserved_for_fees": 0,
            "pending_approvals": [],
            "approved_actions": [],
            "rejected_actions": [],
            "pending_payments": [],
            # Timeline
            "target_completion_days": timeline or AppConstants.DEFAULT_TIMELINE_DAYS,
            "current_day": 0,
            "milestones": [],
            # Multi-agent orchestration
            "active_agents": [],
            "agent_outputs": [],
            "agent_status": {},
            "delegated_tasks": {},
            # Task breakdown
            "identified_tasks": [],
            "assigned_tasks": {},
            "completed_tasks": [],
            "blocked_tasks": [],
            # Risk management
            "risks": [],
            "risk_mitigation_plans": {},
            "opportunities": [],
            "opportunity_analysis": [],
            # Deliverables
            "deliverables": [],
            "status_reports": [],
            "final_executive_summary": "",
            # Governance
            "guard_rail_violations": [],
            "liability_warnings": [],
            "compliance_status": {},
            "executive_decisions": [],
            # Workflow
            "current_phase": AppConstants.PHASE_INITIALIZATION,
            "completed_phases": [],
        }

        # Merge any additional kwargs
        state.update(kwargs)

        return state

    @staticmethod
    def create_from_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create state from API request data

        Args:
            request_data: Request data from API

        Returns:
            CFO agent state
        """
        # Extract company info (handle both nested and flat structures)
        company_info = request_data.get("company_info", {})

        return CFOStateBuilder.create_initial_state(
            company_name=request_data.get("company_name")
            or company_info.get("company_name")
            or company_info.get("name"),
            industry=request_data.get("industry") or company_info.get("industry"),
            location=request_data.get("location") or company_info.get("location"),
            budget=float(request_data.get("budget", AppConstants.DEFAULT_BUDGET)),
            timeline=int(request_data.get("timeline", AppConstants.DEFAULT_TIMELINE_DAYS)),
            objectives=request_data.get("objectives", []),
        )

    @staticmethod
    def validate_state(state: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate state structure

        Args:
            state: State dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = [
            "company_name",
            "industry",
            "location",
            "total_budget",
            "target_completion_days",
            "strategic_objectives",
            "current_phase",
        ]

        for field in required_fields:
            if field not in state:
                return False, f"Missing required field: {field}"

        # Validate budget
        if state["total_budget"] <= 0:
            return False, "Budget must be greater than 0"

        # Validate timeline
        if state["target_completion_days"] <= 0:
            return False, "Timeline must be greater than 0"

        return True, None

    @staticmethod
    def extract_company_info(state: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract company info from state

        Args:
            state: CFO agent state

        Returns:
            Company info dictionary
        """
        return {
            "name": state.get("company_name", ""),
            "company_name": state.get("company_name", ""),
            "dba_name": state.get("company_name", ""),  # Use same as company_name if not specified
            "industry": state.get("industry", ""),
            "location": state.get("location", ""),
        }
