"""Load local configuration before importing configured runtime services."""

import logging
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def bootstrap_environment():
    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    load_dotenv(dotenv_path=env_path, override=False)
    if (
        env_path.exists()
        or not (root / ".env.encrypted").exists()
        or not (root / ".env.key").exists()
    ):
        return
    from tools.encrypted_env_demo import EncryptedEnvManager

    EncryptedEnvManager(project_root=root).load_env(decrypt_first=True)
    load_dotenv(dotenv_path=env_path, override=False)


bootstrap_environment()
