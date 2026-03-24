from __future__ import annotations

from pathlib import Path

APP_NAME = 'context-menu-runner'
INSTALL_DIR_NAME = 'context-menu-runner'


def get_install_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_logs_dir() -> Path:
    return get_install_root() / 'logs'


def ensure_logs_dir() -> Path:
    logs_dir = get_logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_default_action_path() -> Path:
    return get_install_root() / 'actions' / 'default_action.py'
