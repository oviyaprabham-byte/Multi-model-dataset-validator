@echo off
setlocal EnableDelayedExpansion
title DataValidator — Startup

echo.
echo  ╔═══════════════════════════════════════╗
echo  ║    DataValidator ML Quality Suite     ║
echo  ║    Starting Application...            ║
echo  ╚═══════════════════════════════════════╝
echo.

:: ── Paths ──────────────────────────────────────────────────────────────────
set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"
set "VENV=%BACKEND%\venv"

:: ── Check Python ──────────────────────────────────────────────────────────
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] Python not found. Install Python 3.9+ and add to PATH.
    pause
    exit /b 1
)

:: ── Check Node.js ─────────────────────────────────────────────────────────
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] Node.js not found. Install Node.js 18+ and add to PATH.
    pause
    exit /b 1
)

:: ── Create virtual environment if missing ─────────────────────────────────
if not exist "%VENV%" (
    echo  [1/4] Creating Python virtual environment...
    python -m venv "%VENV%"
    if %ERRORLEVEL% NEQ 0 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo        Done.
) else (
    echo  [1/4] Virtual environment found.
)

:: ── Install backend dependencies if needed ────────────────────────────────
if not exist "%VENV%\Lib\site-packages\fastapi" (
    echo  [2/4] Installing backend dependencies (this may take a few minutes)...
    call "%VENV%\Scripts\pip.exe" install -r "%BACKEND%\requirements.txt" --quiet
    if %ERRORLEVEL% NEQ 0 (
        echo  [ERROR] Failed to install backend dependencies.
        pause
        exit /b 1
    )
    echo        Done.
) else (
    echo  [2/4] Backend dependencies already installed.
)

:: ── Install frontend dependencies if needed ───────────────────────────────
if not exist "%FRONTEND%\node_modules" (
    echo  [3/4] Installing frontend dependencies (this may take a moment)...
    pushd "%FRONTEND%"
    call npm install --silent
    popd
    if %ERRORLEVEL% NEQ 0 (
        echo  [ERROR] Failed to install frontend dependencies.
        pause
        exit /b 1
    )
    echo        Done.
) else (
    echo  [3/4] Frontend dependencies already installed.
)

:: ── Launch apps ──────────────────────────────────────────────────────────
echo  [4/4] Starting servers...
echo.

start "DataValidator — Backend (port 8000)" cmd /k "cd /d "%BACKEND%" && "%VENV%\Scripts\python.exe" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 2 /nobreak >nul

start "DataValidator — Frontend (port 5173)" cmd /k "cd /d "%FRONTEND%" && npm run dev"

timeout /t 3 /nobreak >nul

:: ── Open browser ──────────────────────────────────────────────────────────
start "" "http://localhost:5173"

echo.
echo  ╔═══════════════════════════════════════╗
echo  ║  ✓  Both servers are starting up!    ║
echo  ║                                       ║
echo  ║  Frontend : http://localhost:5173     ║
echo  ║  Backend  : http://localhost:8000     ║
echo  ║  API Docs : http://localhost:8000/docs║
echo  ╚═══════════════════════════════════════╝
echo.
echo  Two terminal windows have opened for the servers.
echo  Close those windows to stop the application.
echo.
pause
