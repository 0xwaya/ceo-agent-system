"""
Service Layer - Business logic separation from presentation

Implements services for agents, state management, and validation.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from models import (
    AgentType, CompanyInfo, Task, TaskBreakdown, TaskPriority, TaskStatus,
    BudgetTracker, BudgetAllocation, AgentExecutionRequest, AgentExecutionResult,
    OrchestrationState, ExecutionPhase
)
from exceptions import (
    AgentNotFoundError, InvalidAgentTypeError, StateError,
    OrchestrationError, InsufficientBudgetError
)
from logger import OrchestrationLogger, get_agent_logger
from config import BudgetConfig, AgentConfig


# ============================================================================
# AGENT SERVICE
# ============================================================================

class AgentService:
    """
    Service for managing agent lifecycle and execution
    
    Separates agent management logic from presentation layer.
    """
    
    def __init__(self, agent_registry: Optional[Dict[AgentType, Any]] = None):
        """
        Initialize agent service
        
        Args:
            agent_registry: Registry of available agents
        """
        self.agent_registry = agent_registry or {}
        self.logger = OrchestrationLogger()
    
    def register_agent(self, agent_type: AgentType, agent_class: type):
        """
        Register an agent type
        
        Args:
            agent_type: Agent type to register
            agent_class: Agent class
        """
        self.agent_registry[agent_type] = agent_class
    
    def get_agent(
        self,
        agent_type: AgentType,
        budget_allocation: Optional[BudgetAllocation] = None
    ) -> Any:
        """
        Get agent instance
        
        Args:
            agent_type: Type of agent
            budget_allocation: Optional budget allocation
        
        Returns:
            Agent instance
        
        Raises:
            AgentNotFoundError: If agent type not registered
        """
        if agent_type not in self.agent_registry:
            raise AgentNotFoundError(
                f"Agent type '{agent_type.value}' not registered"
            )
        
        agent_class = self.agent_registry[agent_type]
        agent_logger = get_agent_logger(agent_type.value)
        
        # Instantiate with dependency injection
        return agent_class(
            agent_type=agent_type,
            budget_allocation=budget_allocation,
            logger=agent_logger
        )
    
    def execute_agent(
        self,
        request: AgentExecutionRequest
    ) -> AgentExecutionResult:
        """
        Execute an agent
        
        Args:
            request: Execution request
        
        Returns:
            Execution result
        """
        # Get budget allocation
        budget_tracker = BudgetTracker.create_default()
        budget_allocation = budget_tracker.get_allocation(request.agent_type)
        
        # Get agent instance
        agent = self.get_agent(request.agent_type, budget_allocation)
        
        # Execute
        self.logger.log_agent_deployment(request.agent_type.value)
        
        result = agent.execute(
            company_info=request.company_info,
            tasks=request.tasks,
            context=request.context
        )
        
        return result
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """
        Get list of available agents
        
        Returns:
            List of agent information
        """
        agents = []
        
        for agent_type in self.agent_registry.keys():
            budget = BudgetConfig.get_agent_budget(agent_type.value)
            
            # Create temporary instance to get capabilities
            temp_agent = self.get_agent(agent_type)
            
            agents.append({
                'type': agent_type.value,
                'capabilities': temp_agent.get_capabilities(),
                'domain': temp_agent.get_domain(),
                'budget': budget
            })
        
        return agents
    
    def validate_agent_type(self, agent_type: str) -> AgentType:
        """
        Validate and convert agent type string
        
        Args:
            agent_type: Agent type string
        
        Returns:
            AgentType enum
        
        Raises:
            InvalidAgentTypeError: If invalid
        """
        try:
            return AgentType(agent_type)
        except ValueError:
            raise InvalidAgentTypeError(
                f"Invalid agent type: '{agent_type}'. "
                f"Valid types: {[t.value for t in AgentType]}"
            )


# ============================================================================
# STATE SERVICE
# ============================================================================

class StateService:
    """
    Service for managing orchestration state
    
    Handles state lifecycle, persistence, and validation.
    """
    
    def __init__(self):
        """Initialize state service"""
        self.active_states: Dict[str, OrchestrationState] = {}
        self.logger = OrchestrationLogger()
    
    def create_state(
        self,
        company_info: CompanyInfo,
        state_id: Optional[str] = None
    ) -> OrchestrationState:
        """
        Create new orchestration state
        
        Args:
            company_info: Company information
            state_id: Optional state ID (generated if not provided)
        
        Returns:
            New orchestration state
        """
        state_id = state_id or self._generate_state_id(company_info.name)
        
        state = OrchestrationState(
            company_info=company_info,
            current_phase=ExecutionPhase.ANALYSIS,
            budget_tracker=BudgetTracker.create_default()
        )
        
        self.active_states[state_id] = state
        
        return state
    
    def get_state(self, state_id: str) -> OrchestrationState:
        """
        Get orchestration state
        
        Args:
            state_id: State identifier
        
        Returns:
            Orchestration state
        
        Raises:
            StateError: If state not found
        """
        if state_id not in self.active_states:
            raise StateError(f"State '{state_id}' not found")
        
        return self.active_states[state_id]
    
    def update_state(self, state_id: str, state: OrchestrationState):
        """
        Update orchestration state
        
        Args:
            state_id: State identifier
            state: Updated state
        """
        state.update_timestamp()
        self.active_states[state_id] = state
    
    def delete_state(self, state_id: str):
        """
        Delete orchestration state
        
        Args:
            state_id: State identifier
        """
        if state_id in self.active_states:
            del self.active_states[state_id]
    
    def transition_phase(
        self,
        state: OrchestrationState,
        to_phase: ExecutionPhase
    ) -> OrchestrationState:
        """
        Transition state to new phase
        
        Args:
            state: Current state
            to_phase: Target phase
        
        Returns:
            Updated state
        """
        state.set_phase(to_phase)
        return state
    
    def add_agent_result(
        self,
        state: OrchestrationState,
        agent_type: AgentType,
        result: AgentExecutionResult
    ) -> OrchestrationState:
        """
        Add agent execution result to state
        
        Args:
            state: Orchestration state
            agent_type: Agent type
            result: Execution result
        
        Returns:
            Updated state
        """
        state.agent_results[agent_type] = result
        
        # Update budget tracker
        if result.success and result.cost > 0:
            allocation = state.budget_tracker.get_allocation(agent_type)
            if allocation:
                allocation.spend(result.cost)
        
        # Add log entry
        status = "SUCCESS" if result.success else "FAILED"
        state.add_log_entry(
            f"Agent {agent_type.value} completed: {status} "
            f"(Cost: ${result.cost:.2f})"
        )
        
        return state
    
    def _generate_state_id(self, company_name: str) -> str:
        """Generate unique state ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        clean_name = "".join(c for c in company_name if c.isalnum())
        return f"{clean_name}_{timestamp}"


