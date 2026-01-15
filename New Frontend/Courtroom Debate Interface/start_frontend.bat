@echo off
echo ================================================
echo   AETHER Frontend-Backend Integration Starter
echo ================================================
echo.

REM Check if we're in the right directory
if not exist "package.json" (
    echo Error: package.json not found!
    echo Please run this script from the "New Frontend/Courtroom Debate Interface" directory
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo Failed to install dependencies!
        pause
        exit /b 1
    )
) else (
    echo Dependencies already installed.
)

echo.
echo [2/3] Checking backend server...
curl -s http://localhost:8000 >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: Backend server is not running!
    echo Please start the backend server in a separate terminal:
    echo   cd backend
    echo   python -m uvicorn api.main:app --reload
    echo.
    echo Press any key to continue anyway, or Ctrl+C to exit...
    pause >nul
)

echo.
echo [3/3] Starting frontend development server...
echo.
echo Frontend will be available at: http://localhost:5173
echo Backend should be running at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

call npm run dev
