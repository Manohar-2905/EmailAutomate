# 🏦 Bank Statement Agent — Complete Setup Guide

A production-ready Windows desktop application that automatically downloads bank statement PDFs
from multiple Gmail accounts, organises them by user/bank, and optionally backs them up to Google Drive.

---

## 📦 Project Structure

```
bank-automation/
├── main.py                 ← Entry point (GUI + headless)
├── ui.py                   ← Main dashboard (CustomTkinter)
├── setup_wizard.py         ← First-run wizard + dependency installer
├── account_manager.py      ← CRUD for Gmail accounts (config.json)
├── gmail_service.py        ← IMAP email processing
├── drive_service.py        ← Google Drive upload
├── bank_detector.py        ← Detect bank from sender/subject
├── email_tracker.py        ← Idempotent processing (processed_emails.json)
├── hash_manager.py         ← SHA-256 duplicate detection (hash_db.json)
├── automation_runner.py    ← Orchestrates all accounts
├── scheduler.py            ← Windows Task Scheduler integration
├── utils.py                ← Shared helpers (logging, JSON, paths)
├── requirements.txt        ← Python dependencies
├── build_exe.bat           ← PyInstaller build script
├── installer.iss           ← Inno Setup installer script
├── config.json             ← Created at runtime
├── processed_emails.json   ← Created at runtime
├── hash_db.json            ← Created at runtime
└── logs.txt                ← Created at runtime
```

---

## 🚀 Quick Start (Developer)

### 1 — Install Python dependencies

```bash
cd bank-automation
pip install -r requirements.txt
```

### 2 — Run the application

```bash
python main.py
```

On first launch the setup wizard will appear automatically.

---

## 📧 Gmail App Password Setup

Gmail requires an **App Password** (not your regular password) when accessing email via IMAP.

### Steps

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Click **Security** in the left sidebar
3. Under "How you sign in to Google", enable **2-Step Verification** if not already on
4. Search for **App Passwords** (or go to Security → 2-Step Verification → App Passwords)
5. Select app: **Mail** | Select device: **Windows Computer**
6. Click **Generate**
7. Copy the 16-character password (format: `xxxx xxxx xxxx xxxx`)
8. Paste it into the app when adding your account

> ⚠️ If you don't see "App Passwords", your account may be using Advanced Protection or
> the option may be hidden. Make sure 2FA is enabled first.

---

## ☁️ Google Drive API Setup

### Step 1 — Create a Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **New Project** → name it "BankStatementAgent"
3. Click **Create**

### Step 2 — Enable the Drive API

1. In the project, go to **APIs & Services → Library**
2. Search for **Google Drive API** → click **Enable**

### Step 3 — Create OAuth 2.0 Credentials

1. Go to **APIs & Services → Credentials**
2. Click **+ Create Credentials → OAuth client ID**
3. Application type: **Desktop app**
4. Name: "BankStatementAgent"
5. Click **Create**
6. Click **Download JSON** → save as `credentials.json`
7. Place `credentials.json` in the `bank-automation/` folder

### Step 4 — Authorise (first run with Drive enabled)

When you first enable Drive and run automation:
- A browser window will open asking you to sign in to Google
- Grant the requested permissions
- A `token.json` file will be created automatically for future runs

---

## 🖥️ Building the EXE

### Prerequisites

```bash
pip install pyinstaller
```

### Build

```bash
cd bank-automation
build_exe.bat
```

Output: `dist\BankStatementAgent.exe`

> **Note:** If you don't have `icon.ico`, either create one or remove the
> `--icon "icon.ico"` line from `build_exe.bat`.

### What gets bundled

- All Python code and dependencies
- CustomTkinter themes and assets
- The app will auto-install any remaining pip packages on first run

---

## 📀 Creating the Installer (Inno Setup)

### Prerequisites

