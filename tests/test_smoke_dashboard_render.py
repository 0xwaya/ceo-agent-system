"""Pytest wrapper for dashboard rendering smoke checks."""

from pathlib import Path
import subprocess
import sys


def test_dashboard_render_smoke_script_runs() -> None:
    root = Path(__file__).resolve().parents[1]
    script_path = root / "tools" / "smoke_dashboard_render.py"

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "Smoke render script failed.\n" f"stdout:\n{result.stdout}\n" f"stderr:\n{result.stderr}"
    )
