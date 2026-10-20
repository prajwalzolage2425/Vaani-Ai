@echo off
title VaaniAI Server
cd /d "%~dp0"
echo Starting VaaniAI Sanskrit Phonetics System...
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app.py
) else (
    echo Virtual environment not found. Trying py launcher...
    py -3 app.py
)
pause
