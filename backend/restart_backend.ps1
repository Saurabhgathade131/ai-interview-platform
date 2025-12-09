# Force kill any existing backend processes and restart with fresh config
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "🔄 RESTARTING BACKEND WITH FRESH CONFIG" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Kill any existing uvicorn processes
Write-Host "🛑 Stopping existing backend processes..." -ForegroundColor Yellow
Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force
Start-Sleep -Seconds 2

# Verify configuration
Write-Host "`n✅ Checking configuration..." -ForegroundColor Green
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)
python check_config.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Configuration check failed!" -ForegroundColor Red
    Write-Host "Please fix the .env file and try again.`n" -ForegroundColor Red
    exit 1
}

# Start backend
Write-Host "`n🚀 Starting backend server..." -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop`n" -ForegroundColor Gray

# Force reload environment variables
$env:JUDGE0_ENDPOINT = "https://judge0-ce.p.rapidapi.com"
$env:JUDGE0_API_KEY = "eb221c4311msh53b70140df9f90cp133f68jsnd8e67ecd95d8"
$env:USE_LOCAL_LLM = "False"

uvicorn app.main:socket_app --reload --host 0.0.0.0 --port 8000
