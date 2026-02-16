#!/usr/bin/env python3
"""Block staged commits that include likely secrets or sensitive key files."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent

ALLOWED_PATHS = {
    ".env.encrypted",
}

BLOCKED_EXACT_FILENAMES = {
    ".env",
    ".env.local",
    ".env.key",
    "id_rsa",
    "id_ecdsa",
    "id_ed25519",
}

BLOCKED_FILE_SUFFIXES = (
    ".pem",
    ".p12",
    ".pfx",
    ".jks",
    ".kdbx",
)

BLOCKED_PATH_SEGMENTS = (
    "/secrets/",
    "/credentials/",
)

IGNORED_SCAN_SUFFIXES = (
    ".md",
    ".markdown",
)

SECRET_LINE_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ASIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-./+=]{16,}"),
]


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout


def get_staged_files() -> list[str]:
    output = run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    return [line.strip() for line in output.splitlines() if line.strip()]


def is_allowed(path: str) -> bool:
    return path in ALLOWED_PATHS


def has_blocked_path(path: str) -> bool:
    normalized = f"/{path}"
    name = Path(path).name

    if name in BLOCKED_EXACT_FILENAMES:
        return True
    if any(path.endswith(suffix) for suffix in BLOCKED_FILE_SUFFIXES):
        return True
    if any(segment in normalized for segment in BLOCKED_PATH_SEGMENTS):
        return True
    return False


def get_added_lines(path: str) -> list[str]:
    output = run_git(["diff", "--cached", "--unified=0", "--", path])
    added = []
    for line in output.splitlines():
        if line.startswith("+++"):
            continue
        if line.startswith("+"):
            added.append(line[1:])
    return added


def scan_staged_files(paths: list[str]) -> list[str]:
    failures: list[str] = []

    for path in paths:
        if is_allowed(path):
            continue

        if path.lower().endswith(IGNORED_SCAN_SUFFIXES):
            continue

        if has_blocked_path(path):
            failures.append(f"Blocked sensitive file path: {path}")
            continue

        file_path = REPO_ROOT / path
        if not file_path.exists() or file_path.is_dir():
            continue

        try:
            added_lines = get_added_lines(path)
        except subprocess.CalledProcessError:
            continue

        for idx, line in enumerate(added_lines, start=1):
            for pattern in SECRET_LINE_PATTERNS:
                if pattern.search(line):
                    failures.append(f"Possible secret in {path} (added line {idx}): {line[:120]}")
                    break

    return failures


def main() -> int:
    try:
        staged_files = get_staged_files()
    except subprocess.CalledProcessError as error:
        print("Unable to inspect staged files.", file=sys.stderr)
        if error.stderr:
            print(error.stderr.strip(), file=sys.stderr)
        return 2

    if not staged_files:
        print("No staged files found; secret scan skipped.")
        return 0

    failures = scan_staged_files(staged_files)

    if failures:
        print("\nCommit blocked by staged secret scan:\n")
        for failure in failures:
            print(f"- {failure}")
        print("\nIf this is intentional, move secrets to runtime env or encrypted storage.")
        return 1

    print("Staged secret scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
