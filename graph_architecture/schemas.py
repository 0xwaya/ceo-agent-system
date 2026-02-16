"""
JSON Schemas for Shared State, Messages, and Checkpoints

Defines the structure for:
1. Global shared state across all agents
2. Message queue format for inter-agent communication
3. Checkpoint format for persistence
4. Agent communication protocol
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional, Literal
from typing_extensions import NotRequired
from datetime import datetime
from enum import Enum
import operator
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# ENUMS
# ============================================================================


class AgentRole(str, Enum):
    """Agent role hierarchy"""

    CEO = "ceo"
    CFO = "cfo"
    ENGINEER = "engineer"
    RESEARCHER = "researcher"
    LEGAL = "legal"
    MARTECH = "martech"


class MessageType(str, Enum):
    """Message types for inter-agent communication"""

    TASK_ASSIGNMENT = "task_assignment"
    STATUS_UPDATE = "status_update"
    SPEC_REQUEST = "spec_request"
    COST_VALIDATION = "cost_validation"
    APPROVAL_REQUEST = "approval_request"
    FINDINGS = "findings"
    SUMMARY = "summary"
    ERROR = "error"


class TaskPriority(str, Enum):
    """Task priority levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    """Task execution status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, Enum):
    """Risk assessment levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# MESSAGE SCHEMAS (Pydantic for validation)
# ============================================================================


class Message(BaseModel):
    """Inter-agent message format"""

    message_id: str = Field(description="Unique message identifier")
    from_agent: AgentRole = Field(description="Sender agent role")
    to_agent: AgentRole = Field(description="Recipient agent role")
    message_type: MessageType = Field(description="Type of message")
    payload: Dict[str, Any] = Field(description="Message content")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    correlation_id: Optional[str] = Field(None, description="For request-response tracking")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message_id": "msg-12345",
                "from_agent": "engineer",
                "to_agent": "researcher",
                "message_type": "spec_request",
                "payload": {
                    "feature": "AR visualization",
                    "requirements": ["WebGL support", "mobile-friendly"],
                },
                "priority": "high",
                "timestamp": "2026-02-13T10:00:00Z",
                "correlation_id": "req-67890",
            }
        }
    )


class TaskMessage(BaseModel):
    """Task assignment message"""

    task_id: str
    task_name: str
    description: str
    required_expertise: AgentRole
    priority: TaskPriority
    estimated_budget: float
    estimated_days: int
    dependencies: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)


class SummaryMessage(BaseModel):
    """Executive summary message (subordinate → CEO)"""

    agent_role: AgentRole
    task_id: str
    status: TaskStatus
    key_findings: List[str]
    risks: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    budget_used: float
    next_steps: List[str] = Field(default_factory=list)
    raw_data_available: bool = Field(
        default=False, description="Raw data not sent, available on request"
    )


class ApprovalRequest(BaseModel):
    """User approval request"""

    request_id: str
    action: str
    rationale: str
    cost: float
    risk_level: RiskLevel
    consequences_if_declined: str
    auto_decline_after: Optional[str] = None  # ISO timestamp


# ============================================================================
# CHECKPOINT SCHEMA (Pydantic)
# ============================================================================


class CheckpointMetadata(BaseModel):
    """Checkpoint metadata for persistence"""

    checkpoint_id: str = Field(description="Unique checkpoint identifier")
    node_id: str = Field(description="Graph node where checkpoint was created")
    agent_role: AgentRole = Field(description="Agent that created checkpoint")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    thread_id: str = Field(description="Execution thread identifier")
    parent_checkpoint_id: Optional[str] = Field(None, description="Previous checkpoint")

    # Execution context
    execution_step: int = Field(description="Step number in execution")
    total_nodes_visited: int = Field(description="Total nodes visited so far")

    # Resource tracking
    budget_spent: float = Field(default=0.0)
    api_calls_made: int = Field(default=0)

    # Status
    is_terminal: bool = Field(default=False, description="Is this a terminal state")
    requires_approval: bool = Field(default=False, description="Waiting for user approval")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "checkpoint_id": "ckpt-abc123",
                "node_id": "cfo_analyze_budget",
                "agent_role": "cfo",
                "timestamp": "2026-02-13T10:30:00Z",
                "thread_id": "session-123",
                "parent_checkpoint_id": "ckpt-abc122",
                "execution_step": 5,
                "total_nodes_visited": 8,
                "budget_spent": 150.0,
                "api_calls_made": 12,
                "is_terminal": False,
                "requires_approval": True,
            }
        }
    )


# ============================================================================
# SHARED STATE SCHEMAS (TypedDict for LangGraph)
# ============================================================================


