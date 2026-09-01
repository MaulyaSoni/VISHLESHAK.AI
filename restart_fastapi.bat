@echo off
echo ========================================
echo Restarting FastAPI with Auth Endpoints
echo ========================================
echo.

REM Kill existing FastAPI processes
echo Stopping existing FastAPI servers...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq uvicorn*" 2>nul
timeout /t 2 /nobreak >nul

REM Start FastAPI
echo Starting FastAPI on port 8000...
echo.
cd /d D:\FINBOT-2\VISHLESHAK_AI
C:\Users\DELL\Anaconda3\envs\vishleshak\python.exe -m uvicorn backend.fastapi_main:app --reload --port 8000

pause
