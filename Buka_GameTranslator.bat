@echo off
title GameTranslator ID
cd /d "%~dp0"

if not exist "%~dp0python_env\python.exe" (
    echo [ERROR] Environment Python tidak ditemukan!
    echo Pastikan folder python_env berada di folder yang sama.
    pause
    exit /b 1
)

if exist "%~dp0python_env\pythonw.exe" (
    start "" "%~dp0python_env\pythonw.exe" "%~dp0app.py"
) else (
    start "" "%~dp0python_env\python.exe" "%~dp0app.py"
)
exit
