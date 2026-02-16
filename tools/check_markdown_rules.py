#!/usr/bin/env python3
"""Lightweight markdown rules checker for pre-commit.

Rules enforced (aligned with recurring markdownlint issues):
- No trailing punctuation in ATX headings (MD026-like)
- Heading levels must not jump by more than one (MD001-like)
- No duplicate headings within a file (MD024-like)
- No strong emphasis with double underscores (MD050-like)
- No trailing whitespace except two spaces for hard break (MD009-like)
- Blank lines around markdown tables (MD058-like)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CHECK_EXTENSIONS = {".md", ".markdown"}
IGNORED_DIR_NAMES = {".git", ".venv", "venv", "node_modules", "__pycache__"}

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
STRONG_UNDERSCORE_RE = re.compile(r"__[^_].*?__")
TABLE_LINE_RE = re.compile(r"^\s*\|.*\|\s*$")
SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")


def should_check(path: Path) -> bool:
    if any(part in IGNORED_DIR_NAMES for part in path.parts):
        return False
    return path.suffix.lower() in CHECK_EXTENSIONS


def normalize_heading(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def strip_inline_code(line: str) -> str:
    return re.sub(r"`[^`]*`", "", line)


def is_code_fence(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("```") or stripped.startswith("~~~")


def is_heading_trailing_punctuation(text: str) -> bool:
    cleaned = text.strip().rstrip("#").strip()
    return bool(cleaned) and cleaned[-1] in ".,;:!?"


def looks_like_table(lines: list[str], idx: int) -> bool:
    if idx + 1 >= len(lines):
        return False
    return bool(TABLE_LINE_RE.match(lines[idx]) and SEPARATOR_RE.match(lines[idx + 1]))


def check_file(file_path: Path) -> list[tuple[int, str]]:
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return []

    violations: list[tuple[int, str]] = []
    in_fence = False
    last_heading_level = 0
    headings_seen: dict[str, int] = {}

    for i, line in enumerate(lines, start=1):
        if is_code_fence(line):
            in_fence = not in_fence
            continue

        if in_fence:
            continue

        if line.endswith(" ") and not line.endswith("  "):
            violations.append((i, "MD009-style: Trailing whitespace"))

        if STRONG_UNDERSCORE_RE.search(strip_inline_code(line)):
            violations.append(
                (i, "MD050-style: Use **asterisk** strong style, not __underscores__")
            )

        heading_match = HEADING_RE.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)

            if last_heading_level and level > last_heading_level + 1:
                violations.append(
                    (i, f"MD001-style: Heading jumped from h{last_heading_level} to h{level}")
                )

            if is_heading_trailing_punctuation(text):
                violations.append((i, "MD026-style: Heading has trailing punctuation"))

            normalized = normalize_heading(re.sub(r"\*", "", text))
            if normalized in headings_seen:
                first = headings_seen[normalized]
                violations.append(
                    (i, f"MD024-style: Duplicate heading (first seen on line {first})")
                )
            else:
                headings_seen[normalized] = i

            last_heading_level = level

    for idx in range(len(lines)):
        if looks_like_table(lines, idx):
            before_ok = idx == 0 or lines[idx - 1].strip() == ""
            block_end = idx + 1
            while block_end + 1 < len(lines) and TABLE_LINE_RE.match(lines[block_end + 1]):
                block_end += 1
            after_ok = block_end + 1 >= len(lines) or lines[block_end + 1].strip() == ""

            if not before_ok:
                violations.append((idx + 1, "MD058-style: Missing blank line before table"))
            if not after_ok:
                violations.append((block_end + 1, "MD058-style: Missing blank line after table"))

    return violations


def main(argv: list[str]) -> int:
    files = [Path(item) for item in argv if Path(item).exists() and should_check(Path(item))]
    all_violations: list[tuple[str, int, str]] = []

    for file_path in files:
        for line_number, message in check_file(file_path):
            all_violations.append((str(file_path), line_number, message))

    if all_violations:
        print("\n❌ Markdown rule violations found:\n")
        for file_path, line_number, message in all_violations:
            print(f"- {file_path}:{line_number}: {message}")
        print("\nFix these markdown issues before committing.\n")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
