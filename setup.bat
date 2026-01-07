@echo off
setlocal
title Runix Platform Setup & Launcher

echo ========================================================
echo       RUNIX WORKLOAD INTELLIGENCE - EASY SETUP
echo ========================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ and try again.
    pause
    exit /b
)
echo [OK] Python found.

:: 2. Install Dependencies
echo.
echo [1/4] Installing Required Libraries...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b
)

:: 3. Configure Gemini AI Key
echo.
echo [2/4] Configuring AI Engine...
if "%GEMINI_API_KEY%"=="" (
    echo [ERROR] GEMINI_API_KEY is not set.
    echo Please set it using: set GEMINI_API_KEY=your_key_here
    echo or run: $env:GEMINI_API_KEY='your_key_here' in PowerShell
    pause
    exit /b
) else (
    echo [INFO] Using configured GEMINI_API_KEY.
)

:: 4. Cloud Authentication (For Live Mode)
echo.
echo [3/4] Checking Cloud Authentication...
call gcloud auth print-access-token >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Not authenticated with Google Cloud.
    echo [INFO] Launching login browser...
    call gcloud auth application-default login
) else (
    echo [OK] Google Cloud Authentication active.
)

:: 5. Launch Server
echo.
echo [4/4] Starting Runix Dashboard...
echo.
echo ========================================================
echo    DASHBOARD IS READY!
echo    Opening http://localhost:8080
echo ========================================================
echo.

start http://localhost:8080

:: Run server with the API key set
set GEMINI_API_KEY=%GEMINI_API_KEY%
python local_server.py

pause
