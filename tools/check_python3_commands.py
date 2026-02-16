#!/usr/bin/env python3
"""Fail when command lines use `python` instead of `python3`."""

from __future__ import annotations

import re
import sys
from pathlib import Path

COMMAND_PATTERNS = [
    re.compile(r"^\s*(?:\$\s*)?python\s+"),
    re.compile(r"^\s*[-*]\s+python\s+"),
    re.compile(r"`python\s+[^`]*`"),
    re.compile(r"\bpython\s+-m\s+"),
]
IGNORED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".pdf"}
CHECK_EXTENSIONS = {".md", ".sh", ".yml", ".yaml", ".txt", ".mk"}
CHECK_FILENAMES = {"Makefile"}
IGNORED_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
}


def should_check(path: Path) -> bool:
    if any(part in IGNORED_DIR_NAMES for part in path.parts):
        return False
    if path.suffix.lower() in IGNORED_EXTENSIONS:
        return False
    if path.name in CHECK_FILENAMES:
        return True
    return path.suffix.lower() in CHECK_EXTENSIONS


def main(argv: list[str]) -> int:
    files = [Path(item) for item in argv if Path(item).exists() and should_check(Path(item))]

    violations: list[tuple[str, int, str]] = []

    for file_path in files:
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue

        for line_number, line in enumerate(lines, start=1):
            if any(pattern.search(line) for pattern in COMMAND_PATTERNS):
                violations.append((str(file_path), line_number, line.strip()))

    if violations:
        print("\n❌ Found `python` command usage. Use `python3` for consistency:\n")
        for file_path, line_number, line in violations:
            print(f"- {file_path}:{line_number}: {line}")
        print("\nFix these lines to use `python3` before committing.\n")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
