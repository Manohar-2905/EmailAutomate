"""
setup_wizard.py — First-run setup wizard (CustomTkinter modal window)
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox
import threading

import customtkinter as ctk

from account_manager import set_base_folder, set_drive_enabled, add_account, is_first_run
from utils import logger

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SetupWizard(ctk.CTkToplevel):
    """Modal wizard shown on first launch."""

    def __init__(self, parent=None, on_complete=None):
        super().__init__(parent)
        self.on_complete = on_complete
        self.title("Bank Statement Agent — First-Time Setup")
        self.geometry("600x520")
        self.resizable(False, False)
        self.grab_set()   # Modal
        self._step = 0
        self._pages = []
        self._build()

    # ────────────────────────────────────────────
    # Build
    # ────────────────────────────────────────────
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Page container
        self._container = ctk.CTkFrame(self, fg_color="transparent")
        self._container.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)

        # Navigation buttons
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))
        nav.grid_columnconfigure((0, 1, 2), weight=1)

        self._back_btn  = ctk.CTkButton(nav, text="← Back",  command=self._back,  width=100)
        self._next_btn  = ctk.CTkButton(nav, text="Next →",  command=self._next,  width=100)
        self._finish_btn = ctk.CTkButton(nav, text="✓ Finish", command=self._finish,
                                         fg_color="#2ECC71", hover_color="#27AE60", width=110)
        self._back_btn.grid(row=0, column=0, sticky="w")
        self._next_btn.grid(row=0, column=2, sticky="e")

        self._pages = [self._page_welcome, self._page_folder, self._page_account, self._page_done]
        self._show_page(0)

    # ────────────────────────────────────────────
    # Pages
    # ────────────────────────────────────────────
    def _clear_container(self):
        for w in self._container.winfo_children():
            w.destroy()

    def _show_page(self, idx: int):
        self._clear_container()
        self._step = idx
        self._pages[idx]()
        self._back_btn.configure(state="normal" if idx > 0 else "disabled")
        at_last = (idx == len(self._pages) - 1)
        self._next_btn.grid() if not at_last else self._next_btn.grid_remove()
        if at_last:
            self._finish_btn.grid(row=0, column=2, sticky="e")
        else:
            self._finish_btn.grid_remove()

    def _page_welcome(self):
        f = self._container
        ctk.CTkLabel(f, text="👋  Welcome to Bank Statement Agent",
                     font=("Segoe UI", 20, "bold")).pack(pady=(20, 8))
        ctk.CTkLabel(f, text="This wizard will help you configure the app in 3 simple steps.\n\n"
                     "• Step 1 — Choose your base folder\n"
                     "• Step 2 — Add your first Gmail account\n"
                     "• Step 3 — Done!\n\n"
                     "Click Next to begin.",
                     font=("Segoe UI", 13), justify="left").pack(pady=10, padx=20)

    def _page_folder(self):
        f = self._container
        ctk.CTkLabel(f, text="📁  Step 1: Choose Base Folder",
                     font=("Segoe UI", 18, "bold")).pack(pady=(20, 8))
        ctk.CTkLabel(f, text="All downloaded bank statements will be saved here.\n"
                     "Sub-folders will be created automatically per user and bank.",
                     font=("Segoe UI", 12), justify="left").pack(pady=4, padx=20)

        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=10)

        self._folder_var = tk.StringVar()
        entry = ctk.CTkEntry(row, textvariable=self._folder_var,
                             placeholder_text="e.g. C:\\BankStatements", width=350)
        entry.pack(side="left", padx=(0, 8))
        ctk.CTkButton(row, text="Browse…", width=90,
                      command=self._browse_folder).pack(side="left")

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select Base Folder")
        if folder:
            self._folder_var.set(folder)

    def _page_account(self):
        f = self._container
        ctk.CTkLabel(f, text="📧  Step 2: Add First Gmail Account",
                     font=("Segoe UI", 18, "bold")).pack(pady=(20, 8))

        def row_pair(label, placeholder, show=""):
            fr = ctk.CTkFrame(f, fg_color="transparent")
            fr.pack(fill="x", padx=30, pady=4)
            ctk.CTkLabel(fr, text=label, width=110, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(fr, placeholder_text=placeholder, width=300, show=show)
            entry.pack(side="left")
            return entry

        self._acc_name  = row_pair("Name:",         "e.g. Prem")
        self._acc_email = row_pair("Gmail:",        "prem@gmail.com")
        self._acc_pw    = row_pair("App Password:", "xxxx xxxx xxxx xxxx", show="●")

        ctk.CTkLabel(f, text="ℹ  Need an App Password? Go to myaccount.google.com\n"
                     "→ Security → 2-Step Verification → App Passwords",
                     font=("Segoe UI", 11), text_color="#95A5A6", justify="left").pack(
            pady=8, padx=30)

    def _page_done(self):
        f = self._container
        ctk.CTkLabel(f, text="✅  Setup Complete!",
                     font=("Segoe UI", 22, "bold"), text_color="#2ECC71").pack(pady=(40, 12))
        ctk.CTkLabel(f, text="Your configuration has been saved.\n\n"
                     "Click Finish to open the main dashboard.",
                     font=("Segoe UI", 14), justify="center").pack()

    # ────────────────────────────────────────────
    # Navigation
    # ────────────────────────────────────────────
    def _back(self):
        if self._step > 0:
            self._show_page(self._step - 1)

    def _next(self):
        if not self._validate_current():
            return
        self._save_current()
        self._show_page(self._step + 1)

    def _validate_current(self) -> bool:
        if self._step == 1:
            if not self._folder_var.get().strip():
                messagebox.showwarning("Missing", "Please select a base folder.", parent=self)
                return False
        elif self._step == 2:
            if not self._acc_name.get().strip():
                messagebox.showwarning("Missing", "Please enter a name.", parent=self)
                return False
            if "@" not in self._acc_email.get():
                messagebox.showwarning("Missing", "Please enter a valid Gmail address.", parent=self)
                return False
            if not self._acc_pw.get().strip():
                messagebox.showwarning("Missing", "Please enter the App Password.", parent=self)
                return False
        return True

    def _save_current(self):
        if self._step == 1:
            set_base_folder(self._folder_var.get().strip())
        elif self._step == 2:
            added = add_account(
                name=self._acc_name.get().strip(),
                email=self._acc_email.get().strip(),
                app_password=self._acc_pw.get().strip(),
            )
            if not added:
                messagebox.showwarning("Duplicate",
                    "That Gmail account is already configured.", parent=self)

    def _finish(self):
        self.destroy()
        if self.on_complete:
            self.on_complete()


# ────────────────────────────────────────────
# Dependency installer (runs before UI starts)
# ────────────────────────────────────────────
def ensure_dependencies(progress_cb=None):
    """Install missing packages from requirements.txt."""
    import subprocess, sys, importlib
    from pathlib import Path

    req_file = Path(__file__).parent / "requirements.txt"
    if not req_file.exists():
        return

    packages = [
        line.strip().split("==")[0]
        for line in req_file.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

    for pkg in packages:
        try:
            importlib.import_module(pkg.replace("-", "_").lower())
        except ImportError:
            if progress_cb:
                progress_cb(f"Installing {pkg}…")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg, "-q"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
