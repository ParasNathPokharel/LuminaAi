@echo off
title Lumina AI Background Remover - Production Server
color 0B

echo ==============================================================================
echo    Lumina AI Background Remover - Windows Production Server
echo ==============================================================================

cd /d "%~dp0"

REM 1. Activate Virtual Environment
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found at %~dp0venv
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

REM 2. Run Database Migrations
echo [1/3] Verifying and applying database schema...
python -m backend.migrations
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Database migration failed!
    pause
    exit /b 1
)

REM 3. Launch Waitress Production WSGI Server
echo [2/3] Starting multi-threaded production WSGI server on port 5000...
echo Access the live application at: http://127.0.0.1:5000
echo.
python -m waitress --port=5000 --threads=8 backend.app:app

pause
