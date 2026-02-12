"""
Input validation and sanitization utilities
"""

import re
# import bleach  # Commented out - install with: pip install bleach
from typing import Any, Dict, Optional
from functools import wraps
from flask import request, jsonify
from pydantic import ValidationError

from .constants import AppConstants


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input to prevent XSS and injection attacks
    
    Args:
        value: Input string
        max_length: Optional maximum length
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)
    
    # Simple sanitization without bleach
    # Remove dangerous HTML-like patterns
    cleaned = re.sub(r'<[^>]+>', '', value)
    cleaned = re.sub(r'javascript:', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'on\w+\s*=', '', cleaned, flags=re.IGNORECASE)
    
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Truncate if needed
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitize dictionary values
    
    Args:
        data: Input dictionary
        
    Returns:
        Sanitized dictionary
    """
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_string(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized


def validate_request_data(schema_class):
    """
    Decorator to validate request data with Pydantic schema
    
    Usage:
        @app.route('/api/endpoint', methods=['POST'])
        @validate_request_data(MyRequestSchema)
        def my_endpoint(validated_data):
            # validated_data is a Pydantic model instance
            return jsonify({'success': True})
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Get JSON data
                json_data = request.get_json()
                if json_data is None:
                    return jsonify({
                        'error': 'No JSON data provided',
                        'success': False
                    }), AppConstants.BAD_REQUEST
                
                # Sanitize input
                sanitized_data = sanitize_dict(json_data)
                
                # Validate with Pydantic
                validated = schema_class(**sanitized_data)
                
                # Call original function with validated data
                return func(validated, *args, **kwargs)
                
            except ValidationError as e:
                return jsonify({
                    'error': 'Validation failed',
                    'details': e.errors(),
                    'success': False
                }), AppConstants.BAD_REQUEST
            except Exception as e:
                return jsonify({
                    'error': str(e),
                    'success': False
                }), AppConstants.SERVER_ERROR
        
        return wrapper
    return decorator


def validate_agent_type(agent_type: str) -> bool:
    """
    Validate agent type
    
    Args:
        agent_type: Agent type string
        
    Returns:
        True if valid, False otherwise
    """
    return AppConstants.is_valid_agent_type(agent_type)


def validate_budget(budget: float) -> tuple[bool, Optional[str]]:
    """
    Validate budget value
    
    Args:
        budget: Budget amount
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if budget < AppConstants.MIN_BUDGET:
        return False, f'Budget must be at least ${AppConstants.MIN_BUDGET}'
    if budget > AppConstants.MAX_BUDGET:
        return False, f'Budget cannot exceed ${AppConstants.MAX_BUDGET}'
    return True, None


def validate_timeline(days: int) -> tuple[bool, Optional[str]]:
    """
    Validate timeline value
    
    Args:
        days: Timeline in days
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if days < AppConstants.MIN_TIMELINE_DAYS:
        return False, f'Timeline must be at least {AppConstants.MIN_TIMELINE_DAYS} days'
    if days > AppConstants.MAX_TIMELINE_DAYS:
        return False, f'Timeline cannot exceed {AppConstants.MAX_TIMELINE_DAYS} days'
    return True, None


def validate_company_name(name: str) -> tuple[bool, Optional[str]]:
    """
    Validate company name
    
    Args:
        name: Company name
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or len(name.strip()) < AppConstants.COMPANY_NAME_MIN_LENGTH:
        return False, 'Company name is required'
    if len(name) > AppConstants.COMPANY_NAME_MAX_LENGTH:
        return False, f'Company name cannot exceed {AppConstants.COMPANY_NAME_MAX_LENGTH} characters'
    return True, None
