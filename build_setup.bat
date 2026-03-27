@echo off
:: ============================================================
:: build_setup.bat  —  Build ONE self-contained Setup EXE
:: No Inno Setup needed. Uses PyInstaller only.
::
:: Output:  dist_setup\BankStatementAgent_Setup.exe
::          → Share this single file. Users double-click to install.
:: ============================================================

echo.
echo ====================================================
echo  Bank Statement Agent — Setup EXE Builder
echo ====================================================
echo.

:: ── Check / install PyInstaller ───────────────────────────
pip show pyinstaller >nul 2>&1
IF ERRORLEVEL 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

:: ── STEP 1: Build the main app EXE ───────────────────────
echo [1/2]  Building main app EXE...
echo.

IF EXIST dist        rmdir /s /q dist
IF EXIST build       rmdir /s /q build
IF EXIST BankStatementAgent.spec del /q BankStatementAgent.spec

pyinstaller ^
  --onefile ^
  --windowed ^
  --name "BankStatementAgent" ^
  --icon "icon.ico" ^
  --add-data "requirements.txt;." ^
  --hidden-import customtkinter ^
  --hidden-import googleapiclient ^
  --hidden-import google.auth ^
  --hidden-import google_auth_oauthlib ^
  --hidden-import PIL ^
  --hidden-import imaplib ^
  --hidden-import email ^
  --hidden-import hashlib ^
  --hidden-import schedule ^
  --collect-all customtkinter ^
  main.py

IF ERRORLEVEL 1 (
    echo.
    echo [ERROR] Main app build failed.
    pause & exit /b 1
)

echo.
echo [OK] dist\BankStatementAgent.exe ready.

:: ── STEP 2: Bundle app EXE inside the Setup installer ────
echo.
echo [2/2]  Building Setup installer...
echo.

IF EXIST dist_setup  rmdir /s /q dist_setup
IF EXIST build_setup rmdir /s /q build_setup
IF EXIST BankStatementAgent_Setup.spec del /q BankStatementAgent_Setup.spec

pyinstaller ^
  --onefile ^
  --windowed ^
  --name "BankStatementAgent_Setup" ^
  --icon "icon.ico" ^
  --add-data "dist\BankStatementAgent.exe;." ^
  --add-data "icon.ico;." ^
  --distpath "dist_setup" ^
  --workpath "build_setup" ^
  setup_app.py

IF ERRORLEVEL 1 (
    echo.
    echo [ERROR] Setup EXE build failed.
    pause & exit /b 1
)

echo.
echo ====================================================
echo  SUCCESS!
echo.
echo  Setup file:  dist_setup\BankStatementAgent_Setup.exe
echo.
echo  Share this ONE file with users.
echo  They double-click it to install the app.
echo ====================================================
echo.
pause
