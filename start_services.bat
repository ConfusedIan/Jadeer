@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo Starting API Gateway...
start cmd /k "cd APIGateway && python -m uvicorn main:app --reload --port 8000"

echo Starting Profile Service...
start cmd /k "cd Profile_Service && python -m uvicorn main:app --reload --port 5002"

echo Starting CV Service...
start cmd /k "cd CV_Service && python -m uvicorn main:app --reload --port 5004"

echo Starting Assessment Service...
start cmd /k "cd SkillsAssement && python -m uvicorn app:app --reload --port 5003"

echo Starting Recommendation Service...
start cmd /k "cd Recommendation_Service && python -m uvicorn main:app --reload --port 5005"

echo Starting Certificates Service...
start cmd /k "cd Cert_Ver_Service && python -m uvicorn main:app --reload --port 5006"

echo Starting Ranking Service...
start cmd /k "cd Ranking_Service && python -m uvicorn main:app --reload --port 5007"

echo.
echo Opening Swagger...
timeout /t 4 /nobreak >nul
start "" "http://127.0.0.1:8000/docs"
exit /b 0