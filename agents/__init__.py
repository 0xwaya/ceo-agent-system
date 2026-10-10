"""
Agents Package - Multi-Agent System
All specialized agents and orchestration logic
"""

from importlib import import_module

__all__ = [
    "BaseAgent",
    "AgentFactory",
    "BrandingAgent",
    "WebDevelopmentAgent",
    "LegalComplianceAgent",
    "MartechAgent",
    "ContentAgent",
    "CampaignAgent",
    "CFOAgentState",
    "analyze_strategic_objectives",
    "deploy_specialized_agents",
    "AgentGuardRail",
    "AgentDomain",
    "validate_agent_output",
    "create_execution_summary",
]

_MODULES = {
    "BaseAgent": "agents.base_agent",
    **dict.fromkeys(
        [
            "AgentFactory",
            "BrandingAgent",
            "WebDevelopmentAgent",
            "LegalComplianceAgent",
            "MartechAgent",
            "ContentAgent",
            "CampaignAgent",
        ],
        "agents.specialized_agents",
    ),
    **dict.fromkeys(
        ["CFOAgentState", "analyze_strategic_objectives", "deploy_specialized_agents"],
        "agents.cfo_agent",
    ),
    **dict.fromkeys(
        ["AgentGuardRail", "AgentDomain", "validate_agent_output", "create_execution_summary"],
        "agents.agent_guard_rails",
    ),
}


def __getattr__(name):
    """Load legacy compatibility exports only when explicitly requested."""
    if name not in _MODULES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(_MODULES[name]), name)
    globals()[name] = value
    return value