Download and install [Inno Setup](https://jrsoftware.org/isdl.php) (free).

### Steps

1. Build the EXE first (`build_exe.bat`)
2. Open `installer.iss` in the Inno Setup Compiler
3. Press **F9** (or Build → Compile)
4. Output: `installer_output\BankStatementAgent_Setup_v1.0.0.exe`

The installer will:
- Ask the user where to install
- Create a desktop shortcut (optional)
- Create a Start Menu entry
- Allow clean uninstallation

---

## ⏰ Task Scheduler Setup

The app can register itself with Windows Task Scheduler for daily 9 AM runs.

### Via the UI

1. Open the app
2. Go to **Settings**
3. Under "Daily Scheduler", click **Enable**
4. *(Run the app as Administrator for this step)*

### Manual setup via command line

```bat
schtasks /Create /F /TN "BankStatementAgent" /TR "\"C:\Path\To\BankStatementAgent.exe\" --headless" /SC DAILY /ST 09:00 /RL HIGHEST
```

### Verify

```bat
schtasks /Query /TN "BankStatementAgent"
```

### Remove

```bat
schtasks /Delete /F /TN "BankStatementAgent"
```

---

## ▶️ Manual Run

### Via the UI

Click **🚀 Run Automation** on the Dashboard tab.

### Via command line (GUI mode)

```bash
python main.py
```

### Via command line (headless / no window)

```bash
python main.py --headless
```

---

## 📂 File Organisation

```
C:\BankStatements\           ← Your chosen base folder
├── Prem\
│   ├── HDFC\
│   │   └── statement_20240101.pdf
│   ├── SBI\
│   └── UNKNOWN\
└── Sister\
    ├── ICICI\
    └── AXIS\
```

Google Drive mirrors this structure under a **BankStatements** folder.

---

## 🔒 Duplicate Prevention

### Email-level (processed_emails.json)

Each Gmail `Message-ID` is stored after processing.
Re-running the automation NEVER re-downloads the same email.

### File-level (hash_db.json)

Each PDF's **SHA-256 hash** is stored after saving.
Even if the same attachment arrives in a different email, it will NOT be saved again.

---

## 🏦 Supported Banks

| Label   | Detected via                            |
|---------|-----------------------------------------|
| HDFC    | `hdfcbank`, `hdfc` in sender/subject    |
| SBI     | `sbi`, `onlinesbi`                      |
| ICICI   | `icicibank`, `icici`                    |
| AXIS    | `axisbank`, `axis`                      |
| KOTAK   | `kotak`                                 |
| YES     | `yesbank`                               |
| PNB     | `pnb`, `punjabnational`                 |
| BOB     | `bankofbaroda`, `bob`                   |
| UNKNOWN | None of the above matched               |

To add more banks, edit `bank_detector.py` → `_BANK_RULES`.

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| "Login failed" | Check App Password, ensure IMAP is enabled in Gmail Settings → Forwarding and POP/IMAP |
| Scheduler fails | Run app as Administrator when enabling |
| Drive auth loop | Delete `token.json` and re-authenticate |
| No PDFs found | Check that emails have PDF attachments AND contain keywords: statement, bank statement, etc. |
| App won't start | Run `pip install -r requirements.txt` first |

### Enable IMAP in Gmail

1. Open Gmail → Settings (gear icon) → See all settings
2. Click **Forwarding and POP/IMAP** tab
3. Under IMAP access, select **Enable IMAP**
4. Click **Save Changes**

---

## 📋 config.json Example

```json
{
  "base_folder": "C:\\BankStatements",
  "drive_enabled": false,
  "accounts": [
    {
      "name": "Prem",
      "email": "prem@gmail.com",
      "app_password": "xxxx xxxx xxxx xxxx"
    },
    {
      "name": "Sister",
      "email": "sister@gmail.com",
      "app_password": "yyyy yyyy yyyy yyyy"
    }
  ]
}
```

---

## 🔐 Security Notes

- App passwords are stored in `config.json` — keep this file private
- Do NOT commit `config.json`, `credentials.json`, or `token.json` to version control
- Add them to `.gitignore`

---

## 📄 License

MIT License — free for personal and commercial use.
