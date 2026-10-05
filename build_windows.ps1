param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    throw "Python 3 was not found. Install Python 3.10+ and try again."
}

$pythonLauncher = Get-PythonCommand

if ($Clean -and (Test-Path ".venv")) {
    Remove-Item ".venv" -Recurse -Force
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    if ($pythonLauncher.Count -eq 2) {
        & $pythonLauncher[0] $pythonLauncher[1] -m venv .venv
    } else {
        & $pythonLauncher[0] -m venv .venv
    }
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Write-Host "Installing build dependencies..."
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt
& $python -m pip install --upgrade pyinstaller

Write-Host "Building YouTube2Audio.exe..."
& $python -m PyInstaller --noconfirm --clean --onefile --windowed --name "YouTube2Audio" --collect-all yt_dlp --collect-all imageio_ffmpeg --add-data "img;img" main.py

Write-Host ""
Write-Host "Build complete:"
Write-Host (Join-Path $PSScriptRoot "dist\YouTube2Audio.exe")
