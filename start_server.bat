@echo off
echo Killing all Python processes...
taskkill /F /IM python.exe /T
timeout /t 2
echo.
echo Starting backend server...
cd backend
set GOOGLE_API_KEY=AIzaSyDgmAVIF6bgdbLUAMvf1GGafBfGYmqKI5U
set LLM_PROVIDER=google
python run.py
