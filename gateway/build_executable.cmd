@echo off
REM ===================================================
REM Build Radix PyQt5 Gateway Executable with PyInstaller
REM ===================================================

REM Set working directory to the folder where this script is located
cd /d %~dp0

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Set variables
SET SCRIPT_NAME=gateway.py
SET ICON_PATH=assets/logo.ico
SET ADD_DATA=assets;assets

REM Run PyInstaller
pyinstaller --onefile --windowed --icon=%ICON_PATH% --add-data "%ADD_DATA%" %SCRIPT_NAME%

REM Deactivate virtual environment
deactivate

REM Inform user
echo.
echo Build complete! Check the 'dist' folder for the executable.
echo Press any key to exit...
pause > nul
