"""
Role-Based Guards and Governance Layer

Implements strict hierarchical enforcement:
1. Entry guards for subgraph access control
2. Role validation and authorization
3. Scope and domain validation
4. Violation logging and rejection
5. Approval chain enforcement
"""

import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum

from graph_architecture.schemas import (
    AgentRole,
    SharedState,
    SubgraphEntry,
    TaskPriority,
    RiskLevel,
)

logger = logging.getLogger(__name__)


# ============================================================================
# AUTHORIZATION LEVELS
# ============================================================================


class AuthorizationLevel(int, Enum):
    """Hierarchical authorization levels"""

    RESTRICTED = 0  # No special permissions
    OPERATIONAL = 1  # Basic operations
    SUPERVISORY = 2  # Can delegate and oversee
    EXECUTIVE = 3  # Strategic decisions
    OWNER = 4  # Full system access


# Agent role authorization mapping
ROLE_AUTHORIZATION = {
    AgentRole.CEO: AuthorizationLevel.EXECUTIVE,
    AgentRole.CFO: AuthorizationLevel.SUPERVISORY,
    AgentRole.ENGINEER: AuthorizationLevel.OPERATIONAL,
    AgentRole.RESEARCHER: AuthorizationLevel.OPERATIONAL,
    AgentRole.LEGAL: AuthorizationLevel.OPERATIONAL,
    AgentRole.MARTECH: AuthorizationLevel.OPERATIONAL,
    AgentRole.SECURITY: AuthorizationLevel.SUPERVISORY,  # Security has audit authority
}


# ============================================================================
# DOMAIN DEFINITIONS
# ============================================================================


class Domain(str, Enum):
    """Task domain categories"""

    FINANCE = "finance"
    ENGINEERING = "engineering"
    RESEARCH = "research"
    LEGAL = "legal"
    MARKETING = "marketing"
    SECURITY = "security"
    STRATEGY = "strategy"


# Which roles can work in which domains
DOMAIN_PERMISSIONS: Dict[Domain, Set[AgentRole]] = {
    Domain.FINANCE: {AgentRole.CEO, AgentRole.CFO},
    Domain.ENGINEERING: {AgentRole.CEO, AgentRole.ENGINEER},
    Domain.RESEARCH: {AgentRole.CEO, AgentRole.RESEARCHER},
    Domain.LEGAL: {AgentRole.CEO, AgentRole.LEGAL},
    Domain.MARKETING: {AgentRole.CEO, AgentRole.MARTECH},
    Domain.SECURITY: {AgentRole.CEO, AgentRole.SECURITY},  # Security audit domain
    Domain.STRATEGY: {AgentRole.CEO},  # CEO only
}


# ============================================================================
# GUARD RAIL EXCEPTIONS
# ============================================================================


class GuardRailViolation(Exception):
    """Base exception for guard rail violations"""

    def __init__(
        self, message: str, agent_role: AgentRole, violation_type: str, severity: str = "high"
    ):
        super().__init__(message)
        self.agent_role = agent_role
        self.violation_type = violation_type
        self.severity = severity
        self.timestamp = datetime.now().isoformat()


class UnauthorizedAccessError(GuardRailViolation):
    """Agent attempted unauthorized access"""

    def __init__(self, agent_role: AgentRole, target: str):
        super().__init__(
            f"Agent {agent_role} attempted unauthorized access to {target}",
            agent_role,
            "unauthorized_access",
            "critical",
        )


class HierarchyViolationError(GuardRailViolation):
    """Agent bypassed hierarchy"""

    def __init__(self, agent_role: AgentRole, attempted_action: str):
        super().__init__(
            f"Agent {agent_role} violated hierarchy: {attempted_action}",
            agent_role,
            "hierarchy_violation",
            "high",
        )


class ScopeViolationError(GuardRailViolation):
    """Agent exceeded domain scope"""

    def __init__(self, agent_role: AgentRole, domain: Domain):
        super().__init__(
            f"Agent {agent_role} exceeded scope in domain {domain}",
            agent_role,
            "scope_violation",
            "medium",
        )


