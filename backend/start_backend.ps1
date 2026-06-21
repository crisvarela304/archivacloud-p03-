# start_backend.ps1
Set-Location $PSScriptRoot
Write-Host 'ArchivaCloud backend en http://localhost:8000' -ForegroundColor Cyan
.\.venv\Scripts\uvicorn.exe main:app --reload --port 8000
