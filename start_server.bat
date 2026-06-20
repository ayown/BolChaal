@echo off
echo.
echo  ==========================================
echo   BolChaal - Maithili Language Translator
echo  ==========================================
echo.
echo  Starting backend server...
echo  API will be available at: http://localhost:8000
echo  API docs at:              http://localhost:8000/docs
echo.
echo  NOTE: First run will download the AI model (~400MB).
echo  This is a one-time download. Please wait!
echo.

cd /d "%~dp0backend"
"%~dp0venv\Scripts\python.exe" main.py

pause
