# PowerShell launcher for VaaniAI
Set-Location $PSScriptRoot
Write-Host "Starting VaaniAI Sanskrit Phonetics System..." -ForegroundColor Green
if (Test-Path ".\.venv\Scripts\python.exe") {
    & ".\.venv\Scripts\python.exe" app.py
} else {
    Write-Host "Virtual environment not found, attempting py launcher..." -ForegroundColor Yellow
    py -3 app.py
}
