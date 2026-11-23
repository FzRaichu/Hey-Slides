# Build a portable Windows folder: dist\HeySlides\HeySlides.exe
#
# Prerequisites (run once from the repository root):
#   py -3.12 -m venv .venv
#   & .\.venv\Scripts\python.exe -m pip install -r requirements-prototype.txt -r requirements-build.txt
#   & .\.venv\Scripts\python.exe -m scripts.download_model
#
# Then build:
#   powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Missing .venv. Create it first (see the comment at the top of this script)."
}

$modelName = "vosk-model-small-en-us-0.15"
$modelSource = Join-Path $root "models\$modelName"
if (-not (Test-Path (Join-Path $modelSource "am\final.mdl"))) {
    throw "Missing model at $modelSource. Run: .venv\Scripts\python.exe -m scripts.download_model"
}

# PyInstaller --noconfirm empties dist\HeySlides, including recordings and session
# logs the exe wrote to dist\HeySlides\logs. Keep them outside and restore after.
$distLogs = Join-Path $root "dist\HeySlides\logs"
$savedLogs = Join-Path $root "dist\HeySlides-logs-kept"
if ((Test-Path $distLogs) -and (Get-ChildItem $distLogs -Force | Select-Object -First 1)) {
    if (Test-Path $savedLogs) { throw "$savedLogs already exists from an earlier build. Move its files back or away first." }
    Write-Host "Keeping exe logs/recordings: $distLogs -> $savedLogs"
    Move-Item $distLogs $savedLogs
}

Write-Host "Running PyInstaller..."
& $python -m PyInstaller `
    --noconfirm --clean `
    --onedir --windowed `
    --name HeySlides `
    --collect-binaries vosk `
    --collect-data customtkinter `
    --hidden-import win32com.client `
    --exclude-module faster_whisper `
    --exclude-module ctranslate2 `
    --exclude-module torch `
    voice_slide_control.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE (exe logs, if any, are in $savedLogs)" }

$dist = Join-Path $root "dist\HeySlides"
$modelTarget = Join-Path $dist "models\$modelName"
Write-Host "Copying model to $modelTarget ..."
New-Item -ItemType Directory -Force (Split-Path $modelTarget) | Out-Null
if (Test-Path $modelTarget) { Remove-Item -Recurse -Force $modelTarget }
Copy-Item -Recurse $modelSource $modelTarget

@"
Hey Slides (Voice Slide Control) - portable build

1. Extract this whole folder (do not run the .exe from inside the zip).
2. Double-click HeySlides.exe.
3. Keep the "models" and "_internal" folders next to the .exe.
4. Session logs and WAV recordings are written to the "logs" folder here.

Needs Windows 10/11 and a microphone. No Python or internet required.
PowerPoint control needs desktop Microsoft PowerPoint with a running slideshow (F5).
"@ | Set-Content -Encoding utf8 (Join-Path $dist "README.txt")

$zip = Join-Path $root "dist\HeySlides-win64.zip"
if (Test-Path $zip) { Remove-Item -Force $zip }
Write-Host "Creating $zip ..."
Compress-Archive -Path $dist -DestinationPath $zip

# Restore only after zipping, so personal recordings never go into the shared zip.
if (Test-Path $savedLogs) {
    Move-Item $savedLogs $distLogs
    Write-Host "Restored exe logs/recordings to $distLogs (not included in the zip)"
}

$sizeMb = [math]::Round((Get-Item $zip).Length / 1MB, 1)
Write-Host "Done. Folder: $dist"
Write-Host "Zip: $zip ($sizeMb MB)"
