"""OpenAI Codex tooling helper for specialized agents.

This module provides a lightweight wrapper around OpenAI API calls so agents
can optionally request implementation assistance when OPENAI credentials are
configured.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency guard
    OpenAI = None


logger = logging.getLogger(__name__)
SENSITIVE_KEYWORDS = ("key", "token", "secret", "password", "credential")


class OpenAICodexTooling:
    """Optional OpenAI Codex helper for agent execution workflows."""

    def __init__(
        self,
        api_key: Optional[str],
        model: str,
        enabled: bool,
        timeout_seconds: int,
        agent_name: str,
    ):
        self.api_key = api_key
        self.model = model
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds
        self.agent_name = agent_name
        self.client = None

        if self.enabled:
            self._initialize_client()

    @classmethod
    def from_env(cls, agent_name: str) -> "OpenAICodexTooling":
        return cls(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_CODEX_MODEL", "gpt-5-codex"),
            enabled=os.getenv("OPENAI_CODEX_ENABLED", "false").lower() == "true",
            timeout_seconds=int(os.getenv("OPENAI_CODEX_TIMEOUT_SECONDS", "45")),
            agent_name=agent_name,
        )

    def is_available(self) -> bool:
        return bool(self.enabled and self.client)

    def _initialize_client(self) -> None:
        """Initialize OpenAI client when enabled or force-enabled."""
        if self.client is not None:
            return

        if not self.api_key:
            logger.info("OpenAI Codex tooling unavailable: OPENAI_API_KEY not set")
            return

        if OpenAI is None:
            logger.warning("OpenAI package unavailable; Codex tooling disabled")
            return

        try:
            self.client = OpenAI(api_key=self.api_key, timeout=self.timeout_seconds)
        except Exception as error:  # pragma: no cover - network/client initialization
            logger.warning(f"OpenAI Codex client initialization failed: {error}")

    def _sanitize_context(self, context: Any) -> Any:
        """Redact sensitive values and bound payload size before external calls."""
        if isinstance(context, dict):
            sanitized: Dict[str, Any] = {}
            for key, value in context.items():
                if any(word in str(key).lower() for word in SENSITIVE_KEYWORDS):
                    sanitized[str(key)] = "[REDACTED]"
                else:
                    sanitized[str(key)] = self._sanitize_context(value)
            return sanitized

        if isinstance(context, list):
            return [self._sanitize_context(item) for item in context[:25]]

        if isinstance(context, str):
            return context[:1500]

        return context

    def generate_assist(
        self, objective: str, context: Dict[str, Any], force_enable: bool = False
    ) -> Dict[str, Any]:
        """Generate optional Codex-assisted guidance for an agent task."""
        if force_enable and not self.client:
            self._initialize_client()

        if not self.client or (not self.enabled and not force_enable):
            return {
                "enabled": self.enabled,
                "force_enabled": force_enable,
                "used": False,
                "model": self.model,
                "output": None,
                "reason": "OpenAI Codex tooling unavailable",
            }

        system_prompt = (
            "You are OpenAI Codex assisting a production AI agent. "
            "Return concise, actionable implementation guidance as bullet points. "
            "Do not include secrets or credentials."
        )

        user_payload = {
            "agent": self.agent_name,
            "objective": objective,
            "context": self._sanitize_context(context),
            "format": "Return 5-8 concise bullets plus one risk note.",
        }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
                ],
            )
            content = response.choices[0].message.content if response.choices else None

            return {
                "enabled": bool(self.enabled or force_enable),
                "force_enabled": force_enable,
                "used": bool(content),
                "model": self.model,
                "output": content,
            }
        except Exception as error:  # pragma: no cover - external API call
            logger.warning(f"OpenAI Codex tooling call failed: {error}")
            return {
                "enabled": bool(self.enabled or force_enable),
                "force_enabled": force_enable,
                "used": False,
                "model": self.model,
                "output": None,
                "error": str(error),
            }
