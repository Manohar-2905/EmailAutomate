"""
drive_service.py — Google Drive upload with folder mirroring and duplicate prevention
Uses a service-account credentials file (credentials.json) or OAuth token.
"""

from __future__ import annotations

import os
import io
import json
from pathlib import Path
from typing import Dict, Optional, Callable

from utils import logger, BASE_DIR

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    DRIVE_AVAILABLE = True
except ImportError:
    DRIVE_AVAILABLE = False

SCOPES        = ["https://www.googleapis.com/auth/drive"]
CREDS_FILE    = BASE_DIR / "credentials.json"
TOKEN_FILE    = BASE_DIR / "token.json"
MIME_PDF      = "application/pdf"
MIME_FOLDER   = "application/vnd.google-apps.folder"


# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────
def _get_service():
    if not DRIVE_AVAILABLE:
        raise RuntimeError("google-api-python-client not installed.")

    creds = None

    # Try OAuth token first
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # Refresh / re-authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_FILE.exists():
                raise FileNotFoundError(
                    f"Google credentials file not found: {CREDS_FILE}\n"
                    "Download it from Google Cloud Console > APIs & Services > Credentials."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


# ──────────────────────────────────────────────
# Folder helpers
# ──────────────────────────────────────────────
_folder_cache: Dict[str, str] = {}   # path_key -> folder_id


def _get_or_create_folder(service, name: str, parent_id: Optional[str] = None) -> str:
    cache_key = f"{parent_id or 'root'}/{name}"
    if cache_key in _folder_cache:
        return _folder_cache[cache_key]

    query = f"name='{name}' and mimeType='{MIME_FOLDER}' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    else:
        query += " and 'root' in parents"

    resp = service.files().list(q=query, fields="files(id, name)").execute()
    files = resp.get("files", [])
    if files:
        folder_id = files[0]["id"]
    else:
        meta = {
            "name": name,
            "mimeType": MIME_FOLDER,
            "parents": [parent_id] if parent_id else [],
        }
        folder = service.files().create(body=meta, fields="id").execute()
        folder_id = folder["id"]

    _folder_cache[cache_key] = folder_id
    return folder_id


def _file_exists_in_folder(service, filename: str, folder_id: str) -> bool:
    query = (f"name='{filename}' and '{folder_id}' in parents "
             f"and trashed=false")
    resp = service.files().list(q=query, fields="files(id)").execute()
    return bool(resp.get("files"))


# ──────────────────────────────────────────────
# Public upload function
# ──────────────────────────────────────────────
def upload_file(
    local_path: Path,
    user_name: str,
    bank_name: str,
    log_cb: Callable[[str], None] = print,
) -> bool:
    """
    Upload a single PDF to Drive under BankStatements/<user_name>/<bank_name>/
    Returns True on success.
    """
    if not DRIVE_AVAILABLE:
        log_cb("Google Drive SDK not installed — skipping upload.")
        return False

    def log(msg):
        logger.info(f"[Drive] {msg}")
        log_cb(f"[Drive] {msg}")

    try:
        service = _get_service()

        # Ensure folder hierarchy: BankStatements / user_name / bank_name
        root_id = _get_or_create_folder(service, "BankStatements")
        user_id = _get_or_create_folder(service, user_name, parent_id=root_id)
        bank_id = _get_or_create_folder(service, bank_name, parent_id=user_id)

        filename = local_path.name

        # Duplicate check on Drive
        if _file_exists_in_folder(service, filename, bank_id):
            log(f"Already on Drive, skipping: {filename}")
            return True

        # Upload
        meta = {"name": filename, "parents": [bank_id]}
        with open(local_path, "rb") as fh:
            media = MediaIoBaseUpload(fh, mimetype=MIME_PDF, resumable=True)
            service.files().create(body=meta, media_body=media,
                                   fields="id").execute()

        log(f"Uploaded: {filename} → BankStatements/{user_name}/{bank_name}/")
        return True

    except Exception as e:
        log(f"Upload failed for {local_path.name}: {e}")
        logger.exception(e)
        return False


def upload_user_folder(
    base_folder: str,
    user_name: str,
    log_cb: Callable[[str], None] = print,
) -> None:
    """Walk all bank sub-folders for a user and upload every PDF."""
    user_dir = Path(base_folder) / user_name
    if not user_dir.exists():
        return
    for bank_dir in user_dir.iterdir():
        if bank_dir.is_dir():
            for pdf in bank_dir.glob("*.pdf"):
                upload_file(pdf, user_name, bank_dir.name, log_cb=log_cb)
