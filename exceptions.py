"""
Custom Exception Hierarchy - Structured error handling

Defines all custom exceptions for better error handling and debugging.
"""

from typing import Optional, Dict, Any


# ============================================================================
# BASE EXCEPTIONS
# ============================================================================

class AgentSystemError(Exception):
    """Base exception for all agent system errors"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        self.message = message
        self.details = details or {}
        self.original_exception = original_exception
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        result = {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'details': self.details
        }
        if self.original_exception:
            result['original_error'] = str(self.original_exception)
        return result


# ============================================================================
# VALIDATION EXCEPTIONS
# ============================================================================

class ValidationError(AgentSystemError):
    """Base validation error"""
    pass


class InvalidInputError(ValidationError):
    """Invalid input data"""
    pass


class InvalidAgentTypeError(ValidationError):
    """Invalid or unknown agent type"""
    pass


class InvalidStateError(ValidationError):
    """Invalid state data or transition"""
    pass


class SchemaValidationError(ValidationError):
    """Pydantic schema validation failed"""
    pass


# ============================================================================
# BUDGET EXCEPTIONS
# ============================================================================

class BudgetError(AgentSystemError):
    """Base budget-related error"""
    pass


class InsufficientBudgetError(BudgetError):
    """Not enough budget to complete operation"""
    
    def __init__(
        self,
        required: float,
        available: float,
        agent_type: Optional[str] = None,
        **kwargs
    ):
        details = {
            'required': required,
            'available': available,
            'shortfall': required - available
        }
        if agent_type:
            details['agent_type'] = agent_type
        
        message = f"Insufficient budget: required ${required:.2f}, available ${available:.2f}"
        super().__init__(message, details=details, **kwargs)


class BudgetExceededError(BudgetError):
    """Budget limit exceeded"""
    pass


class InvalidBudgetAllocationError(BudgetError):
    """Invalid budget allocation"""
    pass


# ============================================================================
# AGENT EXECUTION EXCEPTIONS
# ============================================================================

class AgentExecutionError(AgentSystemError):
    """Base agent execution error"""
    pass


class AgentNotFoundError(AgentExecutionError):
    """Requested agent not found"""
    pass


class AgentInitializationError(AgentExecutionError):
    """Agent failed to initialize"""
    pass


class AgentTimeoutError(AgentExecutionError):
    """Agent execution timed out"""
    
    def __init__(self, agent_type: str, timeout: int, **kwargs):
        details = {'agent_type': agent_type, 'timeout_seconds': timeout}
        message = f"Agent '{agent_type}' execution timed out after {timeout} seconds"
        super().__init__(message, details=details, **kwargs)


class TaskExecutionError(AgentExecutionError):
    """Task execution failed"""
    
    def __init__(self, task_id: str, reason: str, **kwargs):
        details = {'task_id': task_id, 'reason': reason}
        message = f"Task '{task_id}' execution failed: {reason}"
        super().__init__(message, details=details, **kwargs)


class DeliverableError(AgentExecutionError):
    """Failed to generate required deliverables"""
    pass


# ============================================================================
# GUARD RAIL EXCEPTIONS
# ============================================================================

class GuardRailError(AgentSystemError):
    """Base guard rail error"""
    pass


class GuardRailViolationError(GuardRailError):
    """Guard rail constraint violated"""
    
    def __init__(self, rule: str, violation: str, **kwargs):
        details = {'rule': rule, 'violation': violation}
        message = f"Guard rail violation: {rule} - {violation}"
        super().__init__(message, details=details, **kwargs)


class DomainBoundaryViolationError(GuardRailError):
    """Operation outside allowed domain"""
    pass


class VendorRecommendationError(GuardRailError):
    """Attempted to recommend external vendor"""
    
    def __init__(self, vendor_name: Optional[str] = None, **kwargs):
        details = {}
        if vendor_name:
            details['vendor_name'] = vendor_name
        message = "Vendor recommendations are not allowed - AI must execute directly"
        super().__init__(message, details=details, **kwargs)


class QualityStandardError(GuardRailError):
    """Failed to meet quality standards"""
    pass


# ============================================================================
# STATE MANAGEMENT EXCEPTIONS
# ============================================================================

class StateError(AgentSystemError):
    """Base state management error"""
    pass


class StateNotFoundError(StateError):
    """Requested state not found"""
    pass


class StateTransitionError(StateError):
    """Invalid state transition"""
    
    def __init__(self, from_state: str, to_state: str, reason: str, **kwargs):
        details = {
            'from_state': from_state,
            'to_state': to_state,
            'reason': reason
        }
        message = f"Invalid transition from '{from_state}' to '{to_state}': {reason}"
        super().__init__(message, details=details, **kwargs)


class StatePersistenceError(StateError):
    """Failed to persist state"""
    pass


# ============================================================================
# ORCHESTRATION EXCEPTIONS
# ============================================================================

class OrchestrationError(AgentSystemError):
    """Base orchestration error"""
    pass


class PhaseExecutionError(OrchestrationError):
    """Orchestration phase failed"""
    
    def __init__(self, phase: str, reason: str, **kwargs):
        details = {'phase': phase, 'reason': reason}
        message = f"Phase '{phase}' execution failed: {reason}"
        super().__init__(message, details=details, **kwargs)


class DependencyError(OrchestrationError):
    """Task dependency not satisfied"""
    
    def __init__(self, task_id: str, missing_dependencies: list, **kwargs):
        details = {
            'task_id': task_id,
            'missing_dependencies': missing_dependencies
        }
        message = f"Task '{task_id}' dependencies not met: {', '.join(missing_dependencies)}"
        super().__init__(message, details=details, **kwargs)


class ConcurrentExecutionError(OrchestrationError):
    """Error during concurrent agent execution"""
    pass


# ============================================================================
# SECURITY EXCEPTIONS
# ============================================================================

class SecurityError(AgentSystemError):
    """Base security error"""
    pass


class AuthenticationError(SecurityError):
    """Authentication failed"""
    pass


class AuthorizationError(SecurityError):
    """Authorization failed - insufficient permissions"""
    pass


class RateLimitExceededError(SecurityError):
    """Rate limit exceeded"""
    
    def __init__(self, limit: int, window: str, **kwargs):
        details = {'limit': limit, 'window': window}
        message = f"Rate limit exceeded: {limit} requests per {window}"
        super().__init__(message, details=details, **kwargs)


class InvalidTokenError(SecurityError):
    """Invalid authentication token"""
    pass


class InputSanitizationError(SecurityError):
    """Input failed sanitization checks"""
    pass


# ============================================================================
# CONFIGURATION EXCEPTIONS
# ============================================================================

class ConfigurationError(AgentSystemError):
    """Base configuration error"""
    pass


class MissingConfigurationError(ConfigurationError):
    """Required configuration missing"""
    
    def __init__(self, config_key: str, **kwargs):
        details = {'config_key': config_key}
        message = f"Missing required configuration: {config_key}"
        super().__init__(message, details=details, **kwargs)


class InvalidConfigurationError(ConfigurationError):
    """Invalid configuration value"""
    pass


# ============================================================================
# RESOURCE EXCEPTIONS
# ============================================================================

class ResourceError(AgentSystemError):
    """Base resource error"""
    pass


class ResourceNotFoundError(ResourceError):
    """Requested resource not found"""
    pass


class ResourceExhaustedError(ResourceError):
    """System resources exhausted"""
    pass


class ConnectionError(ResourceError):
    """Connection to external resource failed"""
    pass


# ============================================================================
# DATA EXCEPTIONS
# ============================================================================

class DataError(AgentSystemError):
    """Base data error"""
    pass


class DataNotFoundError(DataError):
    """Requested data not found"""
    pass


class DataCorruptionError(DataError):
    """Data is corrupted or invalid"""
    pass


class SerializationError(DataError):
    """Failed to serialize/deserialize data"""
    pass


# ============================================================================
# INTEGRATION EXCEPTIONS
# ============================================================================

class IntegrationError(AgentSystemError):
    """Base integration error"""
    pass


class APIError(IntegrationError):
    """External API error"""
    
    def __init__(
        self,
        api_name: str,
        status_code: Optional[int] = None,
        response: Optional[str] = None,
        **kwargs
    ):
        details = {'api_name': api_name}
        if status_code:
            details['status_code'] = status_code
        if response:
            details['response'] = response
        
        message = f"API error from '{api_name}'"
        if status_code:
            message += f" (status {status_code})"
        
        super().__init__(message, details=details, **kwargs)


class WebhookError(IntegrationError):
    """Webhook processing error"""
    pass


class ThirdPartyServiceError(IntegrationError):
    """Third-party service error"""
    pass


# ============================================================================
# KNOWLEDGE BASE EXCEPTIONS
# ============================================================================

class KnowledgeBaseError(AgentSystemError):
    """Base knowledge base error"""
    pass


class KnowledgeNotFoundError(KnowledgeBaseError):
    """Knowledge item not found"""
    pass


class KnowledgeIndexError(KnowledgeBaseError):
    """Knowledge index error"""
    pass


# ============================================================================
# EXCEPTION HELPERS
# ============================================================================

def handle_exception(
    exception: Exception,
    context: Optional[str] = None,
    log_func: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Handle exception and return standardized error response
    
    Args:
        exception: The exception to handle
        context: Optional context description
        log_func: Optional logging function
    
    Returns:
        Standardized error dictionary
    """
    if isinstance(exception, AgentSystemError):
        error_dict = exception.to_dict()
    else:
        error_dict = {
            'error_type': exception.__class__.__name__,
            'message': str(exception),
            'details': {}
        }
    
    if context:
        error_dict['context'] = context
    
    if log_func:
        log_func(f"Exception in {context}: {error_dict}")
    
    return error_dict


def raise_for_status(
    condition: bool,
    exception_class: type,
    message: str,
    **kwargs
):
    """
    Raise exception if condition is True
    
    Args:
        condition: If True, raise exception
        exception_class: Exception class to raise
        message: Error message
        **kwargs: Additional arguments for exception
    """
    if condition:
        raise exception_class(message, **kwargs)


# ============================================================================
# SERVICE LAYER EXCEPTIONS (NEW)
# ============================================================================

class AnalysisError(AgentSystemError):
    """CFO strategic analysis failed"""
    pass


class ExecutionError(AgentExecutionError):
    """Agent execution service error"""
    pass


class OrchestrationError(AgentSystemError):
    """Orchestration service error"""
    pass
