@echo off
setlocal EnableExtensions

REM Inner Garden quick start script for Windows cmd/PowerShell.
REM In PowerShell, run this file as: .\start.bat
REM This ASCII block intentionally runs before the legacy localized block below.

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"
set "LOG_DIR=%PROJECT_ROOT%\logs"
set "FLAG_FILE=%BACKEND_DIR%\.installed"

echo.
echo Inner Garden starting...
echo Project root: %PROJECT_ROOT%
echo.

if not exist "%BACKEND_DIR%" (
    echo ERROR: Backend directory not found: %BACKEND_DIR%
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%" (
    echo ERROR: Frontend directory not found: %FRONTEND_DIR%
    pause
    exit /b 1
)

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py"
) else (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo ERROR: Python was not found. Install Python first: https://www.python.org/
    pause
    exit /b 1
)

set "NPM_CMD="
where npm.cmd >nul 2>nul
if not errorlevel 1 (
    set "NPM_CMD=npm.cmd"
) else (
    where npm >nul 2>nul
    if not errorlevel 1 set "NPM_CMD=npm"
)

if not defined NPM_CMD (
    echo ERROR: npm was not found. Install Node.js first: https://nodejs.org/
    pause
    exit /b 1
)

if "%~1"=="--check" (
    echo Check OK.
    echo Python command: %PYTHON_CMD%
    echo npm command: %NPM_CMD%
    echo Backend: %BACKEND_DIR%
    echo Frontend: %FRONTEND_DIR%
    exit /b 0
)

if exist "%FLAG_FILE%" (
    if exist "%BACKEND_DIR%\venv\Scripts\activate.bat" (
        if exist "%FRONTEND_DIR%\node_modules" (
            echo Dependencies already installed. Starting services...
            goto IG_START_SERVICES
        )
    )
)

echo First run or dependencies missing. Setting up environment...
echo.

echo [1/4] Creating backend virtual environment...
if not exist "%BACKEND_DIR%\venv\Scripts\activate.bat" (
    %PYTHON_CMD% -m venv "%BACKEND_DIR%\venv"
    if errorlevel 1 (
        echo ERROR: Failed to create backend virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Backend virtual environment already exists.
)

echo [2/4] Installing backend dependencies...
call "%BACKEND_DIR%\venv\Scripts\activate.bat"
python -m pip install -q -r "%BACKEND_DIR%\requirements.txt"
if errorlevel 1 (
    echo ERROR: Failed to install backend dependencies.
    pause
    exit /b 1
)

echo [3/4] Checking backend .env...
if not exist "%BACKEND_DIR%\.env" (
    if exist "%BACKEND_DIR%\.env.example" (
        copy "%BACKEND_DIR%\.env.example" "%BACKEND_DIR%\.env" >nul
        echo Created backend .env from .env.example. Please configure API keys if needed.
    ) else (
        echo WARNING: backend .env and .env.example were not found.
    )
)

echo [4/4] Installing frontend dependencies...
cd /d "%FRONTEND_DIR%"
call %NPM_CMD% install --silent --no-audit --no-fund
if errorlevel 1 (
    echo ERROR: Failed to install frontend dependencies.
    pause
    exit /b 1
)

type nul > "%FLAG_FILE%"
echo Setup complete.
echo.

:IG_START_SERVICES
echo Starting backend and frontend in separate windows...
echo.

cd /d "%BACKEND_DIR%"
start "Inner Garden Backend" cmd /k "call venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

cd /d "%FRONTEND_DIR%"
start "Inner Garden Frontend" cmd /k "%NPM_CMD% run dev"

timeout /t 2 /nobreak >nul

echo ========================================
echo Inner Garden started
echo ========================================
echo Backend API:   http://localhost:8000
echo API docs:      http://localhost:8000/docs
echo Frontend UI:   http://localhost:5173
echo.
echo Close the backend/frontend windows to stop services.
echo.
pause
exit /b 0
