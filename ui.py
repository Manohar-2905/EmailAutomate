"""
ui.py — Bank Statement Agent — Main Dashboard (CustomTkinter)
"""

from __future__ import annotations

import sys
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
from pathlib import Path
import queue
import math

import customtkinter as ctk

from account_manager import (
    get_config, get_accounts, add_account, update_account,
    delete_account, set_base_folder, set_drive_enabled, is_first_run,
)
from automation_runner import run_all_accounts
from scheduler import register_daily_task, remove_daily_task, task_exists
from utils import logger, LOG_PATH

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ────────────────────────────────────────────────────────────────────────────
# Colour palette
# ────────────────────────────────────────────────────────────────────────────
C = {
    "bg":           "#1A1A2E",
    "surface":      "#16213E",
    "card":         "#0F3460",
    "accent":       "#E94560",
    "accent2":      "#533483",
    "green":        "#2ECC71",
    "yellow":       "#F39C12",
    "red":          "#E74C3C",
    "text":         "#ECF0F1",
    "subtext":      "#95A5A6",
}


# ────────────────────────────────────────────────────────────────────────────
# Account dialog (Add / Edit)
# ────────────────────────────────────────────────────────────────────────────
class AccountDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="Add Account",
                 name="", email="", password=""):
        super().__init__(parent)
        self.title(title)
        self.geometry("440x300")
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        # Intercept window-close so result stays None (same as Cancel)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        ctk.CTkLabel(self, text=title,
                     font=("Segoe UI", 16, "bold")).pack(pady=(18, 8))

        def labeled_entry(label, value, show=""):
            fr = ctk.CTkFrame(self, fg_color="transparent")
            fr.pack(fill="x", padx=30, pady=4)
            ctk.CTkLabel(fr, text=label, width=110, anchor="w").pack(side="left")
            e = ctk.CTkEntry(fr, width=250, show=show)
            e.insert(0, value)
            e.pack(side="left")
            return e

        self._name  = labeled_entry("Name:",         name)
        self._email = labeled_entry("Gmail:",         email)
        self._pw    = labeled_entry("App Password:", password, show="●")

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=14)
        ctk.CTkButton(btns, text="Cancel", width=100,
                      fg_color="gray30", hover_color="gray40",
                      command=self._on_cancel).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Save", width=100,
                      command=self._save).pack(side="left", padx=6)

    def _on_cancel(self):
        """Cancel without saving — result stays None."""
        self.result = None
        self.grab_release()
        self.destroy()

    def _save(self):
        name  = self._name.get().strip()
        email = self._email.get().strip()
        pw    = self._pw.get().strip()
        if not name or not email or not pw:
            messagebox.showwarning("Incomplete", "All fields are required.", parent=self)
            return
        if "@" not in email:
            messagebox.showwarning("Invalid", "Enter a valid email address.", parent=self)
            return
        # Store result BEFORE destroying so wait_window() can read it
        self.result = {"name": name, "email": email, "app_password": pw}
        self.grab_release()
        self.destroy()


