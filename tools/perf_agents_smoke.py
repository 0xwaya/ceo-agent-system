#!/usr/bin/env python3
"""Lightweight agent availability and performance smoke test."""

from __future__ import annotations

import os
import sys
import time
from statistics import mean
from pathlib import Path

# Keep smoke test offline/fast regardless of external API key status.
os.environ.setdefault("OPENAI_CODEX_ENABLED", "false")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.agent_service import AgentExecutionService


SAMPLE_COMPANY_INFO = {
    "name": "SurfaceCraft Studio",
    "dba_name": "SurfaceCraft Studio",
    "industry": "Custom Countertops",
    "location": "Cincinnati, Ohio",
}

TASK_BY_AGENT = {
    "branding": "Produce polished branding direction and logo options",
    "web_development": "Draft modern homepage architecture and UX system",
    "legal": "Prepare basic compliance filing checklist",
    "martech": "Configure practical SMB marketing technology stack",
    "content": "Generate initial content production plan",
    "campaigns": "Set up Google Ads campaigns and implement A/B testing",
    "social_media": "Configure social channel operations and engagement workflows",
    "security": "Run security posture review and next actions",
}


def run_smoke() -> int:
    service = AgentExecutionService()
    available_agents = service.get_available_agents()
    available_types = [agent["type"] for agent in available_agents]

    print("Agent availability")
    print("==================")
    for agent_type in available_types:
        print(f"- {agent_type}")

    missing = [agent for agent in TASK_BY_AGENT if agent not in available_types]
    if missing:
        print(f"\nFAIL: Missing expected agents: {', '.join(missing)}")
        return 1

    timings = []
    failures = []

    print("\nExecution latency (seconds)")
    print("===========================")
    for agent_type in TASK_BY_AGENT:
        start = time.perf_counter()
        try:
            response = service.execute_agent(
                agent_type=agent_type,
                task_description=TASK_BY_AGENT[agent_type],
                company_info=SAMPLE_COMPANY_INFO,
                requirements={},
            )
            elapsed = time.perf_counter() - start
            timings.append(elapsed)
            status = "PASS" if response.get("success") else "FAIL"
            print(f"- {agent_type:15} {elapsed:7.3f}s {status}")
            if status == "FAIL":
                failures.append(agent_type)
        except Exception as error:
            elapsed = time.perf_counter() - start
            timings.append(elapsed)
            failures.append(agent_type)
            print(f"- {agent_type:15} {elapsed:7.3f}s FAIL ({error})")

    print("\nSummary")
    print("=======")
    print(f"agents_tested={len(TASK_BY_AGENT)}")
    print(f"avg_latency={mean(timings):.3f}s")
    print(f"p95_estimate={sorted(timings)[max(0, int(len(timings) * 0.95) - 1)]:.3f}s")

    if failures:
        print(f"failed_agents={','.join(failures)}")
        return 1

    print("result=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_smoke())
