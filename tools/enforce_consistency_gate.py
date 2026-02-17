#!/usr/bin/env python3
"""Enforce documentation/workflow consistency for major code changes.

Rule:
- If major runtime code changes are detected, at least one documentation file
  and at least one workflow file must also be updated in the same change set.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable


WORKFLOW_PREFIX = ".github/workflows/"

MAJOR_CODE_PATHS = (
    "app.py",
    "config.py",
    "models.py",
    "voice_endpoints.py",
    "agent.py",
    "ceo_agent.py",
    "cfo_agent.py",
    "agents/",
    "services/",
    "graph_architecture/",
    "static/js/",
    "templates/",
)

DOC_PATHS = (
    "README.md",
    "docs/CONTRIBUTING.md",
    "docs/SECURITY.md",
    "docs/",
)


def _run(command: list[str], check: bool = True) -> str:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({' '.join(command)}):\n{result.stdout}\n{result.stderr}"
        )
    return result.stdout.strip()


def _is_ci() -> bool:
    return os.getenv("GITHUB_ACTIONS", "false").lower() == "true"


def _git_changed_files_ci() -> list[str]:
    event_name = os.getenv("GITHUB_EVENT_NAME", "")

    if event_name == "pull_request":
        base_ref = os.getenv("GITHUB_BASE_REF", "main")
        _run(["git", "fetch", "origin", base_ref, "--depth", "1"], check=False)
        diff_range = f"origin/{base_ref}...HEAD"
        output = _run(["git", "diff", "--name-only", diff_range])
        return [line.strip() for line in output.splitlines() if line.strip()]

    if event_name == "push":
        before = os.getenv("GITHUB_EVENT_BEFORE", "")
        sha = os.getenv("GITHUB_SHA", "HEAD")

        if before and set(before) != {"0"}:
            output = _run(["git", "diff", "--name-only", f"{before}...{sha}"])
            return [line.strip() for line in output.splitlines() if line.strip()]

        output = _run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], check=False
        )
        return [line.strip() for line in output.splitlines() if line.strip()]

    output = _run(["git", "diff", "--name-only", "HEAD~1...HEAD"], check=False)
    return [line.strip() for line in output.splitlines() if line.strip()]


def _git_changed_files_local() -> list[str]:
    output = _run(["git", "status", "--porcelain"], check=False)
    files: list[str] = []
    for line in output.splitlines():
        if not line:
            continue
        raw = line[3:]
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        path = raw.strip()
        if path:
            files.append(path)
    return sorted(set(_expand_directory_entries(files)))


def _expand_directory_entries(paths: list[str]) -> list[str]:
    expanded: list[str] = []
    root = Path.cwd()

    for path in paths:
        normalized = path.rstrip("/")
        full_path = root / normalized

        if full_path.is_dir():
            for child in full_path.rglob("*"):
                if child.is_file():
                    expanded.append(str(child.relative_to(root)).replace("\\", "/"))
            continue

        expanded.append(normalized)

    return expanded


def _matches_prefix(path: str, prefixes: Iterable[str]) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in prefixes)


def _is_doc_file(path: str) -> bool:
    return path.endswith(".md") or _matches_prefix(path, DOC_PATHS)


def _is_workflow_file(path: str) -> bool:
    return path.startswith(WORKFLOW_PREFIX) and path.endswith((".yml", ".yaml"))


def _is_major_code(path: str) -> bool:
    normalized = path.replace("\\", "/")

    if normalized.endswith(".md"):
        return False
    if normalized.endswith(".pyc") or "/__pycache__/" in normalized:
        return False

    return _matches_prefix(normalized, MAJOR_CODE_PATHS)


def main() -> int:
    changed_files = _git_changed_files_ci() if _is_ci() else _git_changed_files_local()

    if not changed_files:
        print("No changed files detected; consistency gate passed.")
        return 0

    major_changed = sorted([p for p in changed_files if _is_major_code(p)])
    docs_changed = sorted([p for p in changed_files if _is_doc_file(p)])
    workflows_changed = sorted([p for p in changed_files if _is_workflow_file(p)])

    print("Changed files analyzed:")
    for path in changed_files:
        print(f"- {path}")

    if not major_changed:
        print("\nNo major runtime code changes detected; consistency gate passed.")
        return 0

    print("\nMajor code changes detected:")
    for path in major_changed:
        print(f"- {path}")

    missing_parts: list[str] = []
    if not docs_changed:
        missing_parts.append("documentation updates (*.md)")
    if not workflows_changed:
        missing_parts.append("workflow updates (.github/workflows/*.yml)")

    if missing_parts:
        print("\n❌ Consistency gate failed.")
        print("Major code changes require both docs and workflow updates in the same change set.")
        print("Missing: " + ", ".join(missing_parts))
        print("\nAdd/update relevant docs and workflow files, then rerun checks.")
        return 1

    print("\n✅ Consistency gate passed (major code + docs + workflow updates present).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
