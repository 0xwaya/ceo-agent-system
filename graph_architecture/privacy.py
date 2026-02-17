"""
Privacy Guard — PII Scrubbing Layer

Sits at the graph entry point (before Prompt Expert) and redacts personally
identifiable information from user input before it reaches any LLM node.

Supported detections
────────────────────
  EMAIL          user@domain.com
  PHONE_US       (555) 867-5309 / 555-867-5309 / +1 5558675309
  SSN            123-45-6789
  CREDIT_CARD    4111 1111 1111 1111  (Visa/MC/Amex pattern)
  IP_ADDRESS     192.168.1.100
  DATE_OF_BIRTH  01/15/1990  or  January 15 1990
  STREET_ADDRESS 123 Main St, Cincinnati OH  (heuristic)
  FULL_NAME      "John Smith" style pattern  (heuristic, opt-in via env flag)

Each detection replaces the matched text with a typed placeholder:
  [EMAIL_REDACTED], [PHONE_REDACTED], [SSN_REDACTED] …

Design rules
────────────
  • Scrubbing is ALWAYS applied before user text reaches any LLM.
  • Original text is NEVER stored on SharedState after scrubbing.
  • Detections list tells downstream nodes WHAT types were found, not the values.
  • Scrubbing can be disabled per-env via PRIVACY_PII_SCRUBBING=false (dev only).
  • In production scrubbing is always on regardless of the env flag.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

_SCRUBBING_ENABLED_ENV = os.getenv("PRIVACY_PII_SCRUBBING", "true").lower() != "false"
_REDACTION_TOKEN = os.getenv("PRIVACY_REDACTION_TOKEN", "[REDACTED]")

# Production always scrubs regardless of env flag
_APP_ENV = os.getenv("APP_ENV", "development").lower()
_FORCE_SCRUBBING = _APP_ENV == "production"


# ─────────────────────────────────────────────────────────────────────────────
# PII PATTERNS
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _Pattern:
    label: str  # Detection category name
    regex: re.Pattern  # Compiled pattern
    placeholder: str  # Token inserted in place of matched value


_PII_PATTERNS: List[_Pattern] = [
    # Email addresses
    _Pattern(
        label="EMAIL",
        regex=re.compile(
            r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
            re.IGNORECASE,
        ),
        placeholder="[EMAIL_REDACTED]",
    ),
    # US Social Security Numbers
    _Pattern(
        label="SSN",
        regex=re.compile(r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b"),
        placeholder="[SSN_REDACTED]",
    ),
    # Credit/debit card numbers (13–16 digits, optional separators)
    _Pattern(
        label="CREDIT_CARD",
        regex=re.compile(r"\b(?:\d[ -]?){13,16}\b"),
        placeholder="[CARD_REDACTED]",
    ),
    # US phone numbers — various formats
    _Pattern(
        label="PHONE_US",
        regex=re.compile(r"\b(?:\+1[\s.\-]?)?(?:\(?\d{3}\)?[\s.\-]?)?\d{3}[\s.\-]?\d{4}\b"),
        placeholder="[PHONE_REDACTED]",
    ),
    # IPv4 addresses
    _Pattern(
        label="IP_ADDRESS",
        regex=re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}" r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
        ),
        placeholder="[IP_REDACTED]",
    ),
    # Dates of birth — MM/DD/YYYY or Month DD YYYY
    _Pattern(
        label="DATE_OF_BIRTH",
        regex=re.compile(
            r"\b(?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])[-/](?:19|20)\d{2}\b"
            r"|"
            r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
            r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?"
            r"|Dec(?:ember)?)\s+(?:0?[1-9]|[12]\d|3[01]),?\s+(?:19|20)\d{2}\b",
            re.IGNORECASE,
        ),
        placeholder="[DOB_REDACTED]",
    ),
    # Street addresses — heuristic: number + street keyword
    _Pattern(
        label="STREET_ADDRESS",
        regex=re.compile(
            r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s+){1,3}"
            r"(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Lane|Ln|Drive|Dr"
            r"|Court|Ct|Circle|Cir|Way|Place|Pl|Terrace|Ter|Highway|Hwy)\b",
            re.IGNORECASE,
        ),
        placeholder="[ADDRESS_REDACTED]",
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# CORE SCRUBBING FUNCTION
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ScrubResult:
    """Result from a single scrub operation."""

    original_length: int  # Length of original text
    scrubbed_text: str  # Text with PII replaced
    detections: List[str] = field(default_factory=list)  # Labels of detected PII types
    redaction_count: int = 0  # Total number of replacements made
    scrubbing_applied: bool = True  # Whether scrubbing ran (False if disabled)


def scrub_pii(text: str) -> ScrubResult:
    """
    Scan *text* for PII and return a ScrubResult containing the cleaned text.

    The original text is NOT retained in the result — only the scrubbed
    version and metadata about what was found.

    Args:
        text: Raw user input string

    Returns:
        ScrubResult with scrubbed_text, detections list, redaction_count
    """
    if not text:
        return ScrubResult(
            original_length=0,
            scrubbed_text=text,
            scrubbing_applied=False,
        )

    scrubbing_on = _FORCE_SCRUBBING or _SCRUBBING_ENABLED_ENV

    if not scrubbing_on:
        logger.debug("PII scrubbing disabled via PRIVACY_PII_SCRUBBING env flag")
        return ScrubResult(
            original_length=len(text),
            scrubbed_text=text,
            scrubbing_applied=False,
        )

    scrubbed = text
    detections: List[str] = []
    total_replacements = 0

    for pattern in _PII_PATTERNS:
        matches = pattern.regex.findall(scrubbed)
        if matches:
            count = len(matches)
            scrubbed = pattern.regex.sub(pattern.placeholder, scrubbed)
            total_replacements += count
            if pattern.label not in detections:
                detections.append(pattern.label)
            logger.info(
                "PII scrubber: redacted %d %s occurrence(s) from user input",
                count,
                pattern.label,
            )

    if total_replacements:
        logger.warning(
            "PII scrubber: %d total redaction(s) applied (%s) — " "original text dropped",
            total_replacements,
            ", ".join(detections),
        )

    return ScrubResult(
        original_length=len(text),
        scrubbed_text=scrubbed,
        detections=detections,
        redaction_count=total_replacements,
        scrubbing_applied=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# LANGGRAPH NODE
# ─────────────────────────────────────────────────────────────────────────────


def privacy_scrub_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node — scrubs PII from user_raw_input before any LLM sees it.

    Reads:   state["user_raw_input"]
    Writes:
        state["user_raw_input"]    — replaced with scrubbed version
        state["privacy_scrubbed"]  — True if scrubbing ran
        state["pii_detections"]    — list of detected PII category labels

    This node is the FIRST node in the graph (after START), before
    prompt_expert_node, so no raw PII ever reaches an LLM.
    """
    raw = state.get("user_raw_input", "")
    result = scrub_pii(raw)

    updates: Dict[str, Any] = {
        "user_raw_input": result.scrubbed_text,
        "privacy_scrubbed": result.scrubbing_applied,
        "pii_detections": result.detections,
    }

    if result.detections:
        # Surface a guard-rail violation record so the audit trail captures it
        updates["guard_rail_violations"] = [
            {
                "node": "privacy_scrub_node",
                "violation_type": "pii_detected_and_redacted",
                "pii_types": result.detections,
                "redaction_count": result.redaction_count,
                "timestamp": _now_iso(),
                "message": (
                    f"Detected and redacted {result.redaction_count} PII "
                    f"value(s): {', '.join(result.detections)}"
                ),
            }
        ]

    return updates


# ─────────────────────────────────────────────────────────────────────────────
# UTILITY
# ─────────────────────────────────────────────────────────────────────────────


def _now_iso() -> str:
    from datetime import datetime

    return datetime.now().isoformat()


def is_scrubbing_active() -> bool:
    """Return True if PII scrubbing is currently enabled."""
    return _FORCE_SCRUBBING or _SCRUBBING_ENABLED_ENV
