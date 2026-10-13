"""
CFO State Builder - Centralized state creation
Eliminates duplicate state creation code
"""

from typing import Dict, Any, List, Optional
import math
from utils.constants import AppConstants
from exceptions import ValidationError


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
            "company_name": company_name or "",
            "industry": industry or "",
            "location": location or "",
            "business_goals": [],
            # Strategic objectives
            "strategic_objectives": list(objectives) if objectives is not None else [],
            # Budget management
            "total_budget": budget if budget is not None else 0,
            "budget_allocated": {},
            "budget_reserved_for_fees": 0,
            "pending_approvals": [],
            "approved_actions": [],
            "rejected_actions": [],
            "pending_payments": [],
            # Timeline
            "target_completion_days": timeline if timeline is not None else 0,
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
        if not isinstance(request_data, dict):
            raise ValidationError("Scenario must be an object")
        company_info = request_data.get("company_info", {})
        if not isinstance(company_info, dict):
            raise ValidationError("company_info must be an object")
        values = {**company_info, **request_data}
        budget = values.get("total_budget", values.get("budget"))
        timeline = values.get("target_days", values.get("timeline"))
        try:
            if isinstance(budget, bool) or isinstance(timeline, bool):
                raise ValueError
            budget = float(budget)
            timeline_number = float(timeline)
            if not math.isfinite(timeline_number) or not timeline_number.is_integer():
                raise ValueError
            timeline = int(timeline_number)
        except (TypeError, ValueError, OverflowError):
            raise ValidationError("Budget and timeline must be explicit finite numbers")

        objectives = values.get("objectives", values.get("strategic_objectives", []))
        if not isinstance(objectives, list) or any(
            not isinstance(item, str) or not item.strip() for item in objectives
        ):
            raise ValidationError("Objectives must be a list of non-empty strings")
        text_values = [
            values.get("company_name", values.get("name", "")),
            values.get("industry", ""),
            values.get("location", ""),
        ]
        if any(not isinstance(value, str) or not value.strip() for value in text_values):
            raise ValidationError("Company name, industry and location are required")

        state = CFOStateBuilder.create_initial_state(
            company_name=text_values[0].strip(),
            industry=text_values[1].strip(),
            location=text_values[2].strip(),
            budget=budget,
            timeline=timeline,
            objectives=[item.strip() for item in objectives],
        )
        from services.website_service import normalize_website

        state["website"] = normalize_website(values.get("website", ""))
        valid, error = CFOStateBuilder.validate_state(state)
        if not valid:
            raise ValidationError(error)
        return state

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
        if not math.isfinite(state["total_budget"]) or state["total_budget"] <= 0:
            return False, "Budget must be finite and greater than 0"

        # Validate timeline
        if state["target_completion_days"] <= 0:
            return False, "Timeline must be greater than 0"
        if not state["strategic_objectives"]:
            return False, "At least one objective is required"

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
