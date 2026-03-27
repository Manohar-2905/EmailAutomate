"""
account_manager.py — CRUD operations for Gmail accounts stored in config.json
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any

from utils import CONFIG_PATH, load_json, save_json, logger


# ──────────────────────────────────────────────
# Default config skeleton
# ──────────────────────────────────────────────
DEFAULT_CONFIG: Dict[str, Any] = {
    "base_folder": "",
    "drive_enabled": False,
    "accounts": [],
}


def _load_config() -> Dict[str, Any]:
    cfg = load_json(CONFIG_PATH, default=None)
    if cfg is None:
        cfg = dict(DEFAULT_CONFIG)
    # Back-fill missing top-level keys
    for k, v in DEFAULT_CONFIG.items():
        cfg.setdefault(k, v)
    return cfg


def _save_config(cfg: Dict[str, Any]) -> None:
    save_json(CONFIG_PATH, cfg)


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────
def get_config() -> Dict[str, Any]:
    return _load_config()


def set_base_folder(folder: str) -> None:
    cfg = _load_config()
    cfg["base_folder"] = folder
    _save_config(cfg)
    logger.info(f"Base folder set to: {folder}")


def set_drive_enabled(enabled: bool) -> None:
    cfg = _load_config()
    cfg["drive_enabled"] = enabled
    _save_config(cfg)


def get_accounts() -> List[Dict[str, str]]:
    return _load_config().get("accounts", [])


def add_account(name: str, email: str, app_password: str) -> bool:
    """Returns False if email already exists."""
    cfg = _load_config()
    for acc in cfg["accounts"]:
        if acc["email"].lower() == email.lower():
            logger.warning(f"Account {email} already exists.")
            return False
    cfg["accounts"].append({
        "name": name.strip(),
        "email": email.strip().lower(),
        "app_password": app_password.strip(),
    })
    _save_config(cfg)
    logger.info(f"Account added: {name} <{email}>")
    return True


def update_account(email: str, new_name: str = None,
                   new_email: str = None, new_password: str = None) -> bool:
    cfg = _load_config()
    for acc in cfg["accounts"]:
        if acc["email"].lower() == email.lower():
            if new_name:
                acc["name"] = new_name.strip()
            if new_email:
                acc["email"] = new_email.strip().lower()
            if new_password:
                acc["app_password"] = new_password.strip()
            _save_config(cfg)
            logger.info(f"Account updated: {email}")
            return True
    logger.warning(f"Account not found: {email}")
    return False


def delete_account(email: str) -> bool:
    cfg = _load_config()
    before = len(cfg["accounts"])
    cfg["accounts"] = [a for a in cfg["accounts"]
                       if a["email"].lower() != email.lower()]
    if len(cfg["accounts"]) < before:
        _save_config(cfg)
        logger.info(f"Account deleted: {email}")
        return True
    logger.warning(f"Account not found for deletion: {email}")
    return False


def is_first_run() -> bool:
    """True if config file doesn't exist or base_folder is empty."""
    if not CONFIG_PATH.exists():
        return True
    cfg = _load_config()
    return not bool(cfg.get("base_folder"))
