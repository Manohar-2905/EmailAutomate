"""
email_tracker.py — Idempotent email processing via processed_emails.json

Checkpoint system:
  For each account we store the highest IMAP UID seen so far.
  On the next run we search only  "UID <last+1>:*"  — skipping
  the entire history in a single IMAP command.
  The existing Message-ID dedup is kept as a second safety net.
"""

from __future__ import annotations
from typing import List

from utils import PROCESSED_PATH, load_json, save_json, logger


def _load() -> dict:
    return load_json(PROCESSED_PATH, default={})


def _save(data: dict) -> None:
    save_json(PROCESSED_PATH, data)


# ──────────────────────────────────────────────
# Legacy Migration Helper
# ──────────────────────────────────────────────

def _get_account_data(user_name: str) -> dict:
    """Returns the dict for user_name, migrating from legacy list if needed."""
    data = _load()
    acc = data.get(user_name, {"ids": [], "last_uid": 0})
    if isinstance(acc, list):
        acc = {"ids": acc, "last_uid": 0}
        data[user_name] = acc
        _save(data)
    return acc


# ── Message-ID dedup (safety net) ─────────────────────────────────────────

def is_processed(user_name: str, email_id: str) -> bool:
    acc = _get_account_data(user_name)
    return email_id in acc.get("ids", [])


def mark_processed(user_name: str, email_id: str) -> None:
    data = _load()
    acc = _get_account_data(user_name)
    if email_id not in acc["ids"]:
        acc["ids"].append(email_id)
        data[user_name] = acc
        _save(data)
        logger.debug(f"[{user_name}] Marked email as processed: {email_id}")


def get_processed_ids(user_name: str) -> List[str]:
    acc = _get_account_data(user_name)
    return acc.get("ids", [])


def processed_count(user_name: str) -> int:
    return len(get_processed_ids(user_name))


# ── UID Checkpoint ─────────────────────────────────────────────────────────

def get_last_uid(user_name: str) -> int:
    """Return the last IMAP UID processed for this account (0 = never run)."""
    acc = _get_account_data(user_name)
    return int(acc.get("last_uid", 0))


def set_last_uid(user_name: str, uid: int) -> None:
    """Persist the highest IMAP UID seen so the next run can start from uid+1."""
    data = _load()
    acc = data.get(user_name, {})
    # Migrate old list format transparently
    if isinstance(acc, list):
        acc = {"ids": acc, "last_uid": 0}
    acc["last_uid"] = uid
    data[user_name] = acc
    _save(data)
    logger.debug(f"[{user_name}] Checkpoint UID saved: {uid}")
