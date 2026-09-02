@echo off
echo ============================================
echo RESTARTING FASTAPI - FRESH START
echo ============================================
echo.

echo Step 1: Killing all Python processes...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo Done!

echo.
echo Step 2: Starting FastAPI with auth endpoints...
echo.
cd /d D:\FINBOT-2\VISHLESHAK_AI
start "FastAPI Server" C:\Users\DELL\Anaconda3\envs\vishleshak\python.exe -m uvicorn backend.fastapi_main:app --reload --port 8000

timeout /t 5 /nobreak >nul

echo.
echo Step 3: Creating admin user...
echo.
cd /d D:\FINBOT-2\VISHLESHAK_AI\backend
C:\Users\DELL\Anaconda3\envs\vishleshak\python.exe create_admin.py

echo.
echo ============================================
echo DONE! FastAPI is starting...
echo ============================================
echo.
echo Wait 5 seconds, then test login at:
echo http://localhost:8000/docs
echo.
echo Or use frontend at:
echo http://localhost:5173
echo.
echo Credentials:
echo Email: admin@test.com
echo Password: admin123
echo.
pause
