"""
scheduler.py — Windows Task Scheduler integration for 9 AM daily automation
"""

from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path

from utils import logger, BASE_DIR

TASK_NAME = "BankStatementAgent"


# ──────────────────────────────────────────────
# Schedule via Windows Task Scheduler (schtasks)
# ──────────────────────────────────────────────
def register_daily_task(run_time: str = "09:00") -> bool:
    """
    Register a Windows Scheduled Task to run the automation daily at run_time.
    Works for both .exe builds and plain Python.
    Returns True on success.
    """
    exe_path = _get_executable_path()
    cmd = [
        "schtasks", "/Create",
        "/F",                               # Force overwrite if exists
        "/TN", TASK_NAME,
        "/TR", f'"{exe_path}" --headless',
        "/SC", "DAILY",
        "/ST", run_time,
        "/RL", "HIGHEST",                   # Run with highest privileges
    ]

    logger.info(f"Registering Task Scheduler job: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Task '{TASK_NAME}' scheduled at {run_time} daily.")
            return True
        else:
            logger.error(f"schtasks error: {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        logger.error("schtasks not found. Are you on Windows?")
        return False


def remove_daily_task() -> bool:
    """Remove the scheduled task if it exists."""
    cmd = ["schtasks", "/Delete", "/F", "/TN", TASK_NAME]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def task_exists() -> bool:
    cmd = ["schtasks", "/Query", "/TN", TASK_NAME]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


# ──────────────────────────────────────────────
# In-process schedule loop (for --headless mode)
# ──────────────────────────────────────────────
def run_headless() -> None:
    """Called when app is launched with --headless flag by Task Scheduler."""
    from automation_runner import run_all_accounts
    logger.info("Headless run triggered by Task Scheduler.")
    run_all_accounts(log_cb=logger.info)
    logger.info("Headless run complete.")


# ──────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────
def _get_executable_path() -> str:
    if getattr(sys, "frozen", False):
        # Running as PyInstaller EXE
        return sys.executable
    else:
        # Running as plain Python script
        main_py = BASE_DIR / "main.py"
        return f'"{sys.executable}" "{main_py}"'
