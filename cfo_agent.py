#!/usr/bin/env python3
"""
CFO Agent Launcher
Convenience wrapper to run the CFO agent from the root directory
"""

if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    # Run the CFO agent module directly
    import runpy

    runpy.run_module("agents.cfo_agent", run_name="__main__")
