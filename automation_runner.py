"""
automation_runner.py — Orchestrates processing of all accounts
"""

from __future__ import annotations

from typing import Callable, Dict, Any

from account_manager import get_config, get_accounts
from gmail_service import process_account
from drive_service import upload_user_folder
from utils import logger


def run_all_accounts(
    log_cb: Callable[[str], None] = print,
) -> Dict[str, Any]:
    """
    Process every configured Gmail account.
    Returns aggregated summary.
    """
    config    = get_config()
    base_folder = config.get("base_folder", "")
    drive_on    = config.get("drive_enabled", False)
    accounts    = get_accounts()

    totals = {"saved": 0, "skipped_email": 0, "skipped_hash": 0, "errors": 0}

    if not base_folder:
        msg = "ERROR: Base folder not configured. Please complete setup first."
        log_cb(msg)
        logger.error(msg)
        return totals

    if not accounts:
        log_cb("No accounts configured. Add at least one Gmail account.")
        return totals

    for acc in accounts:
        log_cb(f"\n{'='*50}")
        log_cb(f"Processing: {acc['name']} ({acc['email']})")
        log_cb(f"{'='*50}")

        summary = process_account(
            account=acc,
            base_folder=base_folder,
            log_cb=log_cb,
        )

        for k in totals:
            totals[k] += summary.get(k, 0)

        # Upload to Google Drive if enabled
        if drive_on:
            log_cb(f"\nUploading {acc['name']}'s files to Google Drive…")
            try:
                upload_user_folder(base_folder, acc["name"], log_cb=log_cb)
            except Exception as e:
                log_cb(f"Drive upload error for {acc['name']}: {e}")
                logger.exception(e)
                totals["errors"] += 1

    log_cb(f"\n{'='*50}")
    log_cb(f"ALL DONE — Saved: {totals['saved']}  "
           f"SkippedEmail: {totals['skipped_email']}  "
           f"SkippedDuplicate: {totals['skipped_hash']}  "
           f"Errors: {totals['errors']}")
    log_cb(f"{'='*50}\n")
    return totals