class BudgetExceededError(GuardRailViolation):
    """Agent exceeded budget allocation"""

    def __init__(self, agent_role: AgentRole, requested: float, allowed: float):
        super().__init__(
            f"Agent {agent_role} requested ${requested} but only ${allowed} allowed",
            agent_role,
            "budget_exceeded",
            "high",
        )


# ============================================================================
# ENTRY GUARDS
# ============================================================================


class SubgraphEntryGuard:
    """
    Validates entry into subgraphs
    Ensures only authorized agents can invoke subgraphs
    """

    def __init__(self, allowed_roles: Set[AgentRole], domain: Domain):
        """
        Initialize entry guard

        Args:
            allowed_roles: Set of roles allowed to enter
            domain: Domain of this subgraph
        """
        self.allowed_roles = allowed_roles
        self.domain = domain
        self.access_log: List[Dict[str, Any]] = []

    def validate_entry(
        self, state: SharedState, requester_role: Optional[AgentRole] = None
    ) -> SharedState:
        """
        Validate entry to subgraph

        Args:
            state: Shared state
            requester_role: Role attempting to enter (if not in state)

        Returns:
            Validated state

        Raises:
            UnauthorizedAccessError: If access denied
        """
        # Determine requester from state or parameter
        if requester_role is None:
            # Extract from state (e.g., last active agent)
            if state.get("active_agents"):
                last_agent = state["active_agents"][-1]
                try:
                    requester_role = AgentRole(last_agent)
                except ValueError:
                    raise UnauthorizedAccessError(
                        AgentRole.CEO, f"Subgraph {self.domain}"  # Default
                    )
            else:
                # First entry, must be CEO
                requester_role = AgentRole.CEO

        # Check authorization
        if requester_role not in self.allowed_roles:
            violation = {
                "timestamp": datetime.now().isoformat(),
                "requester": requester_role.value,
                "domain": self.domain.value,
                "result": "denied",
                "reason": "insufficient_role",
            }
            self.access_log.append(violation)

            # Log to state
            state["guard_rail_violations"].append(violation)

            raise UnauthorizedAccessError(requester_role, f"{self.domain.value} subgraph")

        # Log successful entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "requester": requester_role.value,
            "domain": self.domain.value,
            "result": "granted",
        }
        self.access_log.append(entry)

        logger.info(f"Access granted: {requester_role.value} → {self.domain.value} subgraph")

        return state


# ============================================================================
# ROLE VALIDATORS
# ============================================================================


def validate_agent_role(agent_role: AgentRole, required_level: AuthorizationLevel) -> bool:
    """
    Validate agent has required authorization level

    Args:
        agent_role: Agent's role
        required_level: Required authorization level

    Returns:
        True if authorized
    """
    agent_level = ROLE_AUTHORIZATION.get(agent_role, AuthorizationLevel.RESTRICTED)
    return agent_level >= required_level


def validate_domain_access(agent_role: AgentRole, domain: Domain) -> bool:
    """
    Validate agent can access domain

    Args:
        agent_role: Agent's role
        domain: Target domain

    Returns:
        True if access allowed
    """
    allowed_roles = DOMAIN_PERMISSIONS.get(domain, set())
    return agent_role in allowed_roles


def validate_hierarchy(from_agent: AgentRole, to_agent: AgentRole) -> bool:
    """
    Validate communication follows hierarchy

    Rules:
    1. CEO can communicate with anyone
    2. Subordinates can only communicate with:
       - CEO (upward reporting)
       - Peers (lateral coordination)
       - Never downward to other subordinates

    Args:
        from_agent: Sender
        to_agent: Recipient

    Returns:
        True if communication allowed
    """
    # CEO can talk to anyone
    if from_agent == AgentRole.CEO:
        return True

    # Subordinates can talk to CEO (upward)
    if to_agent == AgentRole.CEO:
        return True

    # Peers can communicate laterally
    # (same authorization level)
    from_level = ROLE_AUTHORIZATION.get(from_agent, AuthorizationLevel.RESTRICTED)
    to_level = ROLE_AUTHORIZATION.get(to_agent, AuthorizationLevel.RESTRICTED)

    return from_level == to_level


