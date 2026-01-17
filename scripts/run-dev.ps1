# Development run script for Windows PowerShell
# Usage: .\scripts\run-dev.ps1

Write-Host "🔬 Science Digest - Development Mode" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

# Check if Docker is running
$dockerRunning = docker info 2>$null
if (-not $dockerRunning) {
    Write-Host "❌ Docker is not running. Please start Docker first." -ForegroundColor Red
    exit 1
}

# Start services
Write-Host "`n📦 Starting database and Redis..." -ForegroundColor Yellow
docker-compose up -d db redis

# Wait for database to be ready
Write-Host "⏳ Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Backend
Write-Host "`n🐍 Starting backend..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location "$using:PWD\backend"
    if (-not (Test-Path "venv")) {
        python -m venv venv
    }
    & ".\venv\Scripts\Activate.ps1"
    pip install -r requirements.txt -q
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Frontend
Write-Host "⚛️  Starting frontend..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "$using:PWD\frontend"
    if (-not (Test-Path "node_modules")) {
        npm install
    }
    npm run dev
}

Write-Host "`n✅ Services starting..." -ForegroundColor Green
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "   Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "`nPress Ctrl+C to stop all services`n" -ForegroundColor Gray

# Wait and show logs
try {
    while ($true) {
        Receive-Job $backendJob
        Receive-Job $frontendJob
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host "`n🛑 Stopping services..." -ForegroundColor Yellow
    Stop-Job $backendJob, $frontendJob
    Remove-Job $backendJob, $frontendJob
    docker-compose down
}
