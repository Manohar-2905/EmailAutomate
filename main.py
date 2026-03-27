"""
main.py — Entry point for Bank Statement Agent

Usage:
  python main.py            → Launch GUI
  python main.py --headless → Run automation headlessly (called by Task Scheduler)
"""

import sys


def _install_deps_if_needed():
    """Silently install any missing packages before importing the rest."""
    import importlib, subprocess
    REQUIRED = {
        "customtkinter":               "customtkinter",
        "googleapiclient":             "google-api-python-client",
        "google.auth":                 "google-auth",
        "google_auth_oauthlib":        "google-auth-oauthlib",
        "google.auth.transport":       "google-auth-httplib2",
        "schedule":                    "schedule",
        "PIL":                         "Pillow",
    }
    missing = []
    for module, pkg in REQUIRED.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"Installing missing packages: {missing}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + missing
        )
        print("Installation complete.")


if __name__ == "__main__":
    _install_deps_if_needed()

    if "--headless" in sys.argv:
        from scheduler import run_headless
        run_headless()
    else:
        from ui import launch_app
        launch_app()
