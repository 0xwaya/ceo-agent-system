"""
Base Agent Class - Abstract base with dependency injection

Defines the contract and shared functionality for all agents.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from models import AgentType, Task, TaskStatus, AgentExecutionResult, BudgetAllocation, CompanyInfo
from exceptions import (
    AgentExecutionError,
    InsufficientBudgetError,
    DeliverableError,
    GuardRailViolationError,
)
from logger import AgentLogger
from config import AgentConfig


class BaseAgent(ABC):
    """
    Abstract base class for all agents

    Implements dependency injection, common functionality, and enforces
    the agent contract through abstract methods.
    """

    def __init__(
        self,
        agent_type: AgentType,
        budget_allocation: Optional[BudgetAllocation] = None,
        logger: Optional[AgentLogger] = None,
        guard_rail_validator: Optional[Any] = None,
    ):
        """
        Initialize base agent with dependencies

        Args:
            agent_type: Type of agent
            budget_allocation: Budget allocation (injected dependency)
            logger: Logger instance (injected dependency)
            guard_rail_validator: Guard rail validator (injected dependency)
        """
        self.agent_type = agent_type
        self.budget_allocation = budget_allocation
        self.logger = logger or AgentLogger(agent_type.value)
        self.guard_rail_validator = guard_rail_validator

        # Execution state
        self._is_executing = False
        self._execution_start_time: Optional[float] = None
        self._deliverables: List[str] = []
        self._warnings: List[str] = []
        self._metadata: Dict[str, Any] = {}

    # ========================================================================
    # ABSTRACT METHODS (Must be implemented by subclasses)
    # ========================================================================

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return list of agent capabilities

        Returns:
            List of capability descriptions
        """
        pass

    @abstractmethod
    def get_domain(self) -> str:
        """
        Return the domain this agent operates in

        Returns:
            Domain name (e.g., "digital_marketing", "legal_compliance")
        """
        pass

    @abstractmethod
    def execute_task(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific task

        Args:
            task: Task to execute
            context: Execution context

        Returns:
            Task execution result
        """
        pass

    @abstractmethod
    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        Validate that context contains required information

        Args:
            context: Context to validate

        Returns:
            True if valid

        Raises:
            ValidationError if invalid
        """
        pass

    # ========================================================================
    # CONCRETE METHODS (Implemented functionality)
    # ========================================================================

    def execute(
        self,
        company_info: CompanyInfo,
        tasks: Optional[List[Task]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentExecutionResult:
        """
        Main execution method - orchestrates task execution

        Args:
            company_info: Company information
            tasks: Optional list of tasks to execute
            context: Optional execution context

        Returns:
            AgentExecutionResult with deliverables and metrics

        Raises:
            AgentExecutionError: If execution fails
        """
        # Initialize
        self._execution_start_time = time.time()
        self._is_executing = True
        self._deliverables = []
        self._warnings = []
        self._metadata = {}

        try:
            # Prepare context
            exec_context = self._prepare_context(company_info, context or {})

            # Validate context
            self.validate_context(exec_context)

            # Log start
            self.logger.log_execution_start(f"Agent for {company_info.name}")

            # Execute tasks or run default
            if tasks:
                for task in tasks:
                    self._execute_single_task(task, exec_context)
            else:
                self._execute_default(exec_context)

            # Validate deliverables
            if not self._deliverables:
                raise DeliverableError(f"Agent {self.agent_type.value} produced no deliverables")

            # Calculate execution time and cost
            execution_time = time.time() - self._execution_start_time
            total_cost = sum(
                task.actual_cost for task in (tasks or []) if task.status == TaskStatus.COMPLETED
            )

            # Log completion
            self.logger.log_execution_complete(execution_time, total_cost)

            # Create result
            result = AgentExecutionResult(
                agent_type=self.agent_type,
                success=True,
                deliverables=self._deliverables,
                cost=total_cost,
                execution_time=execution_time,
                warnings=self._warnings,
                metadata=self._metadata,
            )

            return result

        except Exception as e:
            execution_time = time.time() - (self._execution_start_time or time.time())
            error_message = str(e)

            self.logger.log_execution_error(error_message)

            # Create failure result
            result = AgentExecutionResult(
                agent_type=self.agent_type,
                success=False,
                deliverables=self._deliverables,
                cost=0.0,
                execution_time=execution_time,
                error_message=error_message,
                warnings=self._warnings,
                metadata=self._metadata,
            )

            return result

        finally:
            self._is_executing = False

    def _execute_single_task(self, task: Task, context: Dict[str, Any]):
        """Execute a single task"""
        try:
            # Mark task in progress
            task.mark_in_progress()

            # Validate budget
            if self.budget_allocation:
                if task.estimated_cost > self.budget_allocation.remaining:
                    raise InsufficientBudgetError(
                        required=task.estimated_cost,
                        available=self.budget_allocation.remaining,
                        agent_type=self.agent_type.value,
                    )

            # Execute task
            task_result = self.execute_task(task, context)

            # Process result
            if "deliverables" in task_result:
                self._deliverables.extend(task_result["deliverables"])

            if "cost" in task_result:
                actual_cost = task_result["cost"]
                task.mark_completed(actual_cost)

                # Update budget
                if self.budget_allocation:
                    self.budget_allocation.spend(actual_cost)
                    self.logger.log_budget_usage(actual_cost, self.budget_allocation.remaining)
            else:
                task.mark_completed()

            # Log deliverables
            for deliverable in task_result.get("deliverables", []):
                self.logger.log_deliverable(deliverable)

        except Exception as e:
            task.mark_failed()
            raise AgentExecutionError(
                f"Task {task.id} failed: {str(e)}",
                details={"task_id": task.id, "error": str(e)},
                original_exception=e,
            )

    def _execute_default(self, context: Dict[str, Any]):
        """
        Default execution when no tasks provided
        Subclasses can override this for default behavior
        """
        # Create a generic task
        task = Task(
            id=f"{self.agent_type.value}_default",
            description=f"Execute {self.agent_type.value} agent",
            priority="high",
            agent_type=self.agent_type,
            estimated_cost=0.0,
        )

        self._execute_single_task(task, context)

    def _prepare_context(
        self, company_info: CompanyInfo, additional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare execution context"""
        return {
            "company_info": company_info,
            "agent_type": self.agent_type.value,
            "capabilities": self.get_capabilities(),
            "domain": self.get_domain(),
            "timestamp": datetime.utcnow().isoformat(),
            **additional_context,
        }

    def validate_guard_rails(self, operation: str, data: Dict[str, Any]) -> bool:
        """
        Validate operation against guard rails

        Args:
            operation: Operation being performed
            data: Data to validate

        Returns:
            True if valid

        Raises:
            GuardRailViolationError if invalid
        """
        if not self.guard_rail_validator:
            return True

        # Use injected validator
        result = self.guard_rail_validator.validate(
            agent_type=self.agent_type.value, operation=operation, data=data
        )

        if not result.is_valid:
            violation_msg = "; ".join([v.message for v in result.violations])
            self.logger.log_guard_rail_violation(violation_msg)
            raise GuardRailViolationError(rule="guard_rail_validation", violation=violation_msg)

        # Log warnings
        for warning in result.warnings:
            self._warnings.append(warning.message)

        return True

    def add_deliverable(self, deliverable: str):
        """Add a deliverable"""
        self._deliverables.append(deliverable)
        self.logger.log_deliverable(deliverable)

    def add_warning(self, warning: str):
        """Add a warning"""
        self._warnings.append(warning)
        self.logger.warning(warning)

    def set_metadata(self, key: str, value: Any):
        """Set metadata"""
        self._metadata[key] = value

    def check_budget(self, required_amount: float) -> bool:
        """
        Check if budget is available

        Args:
            required_amount: Amount needed

        Returns:
            True if budget available

        Raises:
            InsufficientBudgetError if not available
        """
        if not self.budget_allocation:
            return True

        if required_amount > self.budget_allocation.remaining:
            raise InsufficientBudgetError(
                required=required_amount,
                available=self.budget_allocation.remaining,
                agent_type=self.agent_type.value,
            )

        return True

    def spend_budget(self, amount: float) -> bool:
        """
        Spend from budget

        Args:
            amount: Amount to spend

        Returns:
            True if successful
        """
        if not self.budget_allocation:
            return True

        success = self.budget_allocation.spend(amount)

        if success:
            self.logger.log_budget_usage(amount, self.budget_allocation.remaining)

        return success

    @property
    def is_executing(self) -> bool:
        """Check if agent is currently executing"""
        return self._is_executing

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation"""
        return {
            "agent_type": self.agent_type.value,
            "capabilities": self.get_capabilities(),
            "domain": self.get_domain(),
            "budget": {
                "allocated": self.budget_allocation.allocated if self.budget_allocation else 0,
                "spent": self.budget_allocation.spent if self.budget_allocation else 0,
                "remaining": self.budget_allocation.remaining if self.budget_allocation else 0,
            }
            if self.budget_allocation
            else None,
            "is_executing": self.is_executing,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} type={self.agent_type.value}>"
