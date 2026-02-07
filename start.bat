@echo off
REM Rina-chan AI Companion - Quick Start Script

echo.
echo ╔══════════════════════════════════════╗
echo ║   Rina-chan AI Companion Quick Start ║
echo ╚══════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Python not found! Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo ✓ Python is installed

REM Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ pip not found! Please install Python with pip included.
    pause
    exit /b 1
)

echo ✓ pip is available

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ✗ Failed to install dependencies!
    pause
    exit /b 1
)

echo ✓ Dependencies installed successfully

REM Check .env file
if not exist .env (
    echo.
    echo ⚠ .env file not found! Creating from .env.example...
    copy .env.example .env
    echo ✓ Created .env file
    echo.
    echo Please edit .env file to match your Ollama configuration:
    echo  - OLLAMA_IP: IP address of your Ollama server
    echo  - OLLAMA_PORT: Port number (default 11434)
    echo  - OLLAMA_MODEL: Model name (e.g., mistral, neural-chat)
    echo.
    echo Then run this script again!
    pause
    exit /b 0
)

echo ✓ .env file found

REM Check Ollama connection
echo.
echo Checking Ollama connection...
python -c "import os; from dotenv import load_dotenv; import requests; load_dotenv(); ip=os.getenv('OLLAMA_IP'); port=os.getenv('OLLAMA_PORT'); print(f'Checking {ip}:{port}...'); requests.get(f'http://{ip}:{port}/api/tags', timeout=5); print('✓ Ollama is reachable!')" >nul 2>&1

if %errorlevel% neq 0 (
    echo ✗ Cannot reach Ollama server!
    echo.
    echo Make sure:
    echo  1. Ollama is running (ollama serve)
    echo  2. OLLAMA_IP in .env is correct
    echo  3. OLLAMA_PORT in .env is correct (default 11434)
    echo  4. Firewall allows connection to Ollama port
    echo.
    echo You can test connection with:
    echo   curl http://YOUR_IP:11434/api/tags
    pause
    exit /b 1
)

echo.
echo ═══════════════════════════════════════════
echo ✓ Everything looks good!
echo.
echo Starting Rina-chan backend server...
echo Server will run on http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ═══════════════════════════════════════════
echo.

REM Start the server
python app.py

pause
