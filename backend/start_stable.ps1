# Restart script using the stable no-reload server
Write-Host "Stopping existing Python processes..."
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host "Starting stable server (0.0.0.0:8000)..."
$env:PYTHONPATH = "c:\AI Interview\ai-interview-platform\backend"
python run_server_no_reload.py
