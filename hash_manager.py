"""
hash_manager.py — SHA-256 file-level duplicate detection via hash_db.json
"""

from __future__ import annotations
from typing import List

from utils import HASH_DB_PATH, load_json, save_json, sha256_of_bytes, logger


def _load() -> dict:
    return load_json(HASH_DB_PATH, default={})


def _save(data: dict) -> None:
    save_json(HASH_DB_PATH, data)


def is_duplicate(user_name: str, file_bytes: bytes) -> bool:
    h = sha256_of_bytes(file_bytes)
    data = _load()
    return h in data.get(user_name, [])


def register_file(user_name: str, file_bytes: bytes) -> str:
    """Store hash; return the hex digest."""
    h = sha256_of_bytes(file_bytes)
    data = _load()
    data.setdefault(user_name, [])
    if h not in data[user_name]:
        data[user_name].append(h)
        _save(data)
        logger.debug(f"[{user_name}] Registered file hash: {h[:16]}…")
    return h


def get_hashes(user_name: str) -> List[str]:
    return _load().get(user_name, [])