# ────────────────────────────────────────────────────────────────────────────
# Main Application Window
# ────────────────────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Bank Statement Agent")
        self.geometry("1050x720")
        self.minsize(900, 620)
        self.configure(fg_color=C["bg"])

        # ── App icon (taskbar + title bar) ────────
        _icon = Path(__file__).with_name("icon.ico")
        if _icon.exists():
            try:
                self.wm_iconbitmap(str(_icon))
            except Exception:
                pass

        self._log_queue: queue.Queue = queue.Queue()
        self._running = False

        # ── Window close handler (Fix #4) ────────
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_layout()
        self._refresh_accounts()
        self._refresh_settings()
        self._check_scheduler_status()
        self._poll_log_queue()

    def _on_close(self):
        """Confirm before closing while automation is running."""
        if self._running:
            if not messagebox.askyesno(
                "Automation Running",
                "Automation is still running.\nAre you sure you want to quit?",
            ):
                return
        self.destroy()

    # ────────────────────────────────────────────
    # Layout
    # ────────────────────────────────────────────
    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0)   # Sidebar
        self.grid_columnconfigure(1, weight=1)   # Content
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ──────────────────────────────
        sidebar = ctk.CTkFrame(self, width=200, fg_color=C["surface"],
                               corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(sidebar, text="💳", font=("Segoe UI", 36)).pack(pady=(24, 2))
        ctk.CTkLabel(sidebar, text="Bank\nStatement\nAgent",
                     font=("Segoe UI", 14, "bold"),
                     text_color=C["text"]).pack()

        sep = ctk.CTkFrame(sidebar, height=1, fg_color="gray30")
        sep.pack(fill="x", padx=16, pady=16)

        nav_items = [
            ("🏠  Dashboard",  self._show_dashboard),
            ("👥  Accounts",   self._show_accounts),
            ("⚙️  Settings",   self._show_settings),
            ("📋  Logs",       self._show_logs),
        ]
        self._nav_btns = []
        for label, cmd in nav_items:
            btn = ctk.CTkButton(sidebar, text=label, anchor="w",
                                font=("Segoe UI", 13),
                                fg_color="transparent",
                                hover_color=C["card"],
                                text_color=C["text"],
                                command=cmd, height=38, corner_radius=8)
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_btns.append(btn)

        # ── Content area ──────────────────────────
        self._content = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        self._show_dashboard()

    def _clear_content(self):
        for w in self._content.winfo_children():
            w.destroy()

    # ────────────────────────────────────────────
    # Dashboard Tab
    # ────────────────────────────────────────────
    def _show_dashboard(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self._content, fg_color=C["bg"])
        f.grid(row=0, column=0, sticky="nsew")
        f.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(f, text="🏠  Dashboard",
                     font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=24, pady=(22, 4))

        # ── Status cards ─────────────────────────
        cards_row = ctk.CTkFrame(f, fg_color="transparent")
        cards_row.pack(fill="x", padx=24, pady=10)

        cfg = get_config()
        accounts = get_accounts()

        # Deduplicate task_exists() call (performance fix)
        _sched_active = task_exists()
        self._make_stat_card(cards_row, "👥 Accounts",  str(len(accounts)), C["accent2"])
        self._make_stat_card(cards_row, "📁 Base Folder",
                             "Set" if cfg.get("base_folder") else "Not Set",
                             C["card"])
        self._make_stat_card(cards_row, "☁ Drive",
                             "Enabled" if cfg.get("drive_enabled") else "Disabled",
                             C["green"] if cfg.get("drive_enabled") else "gray30")
        self._make_stat_card(cards_row, "⏰ Scheduler",
                             "Active" if _sched_active else "Inactive",
                             C["green"] if _sched_active else C["yellow"])

        # ── Run button & progress ─────────────────
        run_card = ctk.CTkFrame(f, fg_color=C["surface"], corner_radius=12)
        run_card.pack(fill="x", padx=24, pady=10)

        ctk.CTkLabel(run_card, text="▶  Manual Run",
                     font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=20, pady=(16, 4))
        ctk.CTkLabel(run_card,
                     text="Process all accounts now. Already-processed emails are never re-downloaded.",
                     text_color=C["subtext"],
                     font=("Segoe UI", 11)).pack(anchor="w", padx=20)

        self._run_btn = ctk.CTkButton(run_card, text="🚀  Run Automation",
                                      font=("Segoe UI", 13, "bold"),
                                      fg_color=C["accent"], hover_color="#C0392B",
                                      height=42, corner_radius=8,
                                      command=self._start_automation)
        self._run_btn.pack(anchor="w", padx=20, pady=12)

        self._progress_label = ctk.CTkLabel(run_card, text="",
                                            font=("Segoe UI", 11),
                                            text_color=C["subtext"])
        self._progress_label.pack(anchor="w", padx=20)

        self._progress = ctk.CTkProgressBar(run_card, width=500, height=12,
                                            fg_color="gray20",
                                            progress_color=C["green"])
        self._progress.pack(anchor="w", padx=20, pady=(4, 16))
        self._progress.set(0)

        # ── Live log panel ────────────────────────
        log_card = ctk.CTkFrame(f, fg_color=C["surface"], corner_radius=12)
        log_card.pack(fill="both", expand=True, padx=24, pady=10)

        ctk.CTkLabel(log_card, text="📡  Live Log",
                     font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(14, 4))

        self._live_log = ctk.CTkTextbox(log_card, height=220,
                                        font=("Consolas", 11),
                                        fg_color="#0D1117",
                                        text_color="#7EE787",
                                        state="disabled")
        self._live_log.pack(fill="both", expand=True, padx=20, pady=(0, 14))

    def _make_stat_card(self, parent, title, value, color):
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=10, width=180, height=80)
        card.pack(side="left", padx=6, pady=4)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 11),
                     text_color="white").pack(pady=(10, 0))
        ctk.CTkLabel(card, text=value, font=("Segoe UI", 18, "bold"),
                     text_color="white").pack()

    # ────────────────────────────────────────────
    # Automation runner
    # ────────────────────────────────────────────
    def _start_automation(self):
        if self._running:
            return
        cfg = get_config()
        if not cfg.get("base_folder"):
            messagebox.showerror("Setup Required",
                                 "Please configure the base folder in Settings first.")
            return
        if not get_accounts():
            messagebox.showerror("No Accounts",
                                 "Please add at least one Gmail account first.")
            return

        self._running = True
        self._progress_real = 0.0   # tracks true per-account progress
        self._progress_tick = 0     # animation frame counter
        self._run_btn.configure(state="disabled", text="⏳ Running…")
        self._progress.set(0)
        self._progress_label.configure(text="Starting")
        self._live_log_append("─── Run started ───")

        def worker():
            accs  = get_accounts()
            total = len(accs)
            done  = [0]  # mutable container for closure

            def cb(msg: str):
                self._log_queue.put(msg)
                # Advance progress bar after each account finishes
                # Note: msg has a "[Name] " prefix, so use "in" not startswith
                if "Done. Saved=" in msg:
                    done[0] += 1
                    pct = done[0] / total if total else 1.0
                    label = f"Processing account {done[0]} / {total}"
                    self._progress_real = pct          # update real target
                    self.after(0, lambda l=label:
                        self._progress_label.configure(text=l))

            run_all_accounts(log_cb=cb)

            self.after(0, self._automation_done)

        threading.Thread(target=worker, daemon=True).start()
        self._dot_step = 0
        self._animate_dots()
        self._animate_progress_bar()

    def _animate_progress_bar(self):
        """Smooth sine-wave pulse around the real progress value (25 fps)."""
        if not self._running:
            return
        self._progress_tick += 1
        # Sine oscillates ±0.06 around the real progress (never goes below 0.03)
        wave = math.sin(self._progress_tick * 0.18) * 0.06
        display = max(0.03, min(1.0, self._progress_real + wave))
        try:
            self._progress.set(display)
        except Exception:
            pass
        self.after(40, self._animate_progress_bar)   # ~25 fps

    def _animate_dots(self):
        """Cycle '.' / '..' / '...' on the progress label every 500 ms."""
        if not self._running:
            return
        dots = [".", "..", "..."]
        self._dot_step = (self._dot_step + 1) % len(dots)
        try:
            current = self._progress_label.cget("text")
            base = current.rstrip(". ")
            self._progress_label.configure(text=base + dots[self._dot_step])
        except Exception:
            pass
        self.after(500, self._animate_dots)

    def _automation_done(self):
        self._running = False
        self._progress_real = 1.0
        self._run_btn.configure(state="normal", text="🚀  Run Automation")
        self._progress.set(1.0)
        self._progress_label.configure(text="✅  Completed")
        self._live_log_append("─── Run complete ───")

    def _live_log_append(self, text: str):
        try:
            self._live_log.configure(state="normal")
            self._live_log.insert("end", text + "\n")
            self._live_log.see("end")
            self._live_log.configure(state="disabled")
        except Exception:
            pass

    def _poll_log_queue(self):
        try:
            while True:
                msg = self._log_queue.get_nowait()
                self._live_log_append(msg)
        except queue.Empty:
            pass
        self.after(100, self._poll_log_queue)

    # ────────────────────────────────────────────
    # Accounts Tab
    # ────────────────────────────────────────────
    def _show_accounts(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self._content, fg_color=C["bg"])
        f.grid(row=0, column=0, sticky="nsew")
        f.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(f, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(22, 8))
        ctk.CTkLabel(header, text="👥  Account Management",
                     font=("Segoe UI", 22, "bold")).pack(side="left")
        ctk.CTkButton(header, text="➕ Add Account", width=140,
                      fg_color=C["green"], hover_color="#27AE60",
                      command=self._add_account_dialog).pack(side="right")

        self._acc_list_frame = ctk.CTkFrame(f, fg_color=C["surface"],
                                            corner_radius=12)
        self._acc_list_frame.pack(fill="both", expand=True, padx=24, pady=8)
        self._render_account_list()

    def _render_account_list(self):
        for w in self._acc_list_frame.winfo_children():
            w.destroy()
        accounts = get_accounts()
        if not accounts:
            ctk.CTkLabel(self._acc_list_frame,
                         text="No accounts yet. Click '➕ Add Account' to begin.",
                         text_color=C["subtext"]).pack(pady=30)
            return

        # Header row
        hdr = ctk.CTkFrame(self._acc_list_frame, fg_color=C["card"],
                           corner_radius=6)
        hdr.pack(fill="x", padx=12, pady=(10, 4))
        for col, w in [("Name", 160), ("Gmail", 280), ("Actions", 200)]:
            ctk.CTkLabel(hdr, text=col, font=("Segoe UI", 11, "bold"),
                         width=w, anchor="w").pack(side="left", padx=8, pady=6)

        for acc in accounts:
            row = ctk.CTkFrame(self._acc_list_frame,
                               fg_color="transparent", corner_radius=6)
            row.pack(fill="x", padx=12, pady=2)

            ctk.CTkLabel(row, text=acc["name"],   width=160, anchor="w",
                         font=("Segoe UI", 12)).pack(side="left", padx=8)
            ctk.CTkLabel(row, text=acc["email"],  width=280, anchor="w",
                         text_color=C["subtext"],
                         font=("Segoe UI", 11)).pack(side="left")

            action_fr = ctk.CTkFrame(row, fg_color="transparent")
            action_fr.pack(side="left", padx=8)
            ctk.CTkButton(action_fr, text="✏ Edit", width=70, height=28,
                          fg_color=C["accent2"], hover_color="#6C3483",
                          command=lambda a=acc: self._edit_account_dialog(a)
                          ).pack(side="left", padx=3)
            ctk.CTkButton(action_fr, text="🗑 Del", width=70, height=28,
                          fg_color=C["red"], hover_color="#C0392B",
                          command=lambda a=acc: self._delete_account(a)
                          ).pack(side="left", padx=3)

    def _add_account_dialog(self):
        dlg = AccountDialog(self, title="➕ Add Account")
        self.wait_window(dlg)
        if dlg.result:
            ok = add_account(**dlg.result)
            if not ok:
                messagebox.showwarning("Duplicate",
                    "An account with that Gmail already exists.")
            self._refresh_accounts()

    def _edit_account_dialog(self, acc):
        dlg = AccountDialog(self, title="✏ Edit Account",
                            name=acc["name"], email=acc["email"],
                            password=acc["app_password"])
        self.wait_window(dlg)
        if dlg.result:
            update_account(
                email=acc["email"],
                new_name=dlg.result["name"],
                new_email=dlg.result["email"],
                new_password=dlg.result["app_password"],
            )
            self._refresh_accounts()

    def _delete_account(self, acc):
        if messagebox.askyesno("Confirm Delete",
                f"Delete account '{acc['name']}' ({acc['email']})?"):
            delete_account(acc["email"])
            self._refresh_accounts()

    def _refresh_accounts(self):
        try:
            self._render_account_list()
        except Exception:
            pass

    # ────────────────────────────────────────────
    # Settings Tab
    # ────────────────────────────────────────────
    def _show_settings(self):
        self._clear_content()
        f = ctk.CTkScrollableFrame(self._content, fg_color=C["bg"])
        f.grid(row=0, column=0, sticky="nsew")
        f.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(f, text="⚙️  Settings",
                     font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=24, pady=(22, 12))

        # ── Base folder ───────────────────────────
        folder_card = ctk.CTkFrame(f, fg_color=C["surface"], corner_radius=12)
        folder_card.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(folder_card, text="📁  Base Folder",
                     font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(14, 4))
        ctk.CTkLabel(folder_card,
                     text="Where bank statement PDFs will be saved locally.",
                     text_color=C["subtext"]).pack(anchor="w", padx=20)

        row = ctk.CTkFrame(folder_card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(8, 16))
        self._folder_entry = ctk.CTkEntry(row, width=380,
                                          placeholder_text="Select a folder…")
        self._folder_entry.pack(side="left", padx=(0, 8))
        ctk.CTkButton(row, text="Browse…", width=90,
                      command=self._browse_base_folder).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row, text="Save", width=70,
                      fg_color=C["green"], hover_color="#27AE60",
                      command=self._save_folder).pack(side="left")

        # ── Google Drive toggle ───────────────────
        drive_card = ctk.CTkFrame(f, fg_color=C["surface"], corner_radius=12)
        drive_card.pack(fill="x", padx=24, pady=8)
        dr = ctk.CTkFrame(drive_card, fg_color="transparent")
        dr.pack(fill="x", padx=20, pady=14)
        ctk.CTkLabel(dr, text="☁  Google Drive Backup",
                     font=("Segoe UI", 14, "bold")).pack(side="left")
        self._drive_switch = ctk.CTkSwitch(dr, text="",
                                           command=self._toggle_drive)
        self._drive_switch.pack(side="right")
        ctk.CTkLabel(drive_card,
                     text="Requires credentials.json from Google Cloud Console (Drive API).",
                     text_color=C["subtext"]).pack(anchor="w", padx=20, pady=(0, 14))

        # ── Scheduler ────────────────────────────
        sched_card = ctk.CTkFrame(f, fg_color=C["surface"], corner_radius=12)
        sched_card.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(sched_card, text="⏰  Daily Scheduler (9:00 AM)",
                     font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(14, 4))
        ctk.CTkLabel(sched_card,
                     text="Registers a Windows Task Scheduler job to run automatically every day.",
                     text_color=C["subtext"]).pack(anchor="w", padx=20)

        sched_btns = ctk.CTkFrame(sched_card, fg_color="transparent")
        sched_btns.pack(anchor="w", padx=20, pady=12)
        self._sched_status_lbl = ctk.CTkLabel(sched_btns, text="",
                                              font=("Segoe UI", 11))
        self._sched_status_lbl.pack(side="left", padx=(0, 14))
        ctk.CTkButton(sched_btns, text="Enable", width=90,
                      fg_color=C["green"], hover_color="#27AE60",
                      command=self._enable_scheduler).pack(side="left", padx=3)
        ctk.CTkButton(sched_btns, text="Disable", width=90,
                      fg_color=C["red"], hover_color="#C0392B",
                      command=self._disable_scheduler).pack(side="left", padx=3)

        self._refresh_settings()

    def _browse_base_folder(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Select Base Folder")
        if folder:
            self._folder_entry.delete(0, "end")
            self._folder_entry.insert(0, folder)

    def _save_folder(self):
        try:
            val = self._folder_entry.get().strip()
            if not val:
                messagebox.showwarning("Empty", "Please enter or browse a folder path.")
                return
            set_base_folder(val)
            messagebox.showinfo("Saved", f"Base folder set to:\n{val}")
        except AttributeError:
            pass

    def _toggle_drive(self):
        try:
            enabled = self._drive_switch.get() == 1
            set_drive_enabled(enabled)
        except AttributeError:
            pass

    def _enable_scheduler(self):
        ok = register_daily_task("09:00")
        if ok:
            messagebox.showinfo("Scheduler", "Daily task registered at 9:00 AM.")
        else:
            messagebox.showerror("Scheduler",
                "Failed to register task. Run the app as Administrator.")
        self._check_scheduler_status()

    def _disable_scheduler(self):
        remove_daily_task()
        self._check_scheduler_status()
        messagebox.showinfo("Scheduler", "Daily task removed.")

    def _check_scheduler_status(self):
        try:
            exists = task_exists()
            self._sched_status_lbl.configure(
                text="● Active" if exists else "● Inactive",
                text_color=C["green"] if exists else C["subtext"],
            )
        except Exception:
            pass

    def _refresh_settings(self):
        try:
            cfg = get_config()
            folder = cfg.get("base_folder", "")
            self._folder_entry.delete(0, "end")
            self._folder_entry.insert(0, folder)
            if cfg.get("drive_enabled"):
                self._drive_switch.select()
            else:
                self._drive_switch.deselect()
        except Exception:
            pass

    # ────────────────────────────────────────────
    # Logs Tab
    # ────────────────────────────────────────────
    def _show_logs(self):
        self._clear_content()
        f = ctk.CTkFrame(self._content, fg_color=C["bg"])
        f.grid(row=0, column=0, sticky="nsew")
        f.grid_columnconfigure(0, weight=1)
        f.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(f, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 8))
        ctk.CTkLabel(hdr, text="📋  Logs",
                     font=("Segoe UI", 22, "bold")).pack(side="left")
        # Fix #5 — Back to Dashboard button
        ctk.CTkButton(hdr, text="🏠 Dashboard", width=120,
                      fg_color=C["accent2"], hover_color="#6C3483",
                      command=self._show_dashboard).pack(side="left", padx=(16, 0))
        ctk.CTkButton(hdr, text="🔄 Refresh", width=100,
                      command=self._show_logs).pack(side="right")
        ctk.CTkButton(hdr, text="🗑 Clear", width=90,
                      fg_color="gray30", hover_color="gray40",
                      command=self._clear_logs).pack(side="right", padx=6)

        log_box = ctk.CTkTextbox(f, font=("Consolas", 10),
                                 fg_color="#0D1117",
                                 text_color="#7EE787",
                                 state="disabled")
        log_box.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))

        try:
            if LOG_PATH.exists():
                content = LOG_PATH.read_text(encoding="utf-8", errors="replace")
                log_box.configure(state="normal")
                log_box.insert("1.0", content)
                log_box.see("end")
                log_box.configure(state="disabled")
            else:
                log_box.configure(state="normal")
                log_box.insert("1.0", "No logs yet.")
                log_box.configure(state="disabled")
        except Exception as e:
            pass

    def _clear_logs(self):
        if messagebox.askyesno("Clear Logs", "Are you sure you want to clear all logs?"):
            try:
                LOG_PATH.write_text("", encoding="utf-8")
                self._show_logs()
            except Exception:
                pass


# ────────────────────────────────────────────────────────────────────────────
# Entry point
# ────────────────────────────────────────────────────────────────────────────
def launch_app():
    app = App()

    # Show setup wizard on first run
    if is_first_run():
        def on_wizard_done():
            app._refresh_accounts()
            app._refresh_settings()
            app._show_dashboard()

        app.after(200, lambda: _open_wizard(app, on_wizard_done))

    app.mainloop()


def _open_wizard(parent, on_complete):
    from setup_wizard import SetupWizard
    wiz = SetupWizard(parent, on_complete=on_complete)


if __name__ == "__main__":
    launch_app()
