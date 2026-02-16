#!/usr/bin/env python3
"""
Quick test to verify encrypted environment setup
Run this to ensure dependencies are installed
"""

import sys


def check_dependencies():
    """Check if all required dependencies are installed"""
    missing = []

    # Check core dependencies
    try:
        import flask

        print("✓ Flask installed")
    except ImportError:
        missing.append("flask")

    try:
        import pydantic

        print("✓ Pydantic installed")
    except ImportError:
        missing.append("pydantic")

    try:
        from cryptography.fernet import Fernet

        print("✓ Cryptography installed")
    except ImportError:
        missing.append("cryptography")

    try:
        import dotenv

        print("✓ Python-dotenv installed")
    except ImportError:
        missing.append("python-dotenv")

    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print(f"\nInstall missing packages:")
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