class SharedState(TypedDict):
    """
    Global shared state accessible to all agents

    Uses LangGraph's reducer pattern for list fields (Annotated with operator.add)
    """

    # Execution metadata
    thread_id: str
    session_start: str
    current_node: str
    execution_step: int

    # Company information (immutable after init)
    company_name: str
    industry: str
    location: str

    # Strategic objectives (set by CEO)
    strategic_objectives: Annotated[List[str], operator.add]
    business_goals: Annotated[List[Dict[str, Any]], operator.add]

    # Budget management (CEO oversees, CFO manages)
    total_budget: float
    budget_allocated: Dict[str, float]
    budget_spent: Dict[str, float]
    budget_remaining: float

    # Timeline tracking
    target_completion_days: int
    current_day: int
    milestones: Annotated[List[Dict[str, Any]], operator.add]

    # Task management
    identified_tasks: Annotated[List[Dict[str, Any]], operator.add]
    assigned_tasks: Dict[str, List[str]]  # agent_role -> [task_ids]
    completed_tasks: Annotated[List[str], operator.add]
    blocked_tasks: Annotated[List[Dict[str, Any]], operator.add]

    # Inter-agent communication
    pending_messages: Annotated[List[Message], operator.add]
    message_history: Annotated[List[Message], operator.add]

    # Agent status tracking
    active_agents: Annotated[List[str], operator.add]
    agent_outputs: Annotated[List[Dict[str, Any]], operator.add]
    agent_status: Dict[str, str]  # agent_role -> status

    # Risk and opportunity management
    risks: Annotated[List[Dict[str, Any]], operator.add]
    risk_mitigation_plans: Dict[str, str]
    opportunities: Annotated[List[str], operator.add]

    # Governance and compliance
    guard_rail_violations: Annotated[List[Dict[str, Any]], operator.add]
    pending_approvals: Annotated[List[ApprovalRequest], operator.add]
    approved_actions: Annotated[List[str], operator.add]
    rejected_actions: Annotated[List[str], operator.add]

    # Deliverables and reporting
    deliverables: Annotated[List[str], operator.add]
    status_reports: Annotated[List[str], operator.add]
    final_summary: str

    # Workflow control
    current_phase: str
    completed_phases: Annotated[List[str], operator.add]

    # Subgraph-specific fields (NotRequired, used internally by subgraphs)
    # CFO fields
    budget_projections: NotRequired[Annotated[List[Dict[str, Any]], operator.add]]
    cost_analysis: NotRequired[Dict[str, Any]]
    compliance_checks: NotRequired[Annotated[List[Dict[str, Any]], operator.add]]
    audit_trail: NotRequired[Annotated[List[Dict[str, Any]], operator.add]]
    executive_summary: NotRequired[str]
    financial_recommendations: NotRequired[Annotated[List[str], operator.add]]

    # Engineer fields
    tech_stack: NotRequired[List[str]]
    code_files: NotRequired[Annotated[List[Dict[str, Any]], operator.add]]
    architecture_decisions: NotRequired[Annotated[List[Dict[str, Any]], operator.add]]
    test_results: NotRequired[Annotated[List[Dict[str, Any]], operator.add]]
    refactoring_log: NotRequired[Annotated[List[Dict[str, Any]], operator.add]]
    deployment_notes: NotRequired[Annotated[List[str], operator.add]]
    implementation_summary: NotRequired[str]

    # Researcher fields
    search_queries: NotRequired[Annotated[List[str], operator.add]]
    documents_analyzed: NotRequired[Annotated[List[Dict[str, Any]], operator.add]]
    citations: NotRequired[Annotated[List[str], operator.add]]
    key_findings: NotRequired[Annotated[List[str], operator.add]]
    assumptions: NotRequired[Annotated[List[Dict[str, Any]], operator.add]]
    confidence_scores: NotRequired[Dict[str, float]]
    research_summary: NotRequired[str]
    recommendations: NotRequired[Annotated[List[str], operator.add]]


class CEOState(SharedState):
    """CEO-specific state (extends SharedState)"""

    # CEO inherits all SharedState fields plus:
    executive_decisions: Annotated[List[Dict[str, Any]], operator.add]
    delegation_log: Annotated[List[Dict[str, Any]], operator.add]
    subgraph_summaries: Annotated[List[SummaryMessage], operator.add]


class CFOSubgraphState(TypedDict):
    """CFO subgraph internal state"""

    # Inherits from SharedState but adds CFO-specific fields

    # Financial analysis
    financial_data: Dict[str, Any]
    budget_projections: Annotated[List[Dict[str, Any]], operator.add]
    cost_analysis: Dict[str, Any]

    # Compliance and auditing
    compliance_checks: Annotated[List[Dict[str, Any]], operator.add]
    audit_trail: Annotated[List[Dict[str, Any]], operator.add]

    # CFO-specific reporting (internal, not exposed to CEO until summarized)
    raw_financial_tables: List[Dict[str, Any]]
    detailed_calculations: Dict[str, Any]

    # Summary to CEO (this is what gets sent upstream)
    executive_summary: str
    financial_recommendations: Annotated[List[str], operator.add]


