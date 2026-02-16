#!/usr/bin/env python3
"""
CEO Agent Launcher
Runs the upgraded CEO agent (executive orchestrator)
"""

if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    # Run the CEO agent module directly
    import runpy

    runpy.run_module("agents.ceo_agent", run_name="__main__")
