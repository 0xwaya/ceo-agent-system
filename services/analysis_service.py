"""Scenario-specific strategic planning without preset business data."""

import json
import logging
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field

from exceptions import AnalysisError
from services.state_builder import CFOStateBuilder
from graph_architecture.llm_nodes import _get_llm
from graph_architecture.privacy import privacy_scrub_node

logger = logging.getLogger(__name__)


class StrategicTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    task_name: str
    description: str
    required_expertise: str
    objective_index: int = Field(ge=0)
    priority: str
    estimated_budget: float = Field(ge=0, allow_inf_nan=False)
    estimated_days: int = Field(gt=0)
    requires_payment: bool


class StrategicPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identified_tasks: List[StrategicTask] = Field(min_length=1)
    risks: List[str]
    recommendations: List[str]
    discovery_questions: List[str]
    executive_summary: str


def analyze_strategic_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Produce a validated plan; never substitute a template after model failure."""
    safe_state = {**state, **privacy_scrub_node(state)}
    context = {
        key: safe_state[key]
        for key in (
            "company_name",
            "industry",
            "location",
            "total_budget",
            "target_completion_days",
            "strategic_objectives",
        )
    }
    try:
        llm = _get_llm(temperature=0.1, max_tokens=2500)
        plan = llm.with_structured_output(StrategicPlan).invoke(
            [
                (
                    "system",
                    "Plan ONLY for the supplied scenario and objectives. Each task must "
                    "reference a zero-based objective_index. Do not add unrelated standard "
                    "business-launch tasks. Costs and durations are estimates, not spending "
                    "or completed work. Task estimates in total must fit the budget and "
                    "each task must fit the timeline. Ask discovery questions for missing "
                    "facts; never invent research, revenue, customers or existing systems. "
                    "No external tools are connected. Publishing, purchases, outreach and "
                    "deployment require a future connector and explicit approval.",
                ),
                ("human", json.dumps(context)),
            ]
        )
        if not isinstance(plan, StrategicPlan):
            raise ValueError("Model did not return a valid strategic plan")
        tasks = [task.model_dump() for task in plan.identified_tasks]
        if len({task["task_id"] for task in tasks}) != len(tasks):
            raise ValueError("Task IDs must be unique")
        for task in tasks:
            if task["objective_index"] >= len(state["strategic_objectives"]):
                raise ValueError("Task references an objective outside this scenario")
            if task["estimated_days"] > state["target_completion_days"]:
                raise ValueError("Task estimate exceeds scenario timeline")
            task["status"] = "planned"
        allocation: Dict[str, float] = {}
        for task in tasks:
            domain = task["required_expertise"]
            allocation[domain] = allocation.get(domain, 0) + task["estimated_budget"]
        if sum(allocation.values()) > state["total_budget"]:
            raise ValueError("Task estimates exceed scenario budget")
        return {
            **state,
            "identified_tasks": tasks,
            "budget_allocated": allocation,
            "risks": [{"description": risk} for risk in plan.risks],
            "recommendations": plan.recommendations,
            "discovery_questions": [
                {"category": "Scenario", "question": question}
                for question in plan.discovery_questions
            ],
            "final_executive_summary": plan.executive_summary,
        }
    except Exception as exc:
        logger.error("Strategic planning failed", exc_info=True)
        raise AnalysisError(
            "Strategic planning failed; no preset analysis was substituted"
        ) from exc


class AnalysisService:
    def analyze_objectives(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        result = analyze_strategic_state(CFOStateBuilder.create_from_request(request_data))
        return {
            "success": True,
            "tasks": result["identified_tasks"],
            "budget_allocation": result["budget_allocated"],
            "risks": result["risks"],
            "timeline": result["target_completion_days"],
        }
