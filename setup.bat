@echo off
REM ===================================================================
REM  Fitness & Workout Progress Tracker - one-command setup (Windows)
REM  Creates a venv, installs pinned deps, seeds the demo DB, and runs
REM  the Streamlit app. Just double-click this file or run: setup.bat
REM ===================================================================

setlocal
cd /d "%~dp0"

echo.
echo [1/4] Locating Python...
where py >nul 2>&1
if %errorlevel%==0 (
    set "PY=py"
) else (
    where python >nul 2>&1
    if %errorlevel%==0 (
        set "PY=python"
    ) else (
        echo ERROR: Python was not found. Install Python 3.9+ from https://python.org
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
)

echo [2/4] Creating virtual environment (.venv)...
if not exist ".venv" (
    %PY% -m venv .venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo [3/4] Installing pinned dependencies...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
call ".venv\Scripts\python.exe" -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo [4/4] Seeding demo data (idempotent - safe to re-run)...
call ".venv\Scripts\python.exe" seed.py

echo.
echo ===================================================================
echo  Setup complete! Launching the app in your browser...
echo  (Press Ctrl+C in this window to stop the app.)
echo ===================================================================
echo.
call ".venv\Scripts\python.exe" -m streamlit run app.py

endlocal
