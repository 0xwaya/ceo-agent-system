"""
Pydantic Models - Immutable, validated state management

Type-safe state models with automatic validation and serialization.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from config import BudgetConfig, Constants


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Request model for CFO strategic analysis"""
    company_name: str = Field(..., min_length=1, max_length=200)
    dba_name: Optional[str] = Field(None, max_length=200)
    industry: str = Field(..., min_length=3, max_length=100)
    location: str = Field(..., min_length=3, max_length=100)
    budget: float = Field(gt=0, le=100000)
    timeline: int = Field(gt=0, le=365)
    objectives: Optional[List[str]] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "Amazon Granite LLC",
                "dba_name": "SURFACECRAFT STUDIO",
                "industry": "Granite & Engineered Quartz Countertops",
                "location": "Cincinnati, Ohio",
                "budget": 5000,
                "timeline": 90,
                "objectives": ["Launch digital presence", "Build brand identity"]
            }
        }


class AgentExecuteRequest(BaseModel):
    """Request model for agent execution"""
    task: str = Field(..., min_length=1)
    company_info: Dict[str, Any] = Field(...)
    requirements: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "task": "Design brand identity for countertop business",
                "company_info": {
                    "name": "SURFACECRAFT STUDIO",
                    "industry": "Granite Countertops",
                    "location": "Cincinnati, OH"
                }
            }
        }


class OrchestrationRequest(BaseModel):
    """Request model for full orchestration"""
    company_info: Dict[str, Any] = Field(...)
    objectives: Optional[List[str]] = Field(default_factory=list)
    
    @field_validator('company_info')
    @classmethod
    def validate_company_info(cls, v):
        required_fields = ['company_name', 'industry', 'location']
        for field in required_fields:
            if field not in v and field.replace('_', '') not in v:
                raise ValueError(f'Missing required field: {field}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_info": {
                    "company_name": "Amazon Granite LLC",
                    "industry": "Countertops",
                    "location": "Cincinnati, OH"
                },
                "objectives": ["Launch business", "Build brand"]
            }
        }


class AnalyzeResponse(BaseModel):
    """Response model for strategic analysis"""
    success: bool
    tasks: List[Dict[str, Any]] = Field(default_factory=list)
    budget_allocation: Dict[str, float] = Field(default_factory=dict)
    risks: List[str] = Field(default_factory=list)
    timeline: int
    message: Optional[str] = None


class AgentExecuteResponse(BaseModel):
    """Response model for agent execution"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    agent_type: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ErrorResponse(BaseModel):
    """Standardized error response"""
    error: str
    details: Optional[Any] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    success: bool = False


# ============================================================================
# ENUMS
# ============================================================================

class AgentType(str, Enum):
    """Valid agent types"""
    BRANDING = "branding"
    WEB_DEV = "web_dev"
    LEGAL = "legal"
    MARTECH = "martech"
    CONTENT = "content"
    CAMPAIGNS = "campaigns"


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
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionPhase(str, Enum):
    """Orchestration execution phases"""
    ANALYSIS = "analysis"
    PLANNING = "planning"
    EXECUTION = "execution"
    REVIEW = "review"
    COMPLETION = "completion"


# ============================================================================
# BASE MODELS
# ============================================================================

class BaseState(BaseModel):
    """Base state model with common fields"""
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = False  # Allow updates to updated_at
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        object.__setattr__(self, 'updated_at', datetime.utcnow())


# ============================================================================
# TASK MODELS
# ============================================================================

class Task(BaseModel):
    """Individual task model"""
    
    id: str
    description: str
    priority: TaskPriority
    agent_type: AgentType
    status: TaskStatus = TaskStatus.PENDING
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    deliverables: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        frozen = False
    
    @field_validator('estimated_cost', 'actual_cost')
    @classmethod
    def validate_cost(cls, v):
        if v < 0:
            raise ValueError("Cost cannot be negative")
        return round(v, 2)
    
    def mark_in_progress(self):
        """Mark task as in progress"""
        object.__setattr__(self, 'status', TaskStatus.IN_PROGRESS)
    
    def mark_completed(self, actual_cost: float = None):
        """Mark task as completed"""
        object.__setattr__(self, 'status', TaskStatus.COMPLETED)
        if actual_cost is not None:
            object.__setattr__(self, 'actual_cost', actual_cost)
    
    def mark_failed(self):
        """Mark task as failed"""
        object.__setattr__(self, 'status', TaskStatus.FAILED)


class TaskBreakdown(BaseModel):
    """Collection of tasks with metadata"""
    
    tasks: List[Task]
    total_estimated_cost: float = 0.0
    total_actual_cost: float = 0.0
    
    class Config:
        frozen = False
    
    @model_validator(mode='after')
    def calculate_totals(self):
        """Calculate total costs from tasks"""
        self.total_estimated_cost = sum(t.estimated_cost for t in self.tasks)
        self.total_actual_cost = sum(t.actual_cost for t in self.tasks)
        return self
    
    def get_tasks_by_agent(self, agent_type: AgentType) -> List[Task]:
        """Get all tasks for specific agent"""
        return [t for t in self.tasks if t.agent_type == agent_type]
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with specific status"""
        return [t for t in self.tasks if t.status == status]
    
    def get_tasks_by_priority(self, priority: TaskPriority) -> List[Task]:
        """Get all tasks with specific priority"""
        return [t for t in self.tasks if t.priority == priority]


