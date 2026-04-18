# SagePilot Orchestrator for Windows

Write-Host "🚀 Launching SagePilot Order Supervisor System..." -ForegroundColor Cyan

# Start Temporal Dev Server if not running
$temporalRunning = Get-Process -Name "temporal" -ErrorAction SilentlyContinue
if (-not $temporalRunning) {
    Write-Host "📦 Starting Temporal Local Server..." -ForegroundColor Yellow
    $temporalPath = "temporal"
    if (Test-Path ".\temporal.exe") { $temporalPath = ".\temporal.exe" }
    Start-Process -NoNewWindow -FilePath $temporalPath -ArgumentList "server start-dev"
}

# Start Worker
Write-Host "🤖 Starting Temporal Worker..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python worker.py"

# Start API
Write-Host "🌐 Starting FastAPI Server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; uvicorn main:app --reload --port 8000"

# Start Frontend
Write-Host "💻 Starting Next.js UI..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "`n✅ All components requested. Check new windows for logs." -ForegroundColor Green
Write-Host "API: http://localhost:8000"
Write-Host "UI: http://localhost:3000"
Write-Host "Temporal Console: http://localhost:8233"