# ============================================================================
# SCOPE VALIDATORS
# ============================================================================


class ScopeValidator:
    """
    Validates agent tasks are within scope
    """

    # Define permitted task types per agent
    PERMITTED_TASKS: Dict[AgentRole, Set[str]] = {
        AgentRole.CEO: {
            "strategic_planning",
            "goal_setting",
            "resource_allocation",
            "risk_assessment",
            "delegation",
            "final_approval",
        },
        AgentRole.CFO: {
            "budget_analysis",
            "cost_modeling",
            "financial_reporting",
            "compliance_check",
            "audit",
            "payment_validation",
        },
        AgentRole.ENGINEER: {
            "code_generation",
            "refactoring",
            "testing",
            "deployment",
            "architecture_design",
            "performance_optimization",
        },
        AgentRole.RESEARCHER: {
            "web_search",
            "document_analysis",
            "competitive_research",
            "spec_discovery",
            "citation_gathering",
        },
    }

    # Forbidden actions for all agents
    FORBIDDEN_TASKS = {
        "bypass_approval",
        "modify_other_agent_state",
        "delete_audit_logs",
        "escalate_own_privileges",
    }

    @classmethod
    def validate_task_scope(cls, agent_role: AgentRole, task_type: str) -> bool:
        """
        Validate task is within agent's scope

        Args:
            agent_role: Agent role
            task_type: Task type identifier

        Returns:
            True if task allowed

        Raises:
            ScopeViolationError: If task outside scope
        """
        # Check forbidden tasks
        if task_type in cls.FORBIDDEN_TASKS:
            raise ScopeViolationError(
                agent_role, Domain.STRATEGY  # Generic domain for forbidden tasks
            )

        # Check permitted tasks
        permitted = cls.PERMITTED_TASKS.get(agent_role, set())

        if task_type not in permitted:
            logger.warning(f"Task '{task_type}' not in permitted list for {agent_role}")
            return False

        return True


# ============================================================================
# BUDGET GUARDS
# ============================================================================


class BudgetGuard:
    """
    Enforces budget constraints
    """

    def __init__(self, total_budget: float):
        """
        Initialize budget guard

        Args:
            total_budget: Total available budget
        """
        self.total_budget = total_budget
        self.agent_allocations: Dict[AgentRole, float] = {}
        self.agent_spent: Dict[AgentRole, float] = {}

    def allocate_budget(self, agent_role: AgentRole, amount: float):
        """
        Allocate budget to agent

        Args:
            agent_role: Agent receiving allocation
            amount: Amount to allocate

        Raises:
            BudgetExceededError: If allocation exceeds total
        """
        current_total = sum(self.agent_allocations.values())

        if current_total + amount > self.total_budget:
            raise BudgetExceededError(agent_role, current_total + amount, self.total_budget)

        self.agent_allocations[agent_role] = amount
        self.agent_spent[agent_role] = 0.0

        logger.info(f"Allocated ${amount} to {agent_role}")

    def validate_expenditure(self, agent_role: AgentRole, amount: float) -> bool:
        """
        Validate expenditure against allocation

        Args:
            agent_role: Agent requesting expenditure
            amount: Amount to spend

        Returns:
            True if within budget

        Raises:
            BudgetExceededError: If exceeds allocation
        """
        allocated = self.agent_allocations.get(agent_role, 0.0)
        spent = self.agent_spent.get(agent_role, 0.0)
        remaining = allocated - spent

        if amount > remaining:
            raise BudgetExceededError(agent_role, amount, remaining)

        return True

    def record_expenditure(self, agent_role: AgentRole, amount: float):
        """
        Record actual expenditure

        Args:
            agent_role: Agent that spent
            amount: Amount spent
        """
        if agent_role not in self.agent_spent:
            self.agent_spent[agent_role] = 0.0

        self.agent_spent[agent_role] += amount
        logger.info(f"{agent_role} spent ${amount}")


