@echo off
setlocal

:: ----------------------------------------------------
:: Set current directory to the location of this script
:: This ensures that 'cd backend', 'cd gateway', etc., work regardless
:: of where the user executes the script from.
:: ----------------------------------------------------
cd /d "%~dp0"

:: ----------------------------------------------------
:: PARAMETER CHECK: Check if the "headless" argument is provided
:: ----------------------------------------------------
SET GATEWAY_SCRIPT=gateway.py
IF /I "%1"=="headless" (
SET GATEWAY_SCRIPT=gateway_headless.py
echo [INFO] Running gateway in HEADLESS mode.
) ELSE (
echo [INFO] Running gateway in default mode. To use headless mode, run: start_system.cmd headless
)

echo.
echo ====================================================
echo                STARTING SERVICES
echo ====================================================

:: ----------------------------------------------------
:: 1. START BACKEND SERVICE (Uvicorn)
::    (Launches in a new console window)
:: ----------------------------------------------------
echo [1/3] Starting Backend (Uvicorn) in a new window...
start "Backend Server" cmd /k "cd backend && call .venv\Scripts\activate.bat && uvicorn api:app --reload"

:: ----------------------------------------------------
:: 2. START GATEWAY SERVICE (Python)
::    (Launches in a new console window)
:: ----------------------------------------------------
echo [2/3] Starting Gateway (%GATEWAY_SCRIPT%) in a new window...
start "Gateway Service" cmd /k "cd gateway && call .venv\Scripts\activate.bat && python %GATEWAY_SCRIPT%"

:: ----------------------------------------------------
:: 3. BUILD AND START FRONTEND PREVIEW
::    (Build runs in current window, preview launches in new window)
:: ----------------------------------------------------

echo [INFO] Switching to frontend directory...
cd frontend

echo [3/3] Running pnpm build (this may take a moment)...
call pnpm build

echo [3/3] Starting Frontend Preview in a new window...
start "Frontend Preview" cmd /k "pnpm preview"

:: Switch back to the root directory
cd ..

echo.
echo ====================================================
echo                LAUNCH COMPLETE
echo ====================================================
echo Check the three newly opened windows for service status and logs.
echo Press any key to close this launcher script window...
pause >nul

endlocal