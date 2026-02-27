[Setup]
AppName=ZEMPERvideos
AppVersion=1.0.0
DefaultDirName={pf}\ZEMPERvideos
DefaultGroupName=ZEMPERvideos
OutputDir=installer
OutputBaseFilename=ZEMPERvideos_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos"

[Files]
Source: "..\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs; Excludes: ".git*;venv*;output*;dist*;build*;__pycache__*;installer*;credentials*;*.mp4;*.gif;*.zip;*.exe;*.msi"

[Icons]
Name: "{group}\ZEMPERvideos"; Filename: "{app}\scripts\run_app.cmd"; WorkingDir: "{app}"
Name: "{commondesktop}\ZEMPERvideos"; Filename: "{app}\scripts\run_app.cmd"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\install_windows.ps1"""; StatusMsg: "Instalando dependencias (Python, FFmpeg, ngrok)..."; Flags: waituntilterminated