# ============================================================================
# VALIDATION SERVICE
# ============================================================================

class ValidationService:
    """
    Service for input validation and sanitization
    
    Validates requests before processing.
    """
    
    @staticmethod
    def validate_company_info(company_info: CompanyInfo) -> bool:
        """
        Validate company information
        
        Args:
            company_info: Company info to validate
        
        Returns:
            True if valid
        
        Raises:
            ValidationError: If invalid
        """
        # Pydantic already validates on creation
        # Additional business logic validation here if needed
        return True
    
    @staticmethod
    def validate_budget_request(
        agent_type: AgentType,
        amount: float,
        budget_tracker: BudgetTracker
    ) -> bool:
        """
        Validate budget request
        
        Args:
            agent_type: Agent requesting budget
            amount: Amount requested
            budget_tracker: Current budget tracker
        
        Returns:
            True if valid
        
        Raises:
            InsufficientBudgetError: If insufficient budget
        """
        allocation = budget_tracker.get_allocation(agent_type)
        
        if not allocation:
            raise InsufficientBudgetError(
                required=amount,
                available=0,
                agent_type=agent_type.value
            )
        
        if amount > allocation.remaining:
            raise InsufficientBudgetError(
                required=amount,
                available=allocation.remaining,
                agent_type=agent_type.value
            )
        
        return True
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 10000) -> str:
        """
        Sanitize text input
        
        Args:
            text: Input text
            max_length: Maximum allowed length
        
        Returns:
            Sanitized text
        """
        # Remove potentially dangerous characters
        text = text.strip()
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        return text


# ============================================================================
# ORCHESTRATION SERVICE
# ============================================================================