# ============================================================================
# BUDGET MODELS
# ============================================================================

class BudgetAllocation(BaseModel):
    """Budget allocation for a single agent"""
    
    agent_type: AgentType
    allocated: float
    spent: float = 0.0
    reserved: float = 0.0
    
    class Config:
        frozen = False
    
    @field_validator('allocated', 'spent', 'reserved')
    @classmethod
    def validate_amounts(cls, v):
        if v < 0:
            raise ValueError("Budget amounts cannot be negative")
        return round(v, 2)
    
    @property
    def remaining(self) -> float:
        """Calculate remaining budget"""
        return round(self.allocated - self.spent - self.reserved, 2)
    
    @property
    def utilization_percent(self) -> float:
        """Calculate budget utilization percentage"""
        if self.allocated == 0:
            return 0.0
        return round((self.spent / self.allocated) * 100, 2)
    
    def spend(self, amount: float) -> bool:
        """Spend from budget"""
        if amount > self.remaining:
            return False
        object.__setattr__(self, 'spent', round(self.spent + amount, 2))
        return True
    
    def reserve(self, amount: float) -> bool:
        """Reserve budget"""
        if amount > self.remaining:
            return False
        object.__setattr__(self, 'reserved', round(self.reserved + amount, 2))
        return True
    
    def release_reservation(self, amount: float):
        """Release reserved budget"""
        object.__setattr__(self, 'reserved', max(0, round(self.reserved - amount, 2)))


class BudgetTracker(BaseModel):
    """Overall budget tracking"""
    
    total_budget: float = BudgetConfig.TOTAL_BUDGET
    allocations: Dict[AgentType, BudgetAllocation] = Field(default_factory=dict)
    
    class Config:
        frozen = False
    
    @classmethod
    def create_default(cls) -> 'BudgetTracker':
        """Create budget tracker with default allocations"""
        allocations = {
            AgentType.LEGAL: BudgetAllocation(
                agent_type=AgentType.LEGAL,
                allocated=BudgetConfig.LEGAL_BUDGET
            ),
            AgentType.BRANDING: BudgetAllocation(
                agent_type=AgentType.BRANDING,
                allocated=BudgetConfig.BRANDING_BUDGET
            ),
            AgentType.WEB_DEV: BudgetAllocation(
                agent_type=AgentType.WEB_DEV,
                allocated=BudgetConfig.WEB_DEV_BUDGET
            ),
            AgentType.MARTECH: BudgetAllocation(
                agent_type=AgentType.MARTECH,
                allocated=BudgetConfig.MARTECH_BUDGET
            ),
            AgentType.CONTENT: BudgetAllocation(
                agent_type=AgentType.CONTENT,
                allocated=BudgetConfig.CONTENT_BUDGET
            ),
            AgentType.CAMPAIGNS: BudgetAllocation(
                agent_type=AgentType.CAMPAIGNS,
                allocated=BudgetConfig.CAMPAIGNS_BUDGET
            )
        }
        return cls(allocations=allocations)
    
    @property
    def total_spent(self) -> float:
        """Total amount spent across all agents"""
        return round(sum(a.spent for a in self.allocations.values()), 2)
    
    @property
    def total_remaining(self) -> float:
        """Total remaining budget"""
        return round(self.total_budget - self.total_spent, 2)
    
    @property
    def utilization_percent(self) -> float:
        """Overall budget utilization"""
        if self.total_budget == 0:
            return 0.0
        return round((self.total_spent / self.total_budget) * 100, 2)
    
    def get_allocation(self, agent_type: AgentType) -> Optional[BudgetAllocation]:
        """Get budget allocation for agent"""
        return self.allocations.get(agent_type)


# ============================================================================
# COMPANY MODELS
# ============================================================================