class EngineerSubgraphState(TypedDict):
    """Engineer subgraph internal state"""

    # Code generation
    code_files: Annotated[List[Dict[str, Any]], operator.add]
    refactoring_log: Annotated[List[Dict[str, Any]], operator.add]
    test_results: Annotated[List[Dict[str, Any]], operator.add]

    # Technical specifications
    tech_stack: List[str]
    architecture_decisions: Annotated[List[Dict[str, Any]], operator.add]

    # Dependencies on other agents
    pending_spec_requests: Annotated[List[str], operator.add]
    pending_cost_validations: Annotated[List[str], operator.add]

    # Implementation summary (sent to CEO)
    implementation_summary: str
    deployment_notes: Annotated[List[str], operator.add]


class ResearcherSubgraphState(TypedDict):
    """Researcher subgraph internal state"""

    # Research data
    search_queries: Annotated[List[str], operator.add]
    documents_analyzed: Annotated[List[Dict[str, Any]], operator.add]
    citations: Annotated[List[str], operator.add]

    # Findings
    key_findings: Annotated[List[str], operator.add]
    assumptions: Annotated[List[Dict[str, Any]], operator.add]
    confidence_scores: Dict[str, float]

    # Structured output (sent to requester)
    research_summary: str
    recommendations: Annotated[List[str], operator.add]


# ============================================================================
# ROUTING SCHEMAS
# ============================================================================


class RoutingDecision(BaseModel):
    """CEO routing decision"""

    target_subgraph: AgentRole
    rationale: str
    priority: TaskPriority
    estimated_duration: int  # days
    requires_approval: bool


class SubgraphEntry(BaseModel):
    """Entry point validation for subgraphs"""

    requester_role: AgentRole
    task_domain: str
    authorization_level: int
    payload: Dict[str, Any]


# ============================================================================
# TOOL SCHEMAS
# ============================================================================


class ToolContext(BaseModel):
    """Context for tool execution"""

    tool_name: str
    agent_role: AgentRole
    budget_allocated: float
    api_keys: Dict[str, str]
    execution_limits: Dict[str, Any]


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================


def validate_message(message: Dict[str, Any]) -> Message:
    """Validate and parse message"""
    return Message(**message)


def validate_checkpoint_metadata(data: Dict[str, Any]) -> CheckpointMetadata:
    """Validate and parse checkpoint metadata"""
    return CheckpointMetadata(**data)


def create_message(
    from_agent: AgentRole,
    to_agent: AgentRole,
    message_type: MessageType,
    payload: Dict[str, Any],
    priority: TaskPriority = TaskPriority.MEDIUM,
    correlation_id: Optional[str] = None,
) -> Message:
    """Factory function for creating messages"""
    import uuid

    return Message(
        message_id=f"msg-{uuid.uuid4().hex[:8]}",
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=message_type,
        payload=payload,
        priority=priority,
        correlation_id=correlation_id,
    )


# ============================================================================
# SHARED STATE INITIALIZATION
# ============================================================================


def create_initial_shared_state(
    company_name: str,
    industry: str,
    location: str,
    total_budget: float,
    target_days: int,
    objectives: List[str],
) -> SharedState:
    """Create initial shared state"""
    import uuid

    return SharedState(
        # Execution metadata
        thread_id=f"thread-{uuid.uuid4().hex[:8]}",
        session_start=datetime.now().isoformat(),
        current_node="START",
        execution_step=0,
        # Company info
        company_name=company_name,
        industry=industry,
        location=location,
        # Strategic objectives
        strategic_objectives=objectives,
        business_goals=[],
        # Budget
        total_budget=total_budget,
        budget_allocated={},
        budget_spent={},
        budget_remaining=total_budget,
        # Timeline
        target_completion_days=target_days,
        current_day=0,
        milestones=[],
        # Tasks
        identified_tasks=[],
        assigned_tasks={},
        completed_tasks=[],
        blocked_tasks=[],
        # Communication
        pending_messages=[],
        message_history=[],
        # Agents
        active_agents=[],
        agent_outputs=[],
        agent_status={},
        # Risk management
        risks=[],
        risk_mitigation_plans={},
        opportunities=[],
        # Governance
        guard_rail_violations=[],
        pending_approvals=[],
        approved_actions=[],
        rejected_actions=[],
        # Deliverables
        deliverables=[],
        status_reports=[],
        final_summary="",
        # Workflow
        current_phase="initialization",
        completed_phases=[],
    )
