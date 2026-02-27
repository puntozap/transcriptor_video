$ErrorActionPreference = "Stop"

function Write-Step($msg) {
    Write-Host ""
    Write-Host "== $msg =="
}

function Ensure-Admin {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        throw "Este instalador requiere permisos de Administrador."
    }
}

function Add-ToPath([string]$pathToAdd) {
    if (-not $pathToAdd -or -not (Test-Path $pathToAdd)) { return }
    $current = [Environment]::GetEnvironmentVariable("Path", "Machine")
    if (-not $current) { $current = "" }
    if ($current -notmatch [regex]::Escape($pathToAdd)) {
        $newPath = ($current.TrimEnd(";") + ";" + $pathToAdd).Trim(";")
        [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
        $env:Path = $newPath
    }
}

function Get-LatestPythonInstallerUrl {
    $windowsUrl = "https://www.python.org/downloads/windows/"
    $html = (Invoke-WebRequest -Uri $windowsUrl -UseBasicParsing).Content
    $regex = 'https://www\.python\.org/ftp/python/(\d+\.\d+\.\d+)/python-\1-amd64\.exe'
    $matches = [regex]::Matches($html, $regex)
    if ($matches.Count -gt 0) {
        return $matches[0].Value
    }
    $downloadsUrl = "https://www.python.org/downloads/"
    $html2 = (Invoke-WebRequest -Uri $downloadsUrl -UseBasicParsing).Content
    $matches2 = [regex]::Matches($html2, $regex)
    if ($matches2.Count -gt 0) {
        return $matches2[0].Value
    }
    throw "No se pudo detectar la URL del instalador de Python."
}

function Ensure-Python {
    Write-Step "Verificando Python"
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        Write-Host "Python ya instalado: $($pythonCmd.Source)"
        return $pythonCmd.Source
    }

    Write-Step "Descargando Python (ultima version)"
    $pyUrl = Get-LatestPythonInstallerUrl
    $pyInstaller = Join-Path $env:TEMP "python-latest-amd64.exe"
    Invoke-WebRequest -Uri $pyUrl -OutFile $pyInstaller

    Write-Step "Instalando Python"
    $args = "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_launcher=1"
    $proc = Start-Process -FilePath $pyInstaller -ArgumentList $args -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        throw "Instalacion de Python fallo con codigo $($proc.ExitCode)"
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        return $pythonCmd.Source
    }

    $candidate = Get-ChildItem "C:\\Program Files\\Python*\\python.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
    if ($candidate) {
        return $candidate.FullName
    }

    throw "No se encontro python.exe despues de instalar."
}

function Ensure-FFmpeg($installDir) {
    Write-Step "Verificando FFmpeg"
    $ffmpegCmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($ffmpegCmd) {
        Write-Host "FFmpeg ya disponible: $($ffmpegCmd.Source)"
        return
    }

    Write-Step "Descargando FFmpeg (ultima version)"
    $ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    $zipPath = Join-Path $env:TEMP "ffmpeg-release-essentials.zip"
    Invoke-WebRequest -Uri $ffmpegUrl -OutFile $zipPath

    Write-Step "Instalando FFmpeg"
    $toolsDir = Join-Path $installDir "tools"
    $ffmpegDir = Join-Path $toolsDir "ffmpeg"
    New-Item -ItemType Directory -Path $ffmpegDir -Force | Out-Null
    Expand-Archive -Path $zipPath -DestinationPath $ffmpegDir -Force

    $ffmpegRoot = Get-ChildItem $ffmpegDir -Directory | Select-Object -First 1
    if (-not $ffmpegRoot) { throw "No se pudo extraer FFmpeg." }
    $ffmpegBin = Join-Path $ffmpegRoot.FullName "bin"
    Add-ToPath $ffmpegBin
}

function Ensure-Ngrok($installDir) {
    Write-Step "Verificando ngrok"
    $ngrokCmd = Get-Command ngrok -ErrorAction SilentlyContinue
    if ($ngrokCmd) {
        Write-Host "ngrok ya disponible: $($ngrokCmd.Source)"
        return
    }

    Write-Step "Descargando ngrok (ultima version)"
    $ngrokUrl = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
    $zipPath = Join-Path $env:TEMP "ngrok.zip"
    Invoke-WebRequest -Uri $ngrokUrl -OutFile $zipPath

    Write-Step "Instalando ngrok"
    $toolsDir = Join-Path $installDir "tools"
    $ngrokDir = Join-Path $toolsDir "ngrok"
    New-Item -ItemType Directory -Path $ngrokDir -Force | Out-Null
    Expand-Archive -Path $zipPath -DestinationPath $ngrokDir -Force
    Add-ToPath $ngrokDir
}

function Ensure-Venv($installDir, $pythonExe) {
    Write-Step "Creando entorno virtual"
    $venvDir = Join-Path $installDir "venv"
    if (-not (Test-Path $venvDir)) {
        & $pythonExe -m venv $venvDir
    }

    $pipExe = Join-Path $venvDir "Scripts\\pip.exe"
    if (-not (Test-Path $pipExe)) {
        throw "No se encontro pip en el entorno virtual."
    }

    Write-Step "Instalando dependencias"
    & $pipExe install --upgrade pip
    $req = Join-Path $installDir "requirements.txt"
    & $pipExe install -r $req
}

try {
    Ensure-Admin
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $installDir = Split-Path -Parent $scriptDir

    Write-Step "Inicio instalacion ZEMPERvideos"
    Write-Host "Directorio de instalacion: $installDir"

    $pythonExe = Ensure-Python
    Ensure-FFmpeg $installDir
    Ensure-Ngrok $installDir
    Ensure-Venv $installDir $pythonExe

    Write-Step "Instalacion finalizada"
    Write-Host "Puedes ejecutar la app con:"
    Write-Host "  $installDir\\venv\\Scripts\\python.exe $installDir\\app.py"
} catch {
    Write-Error $_
    exit 1
}
