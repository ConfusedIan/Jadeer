@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo Starting API Gateway...
start cmd /k "cd APIGateway & venv\Scripts\activate & uvicorn main:app --reload --port 8000"

echo Starting Profile Service...
start cmd /k "cd Profile_Service && venv\Scripts\activate && uvicorn main:app --reload --port 5002"

echo.
echo Opening Swagger...
timeout /t 4 /nobreak >nul
start "" "http://127.0.0.1:8000/docs"
exit /b 0