class CompanyInfo(BaseModel):
    """Company information for orchestration"""
    
    name: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(..., min_length=1, max_length=100)
    target_audience: str = Field(..., min_length=1, max_length=500)
    objectives: str = Field(..., min_length=10, max_length=2000)
    unique_value_proposition: Optional[str] = Field(None, max_length=500)
    competitors: Optional[str] = Field(None, max_length=500)
    timeline: Optional[str] = Field(None, max_length=200)
    
    @field_validator('name', 'industry', 'target_audience', 'objectives')
    @classmethod
    def validate_not_empty(cls, v, info):
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()


# ============================================================================
# AGENT EXECUTION MODELS
# ============================================================================

class AgentExecutionRequest(BaseModel):
    """Request to execute an agent"""
    
    agent_type: AgentType
    company_info: CompanyInfo
    tasks: Optional[List[Task]] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    timeout: int = Field(default=300, ge=1, le=3600)


class AgentExecutionResult(BaseModel):
    """Result of agent execution"""
    
    agent_type: AgentType
    success: bool
    deliverables: List[str]
    cost: float = 0.0
    execution_time: float = 0.0  # seconds
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('cost', 'execution_time')
    @classmethod
    def validate_positive(cls, v):
        if v < 0:
            raise ValueError("Value cannot be negative")
        return round(v, 2)


# ============================================================================
# ORCHESTRATION STATE
# ============================================================================

class OrchestrationState(BaseState):
    """Complete orchestration state"""
    
    company_info: CompanyInfo
    current_phase: ExecutionPhase = ExecutionPhase.ANALYSIS
    task_breakdown: Optional[TaskBreakdown] = None
    budget_tracker: BudgetTracker = Field(default_factory=BudgetTracker.create_default)
    agent_results: Dict[AgentType, AgentExecutionResult] = Field(default_factory=dict)
    execution_log: List[str] = Field(default_factory=list)
    is_complete: bool = False
    has_errors: bool = False
    
    def add_log_entry(self, message: str):
        """Add entry to execution log"""
        timestamp = datetime.utcnow().isoformat()
        self.execution_log.append(f"[{timestamp}] {message}")
        self.update_timestamp()
    
    def set_phase(self, phase: ExecutionPhase):
        """Update execution phase"""
        object.__setattr__(self, 'current_phase', phase)
        self.add_log_entry(f"Phase changed to: {phase.value}")
    
    def mark_complete(self, has_errors: bool = False):
        """Mark orchestration as complete"""
        object.__setattr__(self, 'is_complete', True)
        object.__setattr__(self, 'has_errors', has_errors)
        self.set_phase(ExecutionPhase.COMPLETION)
    
    def get_completed_agents(self) -> List[AgentType]:
        """Get list of completed agents"""
        return [
            agent_type for agent_type, result in self.agent_results.items()
            if result.success
        ]
    
    def get_failed_agents(self) -> List[AgentType]:
        """Get list of failed agents"""
        return [
            agent_type for agent_type, result in self.agent_results.items()
            if not result.success
        ]


# ============================================================================
# GUARD RAIL MODELS
# ============================================================================

class GuardRailViolation(BaseModel):
    """Guard rail violation record"""
    
    rule: str
    severity: Literal["error", "warning", "info"]
    message: str
    suggestion: str
    context: Dict[str, Any] = Field(default_factory=dict)


class GuardRailValidationResult(BaseModel):
    """Result of guard rail validation"""
    
    is_valid: bool
    violations: List[GuardRailViolation] = Field(default_factory=list)
    warnings: List[GuardRailViolation] = Field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        """Check if there are error violations"""
        return any(v.severity == "error" for v in self.violations)
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings"""
        return len(self.warnings) > 0


# ============================================================================
# VALIDATION MODELS
# ============================================================================

class ValidationResult(BaseModel):
    """Generic validation result"""
    
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class AnalyzeObjectivesRequest(BaseModel):
    """Request for CFO analysis"""
    
    company_info: CompanyInfo


class AnalyzeObjectivesResponse(BaseModel):
    """Response from CFO analysis"""
    
    task_breakdown: TaskBreakdown
    budget_projection: BudgetTracker
    execution_plan: List[str]
    warnings: List[str] = Field(default_factory=list)


class ExecuteAgentRequest(BaseModel):
    """Request to execute specific agent"""
    
    agent_type: AgentType
    company_info: CompanyInfo
    additional_context: Dict[str, Any] = Field(default_factory=dict)


class ExecuteAgentResponse(BaseModel):
    """Response from agent execution"""
    
    agent_type: AgentType
    result: AgentExecutionResult
    updated_budget: Optional[BudgetAllocation] = None
