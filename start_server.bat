@echo off
setlocal enabledelayedexpansion
title Lumina AI Background Remover Studio
cd /d "%~dp0"

echo ======================================================================
echo           Lumina AI - Next-Gen Background Remover Studio
echo ======================================================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in %~dp0venv!
    echo Please create the virtual environment first:
    echo   python -m venv venv
    echo   venv\Scripts\pip install -r backend\requirements.txt
    pause
    exit /b 1
)

echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

echo [2/3] Starting AI Background Remover Flask server on http://127.0.0.1:5000...
start "" "http://127.0.0.1:5000"

echo [3/3] Running Python Backend...
venv\Scripts\python.exe backend\app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Server encountered an error.
    pause
)