# ============================================================================
# APPROVAL CHAIN ENFORCEMENT
# ============================================================================


class ApprovalChain:
    """
    Enforces approval chains for sensitive actions
    """

    # Actions requiring user approval
    USER_APPROVAL_REQUIRED = {
        "payment",
        "legal_filing",
        "contract_signing",
        "data_deletion",
        "external_api_call",
    }

    # Actions requiring CEO approval
    CEO_APPROVAL_REQUIRED = {"budget_reallocation", "task_cancellation", "agent_termination"}

    @classmethod
    def requires_user_approval(cls, action: str) -> bool:
        """Check if action requires user approval"""
        return action in cls.USER_APPROVAL_REQUIRED

    @classmethod
    def requires_ceo_approval(cls, action: str) -> bool:
        """Check if action requires CEO approval"""
        return action in cls.CEO_APPROVAL_REQUIRED

    @classmethod
    def validate_approval_chain(cls, action: str, approvals: List[str]) -> bool:
        """
        Validate proper approval chain

        Args:
            action: Action being attempted
            approvals: List of approvals received

        Returns:
            True if approval chain satisfied
        """
        if cls.requires_user_approval(action):
            if "user" not in approvals:
                logger.warning(f"Action '{action}' requires user approval")
                return False

        if cls.requires_ceo_approval(action):
            if "ceo" not in approvals:
                logger.warning(f"Action '{action}' requires CEO approval")
                return False

        return True


# ============================================================================
# VIOLATION LOGGING
# ============================================================================


class ViolationLogger:
    """
    Centralized violation logging
    """

    def __init__(self):
        self.violations: List[Dict[str, Any]] = []

    def log_violation(self, violation: GuardRailViolation, state: Optional[SharedState] = None):
        """
        Log guard rail violation

        Args:
            violation: Violation exception
            state: Optional shared state to update
        """
        entry = {
            "timestamp": violation.timestamp,
            "agent_role": violation.agent_role.value,
            "violation_type": violation.violation_type,
            "severity": violation.severity,
            "message": str(violation),
        }

        self.violations.append(entry)

        if state is not None:
            state["guard_rail_violations"].append(entry)

        logger.error(
            f"GUARD RAIL VIOLATION: {violation.violation_type} "
            f"by {violation.agent_role} (severity: {violation.severity})"
        )

    def get_violations_by_agent(self, agent_role: AgentRole) -> List[Dict[str, Any]]:
        """Get all violations by specific agent"""
        return [v for v in self.violations if v["agent_role"] == agent_role.value]

    def get_critical_violations(self) -> List[Dict[str, Any]]:
        """Get all critical violations"""
        return [v for v in self.violations if v["severity"] == "critical"]


# ============================================================================
# GUARD COMPOSITION
# ============================================================================


def create_cfo_entry_guard() -> SubgraphEntryGuard:
    """Create entry guard for CFO subgraph"""
    return SubgraphEntryGuard(allowed_roles={AgentRole.CEO}, domain=Domain.FINANCE)


def create_engineer_entry_guard() -> SubgraphEntryGuard:
    """Create entry guard for Engineer subgraph"""
    return SubgraphEntryGuard(allowed_roles={AgentRole.CEO}, domain=Domain.ENGINEERING)


def create_researcher_entry_guard() -> SubgraphEntryGuard:
    """Create entry guard for Researcher subgraph"""
    return SubgraphEntryGuard(
        allowed_roles={AgentRole.CEO, AgentRole.ENGINEER},  # Engineer can request research
        domain=Domain.RESEARCH,
    )
