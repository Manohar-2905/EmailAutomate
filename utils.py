"""
utils.py — Shared utilities: paths, logging, JSON helpers
"""

import json
import os
import logging
import hashlib
from datetime import datetime
from pathlib import Path

# ──────────────────────────────────────────────
# Base paths (resolved relative to this file)
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()

CONFIG_PATH         = BASE_DIR / "config.json"
PROCESSED_PATH      = BASE_DIR / "processed_emails.json"
HASH_DB_PATH        = BASE_DIR / "hash_db.json"
LOG_PATH            = BASE_DIR / "logs.txt"


# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
def get_logger(name: str = "BankAgent") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")

    # File handler
    fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


logger = get_logger()


# ──────────────────────────────────────────────
# JSON helpers
# ──────────────────────────────────────────────
def load_json(path: Path, default=None):
    """Load JSON file; return default if missing or corrupt."""
    if default is None:
        default = {}
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Could not load {path}: {e}")
    return default


def save_json(path: Path, data):
    """Save data to JSON file atomically."""
    try:
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp.replace(path)
    except OSError as e:
        logger.error(f"Could not save {path}: {e}")


# ──────────────────────────────────────────────
# File hashing
# ──────────────────────────────────────────────
def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_of_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ──────────────────────────────────────────────
# Folder helpers
# ──────────────────────────────────────────────
def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def user_bank_folder(base_folder: str, user_name: str, bank_name: str) -> Path:
    """Return (and create) Base/UserName/BankName/"""
    folder = Path(base_folder) / user_name / bank_name
    return ensure_dir(folder)


# ──────────────────────────────────────────────
# Timestamp
# ──────────────────────────────────────────────
def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def date_str() -> str:
    return datetime.now().strftime("%Y%m%d")
