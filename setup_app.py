"""
setup_app.py — Self-contained installer for Bank Statement Agent

How it works:
  PyInstaller bundles BankStatementAgent.exe INSIDE this script.
  When the user runs the resulting Setup EXE, this installer GUI appears,
  lets them pick an install folder, copies the app there, and creates shortcuts.

Build with:  build_setup.bat
"""

import sys
import os
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path


# ── Locate the bundled main EXE ────────────────────────────────────────────
def _bundled(filename: str) -> Path:
    """Return path to a file bundled via PyInstaller --add-data, or dev fallback."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / filename
    return Path(__file__).parent / "dist" / filename


def _create_shortcut_ps(target: Path, shortcut: Path, icon: Path | None = None):
    """Create a Windows .lnk shortcut using PowerShell (no extra deps)."""
    icon_line = f"$sc.IconLocation = '{icon}'" if icon and icon.exists() else ""
    script = f"""
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut('{shortcut}')
$sc.TargetPath = '{target}'
$sc.WorkingDirectory = '{target.parent}'
{icon_line}
$sc.Save()
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
    )


# ── Installer GUI ───────────────────────────────────────────────────────────
class InstallerApp:
    DEFAULT_DIR = str(
        Path.home() / "AppData" / "Local" / "Programs" / "Bank Statement Agent"
    )

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bank Statement Agent — Setup")
        self.root.geometry("540x420")
        self.root.resizable(False, False)
        self.root.configure(bg="#1A1A2E")

        # Centre on screen
        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"540x420+{(sw-540)//2}+{(sh-420)//2}")

        # App icon
        _ico = _bundled("icon.ico")
        if _ico.exists():
            try:
                self.root.wm_iconbitmap(str(_ico))
            except Exception:
                pass

        self.install_dir = tk.StringVar(value=self.DEFAULT_DIR)
        self.desktop_var = tk.BooleanVar(value=True)
        self.startmenu_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Ready to install.")

        self._build_ui()
        self.root.mainloop()

    # ── UI ──────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg="#0F3460", height=90)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(
            hdr, text="💳  Bank Statement Agent",
            font=("Segoe UI", 20, "bold"), fg="#ECF0F1", bg="#0F3460",
        ).pack(expand=True)
        tk.Label(
            hdr, text="Setup Wizard", font=("Segoe UI", 10),
            fg="#95A5A6", bg="#0F3460",
        ).place(relx=0.5, rely=0.82, anchor="center")

        # Body
        body = tk.Frame(self.root, bg="#1A1A2E", padx=32, pady=18)
        body.pack(fill="both", expand=True)

        tk.Label(
            body, text="Install to:", font=("Segoe UI", 11),
            fg="#ECF0F1", bg="#1A1A2E",
        ).pack(anchor="w")

        row = tk.Frame(body, bg="#1A1A2E")
        row.pack(fill="x", pady=(4, 0))

        self.dir_entry = tk.Entry(
            row, textvariable=self.install_dir,
            font=("Segoe UI", 10), bg="#16213E", fg="#ECF0F1",
            insertbackground="white", relief="flat", bd=6, width=44,
        )
        self.dir_entry.pack(side="left", padx=(0, 8))

        tk.Button(
            row, text="Browse…", font=("Segoe UI", 10),
            bg="#533483", fg="white", relief="flat", padx=10,
            cursor="hand2", command=self._browse,
        ).pack(side="left")

        # Separator
        tk.Frame(body, bg="gray30", height=1).pack(fill="x", pady=16)

        # Options
        for var, label in [
            (self.desktop_var, "Create Desktop shortcut"),
            (self.startmenu_var, "Create Start Menu shortcut"),
        ]:
            tk.Checkbutton(
                body, text=label, variable=var,
                font=("Segoe UI", 11), fg="#ECF0F1", bg="#1A1A2E",
                selectcolor="#0F3460", activebackground="#1A1A2E",
                activeforeground="#ECF0F1",
            ).pack(anchor="w", pady=2)

        # Status
        tk.Frame(body, bg="gray30", height=1).pack(fill="x", pady=14)
        self.status_lbl = tk.Label(
            body, textvariable=self.status_var,
            font=("Segoe UI", 10), fg="#95A5A6", bg="#1A1A2E",
        )
        self.status_lbl.pack(anchor="w")

        # Progress bar
        pf = tk.Frame(body, bg="#16213E", height=7)
        pf.pack(fill="x", pady=(6, 0))
        self._prog_outer = pf
        self._prog_bar = tk.Frame(pf, bg="#E94560", height=7, width=0)
        self._prog_bar.place(x=0, y=0)

        # Footer buttons
        footer = tk.Frame(self.root, bg="#16213E", padx=24, pady=14)
        footer.pack(fill="x", side="bottom")

        tk.Button(
            footer, text="Cancel", font=("Segoe UI", 11),
            bg="gray35", fg="white", relief="flat", padx=14, pady=6,
            cursor="hand2", command=self.root.destroy,
        ).pack(side="right", padx=(8, 0))

        self._install_btn = tk.Button(
            footer, text="Install  →", font=("Segoe UI", 11, "bold"),
            bg="#E94560", fg="white", relief="flat", padx=20, pady=6,
            cursor="hand2", command=self._start_install,
        )
        self._install_btn.pack(side="right")

    # ── Actions ─────────────────────────────────────────────────────────────
    def _browse(self):
        folder = filedialog.askdirectory(
            title="Choose install location",
            initialdir=str(Path(self.install_dir.get()).parent),
        )
        if folder:
            self.install_dir.set(str(Path(folder) / "Bank Statement Agent"))

    def _start_install(self):
        self._install_btn.configure(state="disabled", text="Installing…")
        threading.Thread(target=self._do_install, daemon=True).start()

    def _status(self, msg, color="#2ECC71"):
        self.root.after(0, lambda: [
            self.status_var.set(msg),
            self.status_lbl.configure(fg=color),
        ])

    def _progress(self, pct):
        def _apply():
            w = int(self._prog_outer.winfo_width() * pct)
            self._prog_bar.configure(width=max(w, 1))
        self.root.after(0, _apply)

    def _do_install(self):
        try:
            dest = Path(self.install_dir.get())

            self._status("Creating install folder…", "#F39C12")
            self._progress(0.1)
            dest.mkdir(parents=True, exist_ok=True)

            # Copy EXE
            self._status("Copying application…", "#F39C12")
            self._progress(0.3)
            src_exe = _bundled("BankStatementAgent.exe")
            if not src_exe.exists():
                raise FileNotFoundError(
                    f"Bundled EXE not found at {src_exe}.\n"
                    "Please rebuild with build_setup.bat first."
                )
            dest_exe = dest / "BankStatementAgent.exe"
            shutil.copy2(src_exe, dest_exe)
            self._progress(0.55)

            # Copy icon
            src_ico = _bundled("icon.ico")
            dest_ico = None
            if src_ico.exists():
                shutil.copy2(src_ico, dest / "icon.ico")
                dest_ico = dest / "icon.ico"

            # Desktop shortcut
            if self.desktop_var.get():
                self._status("Creating Desktop shortcut…", "#F39C12")
                _create_shortcut_ps(
                    dest_exe,
                    Path.home() / "Desktop" / "Bank Statement Agent.lnk",
                    dest_ico,
                )
            self._progress(0.75)

            # Start Menu shortcut
            if self.startmenu_var.get():
                self._status("Creating Start Menu entry…", "#F39C12")
                sm = (
                    Path.home()
                    / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs"
                )
                _create_shortcut_ps(
                    dest_exe,
                    sm / "Bank Statement Agent.lnk",
                    dest_ico,
                )
            self._progress(1.0)
            self._status("✅  Installation complete!", "#2ECC71")

            # Offer to launch
            self.root.after(400, self._offer_launch, dest_exe)

        except Exception as exc:
            self._status(f"❌  {exc}", "#E74C3C")
            self.root.after(
                0,
                lambda: self._install_btn.configure(
                    state="normal", text="Install  →"
                ),
            )

    def _offer_launch(self, dest_exe: Path):
        launch = messagebox.askyesno(
            "Installation Complete",
            f"Installed to:\n{dest_exe.parent}\n\nLaunch Bank Statement Agent now?",
            parent=self.root,
        )
        if launch:
            subprocess.Popen([str(dest_exe)])
        self.root.destroy()


# ── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    InstallerApp()
