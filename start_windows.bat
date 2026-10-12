@echo off
setlocal
cd /d %~dp0
if not exist backend\echo.db echo.>backend\echo.db
start "ECHO Backend" cmd /k "cd backend && python -m uvicorn app.main:app --reload --port 8000"
start "ECHO Frontend" cmd /k "cd frontend && npm install && npm run dev -- --host 0.0.0.0"
echo.
echo ECHO demo starting...
echo Open http://localhost:5173
endlocal
