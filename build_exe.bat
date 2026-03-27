@echo off
:: ============================================================
:: build_exe.bat  —  Build Bank Statement Agent as a .EXE
:: Run this from the project root: bank-automation\
:: Requires:  pip install pyinstaller
:: ============================================================

echo.
echo ====================================================
echo  Bank Statement Agent — EXE Builder
echo ====================================================
echo.

:: Install PyInstaller if not present
pip show pyinstaller >nul 2>&1
IF ERRORLEVEL 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

:: Clean previous build
IF EXIST dist    rmdir /s /q dist
IF EXIST build   rmdir /s /q build
IF EXIST bank_agent.spec del /q bank_agent.spec

:: ── PyInstaller command ──────────────────────────────────
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
    echo [ERROR] Build failed. See above for details.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo  SUCCESS!  EXE is at:  dist\BankStatementAgent.exe
echo ====================================================
echo.
pause
