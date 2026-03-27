; ============================================================
; installer.iss  —  Inno Setup script for Bank Statement Agent
; Download Inno Setup from: https://jrsoftware.org/isdl.php
; Then run:  ISCC.exe installer.iss
; ============================================================

#define AppName      "Bank Statement Agent"
#define AppVersion   "1.0.0"
#define AppPublisher "EmailAutomate"
#define AppExeName   "BankStatementAgent.exe"
#define AppId        "{{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppSupportURL=https://github.com/
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=installer_output
OutputBaseFilename=BankStatementAgent_Setup_v{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
; Allow install without admin (user-level)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
WizardStyle=modern
DisableProgramGroupPage=auto
; Show "Allow user to choose" install dir page
DisableDirPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; Desktop shortcut is CHECKED by default
Name: "desktopicon";  Description: "Create a &Desktop shortcut";  GroupDescription: "Additional icons:"; Flags: checkedonce
Name: "startmenu";    Description: "Create a &Start Menu shortcut"; GroupDescription: "Additional icons:"; Flags: checkedonce

[Files]
; Main executable (built by PyInstaller — run build_exe.bat first)
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; App icon for shortcuts
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu
Name: "{group}\{#AppName}";           Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
; Desktop shortcut (only if task selected — default: yes)
Name: "{commondesktop}\{#AppName}";   Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon
; Start Menu shortcut
Name: "{userstartmenu}\{#AppName}";   Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: startmenu

[Run]
; Offer to launch app after install
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName} now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove app data files on uninstall
Type: filesandordirs; Name: "{app}\config.json"
Type: filesandordirs; Name: "{app}\token.json"
Type: filesandordirs; Name: "{app}\processed_emails.json"
Type: filesandordirs; Name: "{app}\hash_db.json"
Type: filesandordirs; Name: "{app}\logs.txt"
Type: filesandordirs; Name: "{app}\credentials.json"
