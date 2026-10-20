@echo off
title VaaniAI Database Seeder
cd /d "%~dp0"
echo Seeding VaaniAI Database...
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" seed\seed.py
) else (
    py -3 seed\seed.py
)
pause
