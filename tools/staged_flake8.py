#!/usr/bin/env python3
"""Run flake8 on a staged file group to support incremental cleanup.

The active stage and file groups are configured in tools/flake8_stages.json.
This lets pre-commit stay green while lint debt is retired in controlled batches.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name("flake8_stages.json")
REPO_ROOT = Path(__file__).resolve().parent.parent


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def resolve_stage_files(stage_paths: list[str]) -> set[Path]:
    resolved: set[Path] = set()
    for pattern in stage_paths:
        for matched in REPO_ROOT.glob(pattern):
            if matched.is_file() and matched.suffix == ".py":
                resolved.add(matched.resolve())
    return resolved


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def main(argv: list[str]) -> int:
    config = load_config()
    active = config["active_stage"]
    stage = config["stages"].get(active)

    if not stage:
        print(f"❌ Active stage '{active}' not found in {CONFIG_PATH}")
        return 1

    stage_files = resolve_stage_files(stage.get("paths", []))
    if not stage_files:
        print(f"ℹ️ No Python files resolved for stage '{active}'")
        return 0

    passed_files = {
        Path(arg).resolve() for arg in argv if arg.endswith(".py") and Path(arg).exists()
    }
    targets = (
        sorted(stage_files.intersection(passed_files)) if passed_files else sorted(stage_files)
    )

    if not targets:
        print(f"ℹ️ No staged files in current commit for stage '{active}'")
        return 0

    cmd = [sys.executable, "-m", "flake8", "--max-line-length=100", *[str(p) for p in targets]]

    print(f"\n🔎 Running staged flake8: {active}")
    print(f"   Description: {stage.get('description', '')}")
    for target in targets:
        print(f"   - {rel(target)}")

    completed = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
