"""
Input validation and sanitization utilities
"""

import re

# import bleach  # Commented out - install with: pip install bleach
from typing import Any, Dict, Optional, Set
from dataclasses import dataclass
from functools import wraps
from flask import request, jsonify
from pydantic import ValidationError

from .constants import AppConstants


@dataclass
class ValidationResult:
    """Simple validation result container."""

    valid: bool
    errors: list[str]


def validate_payload_allowlist(
    payload: Dict[str, Any],
    allowed_fields: Set[str],
    required_fields: Optional[Set[str]] = None,
    payload_name: str = "payload",
) -> ValidationResult:
    """Validate payload keys against an explicit allowlist and required set."""
    errors: list[str] = []

    if not isinstance(payload, dict):
        return ValidationResult(valid=False, errors=[f"{payload_name} must be a JSON object"])

    required_fields = required_fields or set()
    unknown_fields = sorted(set(payload.keys()) - allowed_fields)
    missing_fields = sorted(required_fields - set(payload.keys()))

    if unknown_fields:
        errors.append(f"Unknown {payload_name} field(s): {', '.join(unknown_fields)}")

    if missing_fields:
        errors.append(f"Missing required {payload_name} field(s): {', '.join(missing_fields)}")

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_company_info_allowlist(company_info: Dict[str, Any]) -> ValidationResult:
    """Validate nested company_info schema used by execution endpoints."""
    allowed_company_fields = {
        "company_name",
        "name",
        "dba_name",
        "industry",
        "location",
        "budget",
        "timeline",
        # Metadata fields tolerated from scenario sync
        "updated_at",
        "meta",
        "objectives",
    }

    return validate_payload_allowlist(
        company_info,
        allowed_fields=allowed_company_fields,
        required_fields={"industry", "location"},
        payload_name="company_info",
    )


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

    # Remove script tags and their entire content
    cleaned = re.sub(r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)

    # Remove dangerous patterns entirely (not just the function name)
    cleaned = re.sub(
        r"(alert|eval|prompt|confirm|document\.cookie)\s*\([^)]*\)",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Remove any remaining HTML tags
    cleaned = re.sub(r"<[^>]+>", "", cleaned)

    # Remove javascript: URLs
    cleaned = re.sub(r"javascript:", "", cleaned, flags=re.IGNORECASE)

    # Remove event handlers
    cleaned = re.sub(r"on\w+\s*=", "", cleaned, flags=re.IGNORECASE)

    # Remove excessive whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Truncate if needed
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned


def sanitize_input(value: str, max_length: Optional[int] = None) -> str:
    """Backward-compatible alias used by app-level chat handling."""
    return sanitize_string(value, max_length=max_length)


def detect_malicious_content(value: str) -> Optional[str]:
    """Return a reason string if content looks malicious or prompt-injection-like."""
    if not isinstance(value, str):
        return None

    normalized = value.lower()

    patterns = {
        r"<\s*script[^>]*>": "Embedded script tag detected",
        r"javascript\s*:": "javascript: protocol detected",
        r"on\w+\s*=": "Inline event handler detected",
        r"ignore\s+(all\s+)?previous\s+instructions": "Prompt injection phrase detected",
        (
            r"disregard\s+(all\s+)?(prior|previous)\s+instructions"
        ): "Prompt injection phrase detected",
        r"reveal\s+(the\s+)?(system|developer)\s+prompt": ("System prompt exfiltration detected"),
        r"you\s+are\s+now\s+(in\s+)?developer\s+mode": "Role override attempt detected",
        r"jailbreak": "Jailbreak instruction detected",
        r"prompt\s+injection": "Prompt injection content detected",
        r"data\s*:\s*text/html": "Potential HTML payload detected",
    }

    for pattern, reason in patterns.items():
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return reason

    return None


def scan_payload_for_threats(
    payload: Any, path: str = "root", max_findings: int = 3
) -> ValidationResult:
    """Recursively inspect payload values and return threat findings."""
    findings: list[str] = []

    def _scan(value: Any, current_path: str) -> None:
        if len(findings) >= max_findings:
            return

        if isinstance(value, str):
            reason = detect_malicious_content(value)
            if reason:
                findings.append(f"{current_path}: {reason}")
            return

        if isinstance(value, dict):
            for key, nested in value.items():
                _scan(nested, f"{current_path}.{key}")
                if len(findings) >= max_findings:
                    break
            return

        if isinstance(value, list):
            for index, nested in enumerate(value):
                _scan(nested, f"{current_path}[{index}]")
                if len(findings) >= max_findings:
                    break

    _scan(payload, path)
    return ValidationResult(valid=len(findings) == 0, errors=findings)


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
                sanitize_string(item) if isinstance(item, str) else item for item in value
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
                    return (
                        jsonify({"error": "No JSON data provided", "success": False}),
                        AppConstants.BAD_REQUEST,
                    )

                # Sanitize input
                sanitized_data = sanitize_dict(json_data)

                # Validate with Pydantic
                validated = schema_class(**sanitized_data)

                # Call original function with validated data
                return func(validated, *args, **kwargs)

            except ValidationError as e:
                return (
                    jsonify(
                        {
                            "error": "Validation failed",
                            "details": e.errors(),
                            "success": False,
                        }
                    ),
                    AppConstants.BAD_REQUEST,
                )
            except Exception as e:
                return (
                    jsonify({"error": str(e), "success": False}),
                    AppConstants.SERVER_ERROR,
                )

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
        return False, f"Budget must be at least ${AppConstants.MIN_BUDGET}"
    if budget > AppConstants.MAX_BUDGET:
        return False, f"Budget cannot exceed ${AppConstants.MAX_BUDGET}"
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
        return False, f"Timeline must be at least {AppConstants.MIN_TIMELINE_DAYS} days"
    if days > AppConstants.MAX_TIMELINE_DAYS:
        return False, f"Timeline cannot exceed {AppConstants.MAX_TIMELINE_DAYS} days"
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
        return False, "Company name is required"
    if len(name) > AppConstants.COMPANY_NAME_MAX_LENGTH:
        return (
            False,
            f"Company name cannot exceed {AppConstants.COMPANY_NAME_MAX_LENGTH} characters",
        )
    return True, None


def validate_company_info(company_info: Dict[str, Any]) -> ValidationResult:
    """Validate core company fields used across API endpoints."""
    errors: list[str] = []

    name_valid, name_error = validate_company_name(
        company_info.get("name") or company_info.get("company_name", "")
    )
    if not name_valid and name_error:
        errors.append(name_error)

    industry = str(company_info.get("industry", "")).strip()
    if len(industry) < AppConstants.INDUSTRY_MIN_LENGTH:
        errors.append("Industry is required")
    elif len(industry) > AppConstants.INDUSTRY_MAX_LENGTH:
        errors.append(f"Industry cannot exceed {AppConstants.INDUSTRY_MAX_LENGTH} characters")

    location = str(company_info.get("location", "")).strip()
    if len(location) < AppConstants.LOCATION_MIN_LENGTH:
        errors.append("Location is required")
    elif len(location) > AppConstants.LOCATION_MAX_LENGTH:
        errors.append(f"Location cannot exceed {AppConstants.LOCATION_MAX_LENGTH} characters")

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_agent_request(payload: Dict[str, Any]) -> ValidationResult:
    """Validate high-level agent execution request payload."""
    errors: list[str] = []

    company_info = payload.get("company_info") or {
        "company_name": payload.get("company_name", ""),
        "industry": payload.get("industry", ""),
        "location": payload.get("location", ""),
    }
    company_validation = validate_company_info(company_info)
    if not company_validation.valid:
        errors.extend(company_validation.errors)

    budget = payload.get("total_budget")
    if budget is not None:
        try:
            budget_value = float(budget)
            is_budget_valid, budget_error = validate_budget(budget_value)
            if not is_budget_valid and budget_error:
                errors.append(budget_error)
        except (TypeError, ValueError):
            errors.append("Budget must be a number")

    timeline = payload.get("target_days")
    if timeline is not None:
        try:
            timeline_value = int(timeline)
            is_timeline_valid, timeline_error = validate_timeline(timeline_value)
            if not is_timeline_valid and timeline_error:
                errors.append(timeline_error)
        except (TypeError, ValueError):
            errors.append("Timeline must be an integer number of days")

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_chat_message(data: Dict[str, Any]) -> ValidationResult:
    """Validate websocket chat payloads."""
    errors: list[str] = []

    message = str(data.get("message", "")).strip()
    if not message:
        errors.append("Message is required")
    elif len(message) > 5000:
        errors.append("Message cannot exceed 5000 characters")

    sender = str(data.get("sender", "user")).strip().lower()
    if sender not in {"user", "assistant", "system"}:
        errors.append("Sender must be one of: user, assistant, system")

    threat_scan = scan_payload_for_threats({"message": message, "sender": sender}, path="chat")
    if not threat_scan.valid:
        errors.extend(threat_scan.errors)

    return ValidationResult(valid=len(errors) == 0, errors=errors)
