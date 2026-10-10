#!/usr/bin/env python3
"""
Quick test to verify encrypted environment setup
Run this to ensure dependencies are installed
"""

import sys
import importlib


def check_dependencies():
    """Check if all required dependencies are installed"""
    missing = []

    # Check core dependencies
    try:
        importlib.import_module("flask")

        print("✓ Flask installed")
    except ImportError:
        missing.append("flask")

    try:
        importlib.import_module("pydantic")

        print("✓ Pydantic installed")
    except ImportError:
        missing.append("pydantic")

    try:
        importlib.import_module("cryptography.fernet")

        print("✓ Cryptography installed")
    except ImportError:
        missing.append("cryptography")

    try:
        importlib.import_module("dotenv")

        print("✓ Python-dotenv installed")
    except ImportError:
        missing.append("python-dotenv")

    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("\nInstall missing packages:")
        print(f"  pip install {' '.join(missing)}")
        return False

    print("\n✅ All core dependencies installed!")
    print("\nNext steps:")
    print("  1. python3 tools/encrypted_env_demo.py setup")
    print("  2. Edit .env with your API keys")
    print("  3. python3 tools/encrypted_env_demo.py encrypt")
    return True


if __name__ == "__main__":
    success = check_dependencies()
    sys.exit(0 if success else 1)
