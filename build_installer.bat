@echo off
:: ============================================================
:: build_installer.bat — One-click: Build EXE + Installer
:: Run this from the project root: EmailAutomate\
:: Requires: PyInstaller (auto-installed) + Inno Setup
:: Inno Setup download: https://jrsoftware.org/isdl.php
:: ============================================================

echo.
echo ====================================================
echo  Bank Statement Agent — Full Installer Builder
echo ====================================================
echo.

:: ── STEP 1: Build the EXE with PyInstaller ────────────────
echo [1/2] Building EXE with PyInstaller...
echo.

pip show pyinstaller >nul 2>&1
IF ERRORLEVEL 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

IF EXIST dist    rmdir /s /q dist
IF EXIST build   rmdir /s /q build
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
    echo [ERROR] PyInstaller build failed. See above for details.
    pause
    exit /b 1
)

echo.
echo [OK] EXE built successfully: dist\BankStatementAgent.exe

:: ── STEP 2: Build the Installer with Inno Setup ───────────
echo.
echo [2/2] Building installer with Inno Setup...
echo.

IF EXIST installer_output rmdir /s /q installer_output

:: Try common Inno Setup install locations
SET ISCC=""
IF EXIST "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" SET ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
IF EXIST "C:\Program Files\Inno Setup 6\ISCC.exe"       SET ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
IF EXIST "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" SET ISCC="C:\Program Files (x86)\Inno Setup 5\ISCC.exe"

IF %ISCC%=="" (
    echo.
    echo [WARNING] Inno Setup not found.
    echo  Please install it from: https://jrsoftware.org/isdl.php
    echo  Then re-run this script.
    echo.
    echo  Your EXE is ready at: dist\BankStatementAgent.exe
    pause
    exit /b 1
)

%ISCC% installer.iss

IF ERRORLEVEL 1 (
    echo.
    echo [ERROR] Installer build failed.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo  SUCCESS!
echo  Installer: installer_output\BankStatementAgent_Setup_v1.0.0.exe
echo  Share this single file with users to install the app.
echo ====================================================
echo.
pause