class OrchestrationService:
    """
    Service for orchestrating multi-agent workflows
    
    Coordinates execution of multiple agents in sequence.
    """
    
    def __init__(
        self,
        agent_service: AgentService,
        state_service: StateService
    ):
        """
        Initialize orchestration service
        
        Args:
            agent_service: Agent service instance
            state_service: State service instance
        """
        self.agent_service = agent_service
        self.state_service = state_service
        self.logger = OrchestrationLogger()
    
    def create_task_breakdown(
        self,
        company_info: CompanyInfo
    ) -> TaskBreakdown:
        """
        Create task breakdown for company objectives
        
        Args:
            company_info: Company information
        
        Returns:
            Task breakdown
        """
        tasks = []
        task_id_counter = 1
        
        # Legal tasks
        tasks.append(Task(
            id=f"legal_{task_id_counter}",
            description="Ensure legal compliance and create documents",
            priority=TaskPriority.CRITICAL,
            agent_type=AgentType.LEGAL,
            estimated_cost=BudgetConfig.LEGAL_BUDGET
        ))
        task_id_counter += 1
        
        # Branding tasks
        tasks.append(Task(
            id=f"branding_{task_id_counter}",
            description="Develop brand identity and visual assets",
            priority=TaskPriority.HIGH,
            agent_type=AgentType.BRANDING,
            estimated_cost=BudgetConfig.BRANDING_BUDGET
        ))
        task_id_counter += 1
        
        # Web development tasks
        tasks.append(Task(
            id=f"webdev_{task_id_counter}",
            description="Build and deploy website",
            priority=TaskPriority.HIGH,
            agent_type=AgentType.WEB_DEV,
            estimated_cost=BudgetConfig.WEB_DEV_BUDGET,
            dependencies=[f"branding_{task_id_counter-1}"]
        ))
        task_id_counter += 1
        
        # MarTech tasks
        tasks.append(Task(
            id=f"martech_{task_id_counter}",
            description="Configure marketing technology stack",
            priority=TaskPriority.MEDIUM,
            agent_type=AgentType.MARTECH,
            estimated_cost=BudgetConfig.MARTECH_BUDGET
        ))
        task_id_counter += 1
        
        # Content tasks
        tasks.append(Task(
            id=f"content_{task_id_counter}",
            description="Create content marketing assets",
            priority=TaskPriority.MEDIUM,
            agent_type=AgentType.CONTENT,
            estimated_cost=BudgetConfig.CONTENT_BUDGET,
            dependencies=[f"branding_{2}", f"webdev_{3}"]
        ))
        task_id_counter += 1
        
        # Campaign tasks
        tasks.append(Task(
            id=f"campaigns_{task_id_counter}",
            description="Launch and manage marketing campaigns",
            priority=TaskPriority.HIGH,
            agent_type=AgentType.CAMPAIGNS,
            estimated_cost=BudgetConfig.CAMPAIGNS_BUDGET,
            dependencies=[f"content_{task_id_counter-1}", f"martech_{task_id_counter-2}"]
        ))
        
        return TaskBreakdown(tasks=tasks)
    
    def execute_orchestration(
        self,
        company_info: CompanyInfo,
        callback: Optional[callable] = None
    ) -> OrchestrationState:
        """
        Execute full orchestration
        
        Args:
            company_info: Company information
            callback: Optional callback for progress updates
        
        Returns:
            Final orchestration state
        """
        start_time = time.time()
        
        # Create state
        state = self.state_service.create_state(company_info)
        state_id = self._generate_state_id(company_info.name)
        
        try:
            # Phase 1: Analysis
            if callback:
                callback('phase', ExecutionPhase.ANALYSIS.value)
            
            state = self.state_service.transition_phase(state, ExecutionPhase.PLANNING)
            
            # Phase 2: Planning
            if callback:
                callback('phase', ExecutionPhase.PLANNING.value)
            
            task_breakdown = self.create_task_breakdown(company_info)
            state.task_breakdown = task_breakdown
            
            state = self.state_service.transition_phase(state, ExecutionPhase.EXECUTION)
            
            # Phase 3: Execution
            if callback:
                callback('phase', ExecutionPhase.EXECUTION.value)
            
            # Execute agents in order
            agent_order = [
                AgentType.LEGAL,
                AgentType.BRANDING,
                AgentType.WEB_DEV,
                AgentType.MARTECH,
                AgentType.CONTENT,
                AgentType.CAMPAIGNS
            ]
            
            for agent_type in agent_order:
                if callback:
                    callback('agent_deploying', agent_type.value)
                
                # Get tasks for this agent
                agent_tasks = task_breakdown.get_tasks_by_agent(agent_type)
                
                # Create execution request
                request = AgentExecutionRequest(
                    agent_type=agent_type,
                    company_info=company_info,
                    tasks=agent_tasks
                )
                
                # Execute
                result = self.agent_service.execute_agent(request)
                
                # Update state
                state = self.state_service.add_agent_result(state, agent_type, result)
                
                if callback:
                    callback('agent_deployed', agent_type.value)
            
            # Phase 4: Review
            state = self.state_service.transition_phase(state, ExecutionPhase.REVIEW)
            
            # Phase 5: Completion
            has_errors = len(state.get_failed_agents()) > 0
            state.mark_complete(has_errors)
            
            execution_time = time.time() - start_time
            
            self.logger.log_orchestration_complete(
                duration=execution_time,
                total_cost=state.budget_tracker.total_spent,
                success_count=len(state.get_completed_agents()),
                total_agents=len(agent_order)
            )
            
            return state
            
        except Exception as e:
            self.logger.log_orchestration_error(str(e))
            state.add_log_entry(f"ERROR: {str(e)}")
            state.mark_complete(has_errors=True)
            raise OrchestrationError(
                "Orchestration failed",
                details={'error': str(e)},
                original_exception=e
            )
    
    def _generate_state_id(self, company_name: str) -> str:
        """Generate state ID"""
        return self.state_service._generate_state_id(company_name)
