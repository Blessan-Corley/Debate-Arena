@echo off
cd /d "%~dp0backend"
py -3 check_mongo.py
if errorlevel 1 exit /b 1
py -3 -m uvicorn main:app --reload --port 8000
