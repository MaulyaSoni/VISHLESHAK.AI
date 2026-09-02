# Start FastAPI Server
Write-Host "Starting FastAPI on port 8000..." -ForegroundColor Green
Write-Host ""

Set-Location "D:\FINBOT-2\VISHLESHAK_AI"

$pythonExe = "C:\Users\DELL\Anaconda3\envs\vishleshak\python.exe"
$command = "$pythonExe -m uvicorn backend.fastapi_main:app --reload --port 8000"

Write-Host "Command: $command" -ForegroundColor Yellow
Write-Host ""

# Start in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\FINBOT-2\VISHLESHAK_AI; C:\Users\DELL\Anaconda3\envs\vishleshak\python.exe -m uvicorn backend.fastapi_main:app --reload --port 8000"

Start-Sleep -Seconds 3

Write-Host "FastAPI starting in new window..." -ForegroundColor Green
Write-Host "Wait 5 seconds, then check: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
