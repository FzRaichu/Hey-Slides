@echo off
pushd "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Python environment missing. Follow README.md setup instructions.
    pause
    popd
    exit /b 1
)
".venv\Scripts\python.exe" -m app.main
if errorlevel 1 pause
popd
