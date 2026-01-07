@echo off
setlocal
title Runix Platform Setup & Launcher

echo ========================================================
echo       RUNIX WORKLOAD INTELLIGENCE - EASY SETUP
echo ========================================================
echo.

:MENU
echo How would you like to run Runix?
echo.
echo [1] Run Locally (Python) 
echo     - Best for LIVE Analysis of Cloud Run services
echo     - Requires Python 3.10+
echo.
echo [2] Run in Docker
echo     - Best for MOCK Demo and hygiene
echo     - Requires Docker Desktop
echo.
set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" goto LOCAL
if "%choice%"=="2" goto DOCKER
echo Invalid choice. Please try again.
goto MENU

:LOCAL
echo.
echo [LOG] Selected: LOCAL RUN
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

:: Run server
python local_server.py
pause
exit /b

:DOCKER
echo.
echo [LOG] Selected: DOCKER RUN
echo.

:: 1. Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not running.
    echo Please install Docker Desktop.
    pause
    exit /b
)
echo [OK] Docker found.

:: 2. Configure API Key
if "%GEMINI_API_KEY%"=="" (
    echo [ERROR] GEMINI_API_KEY is not set.
    echo Please set it in your environment before running this script.
    pause
    exit /b
)

:: 3. Build Image
echo.
echo [1/2] Building Docker Image (this may take a minute)...
docker build -t runix .
if %errorlevel% neq 0 (
    echo [ERROR] Docker build failed.
    pause
    exit /b
)

:: 4. Run Container
echo.
echo [2/2] Starting Container...
echo.
echo ========================================================
echo    DASHBOARD IS READY!
echo    Opening http://localhost:8080
echo ========================================================
echo.

start http://localhost:8080
docker run -it --rm -p 8080:8080 -e GEMINI_API_KEY=%GEMINI_API_KEY% runix

pause
