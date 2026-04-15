; Script pour Inno Setup - TelVid-Vizane
; © 2026, Vital Zagabe Néophite — VIZANE

#define MyAppName "TelVid-Vizane"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Vital Zagabe Néophite (VIZANE)"
#define MyAppURL "https://github.com/Ir-vital/telvid-vizane"
#define MyAppExeName "TelVid-Vizane.exe"

[Setup]
; NOTE: L'AppId est un identifiant unique pour votre application.
; Utilisez un nouveau GUID pour chaque application. Vous pouvez en générer un ici : https://www.guidgenerator.com/
AppId={{A49F24E4-4446-4B3A-A824-7E7A63F335D5}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Affiche le fichier de licence pendant l'installation. Assurez-vous que le fichier LICENSE.txt est présent.
LicenseFile=LICENSE.txt
OutputBaseFilename=TelVid-Vizane_Setup_v{#MyAppVersion}
SetupIconFile=icons\logo-telvid.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Si votre application crée des fichiers dans son répertoire, vous devrez peut-être ajouter des permissions.

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
