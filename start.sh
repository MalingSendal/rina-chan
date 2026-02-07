#!/bin/bash
# Rina-chan AI Companion - Quick Start Script (Linux/macOS)

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   Rina-chan AI Companion Quick Start ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found! Please install Python 3.8+"
    exit 1
fi

echo "✓ Python is installed"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "✗ pip3 not found! Please install Python with pip included."
    exit 1
fi

echo "✓ pip3 is available"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "✗ Failed to install dependencies!"
    exit 1
fi

echo "✓ Dependencies installed successfully"

# Check .env file
if [ ! -f .env ]; then
    echo ""
    echo "⚠ .env file not found! Creating from .env.example..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "Please edit .env file to match your Ollama configuration:"
    echo " - OLLAMA_IP: IP address of your Ollama server"
    echo " - OLLAMA_PORT: Port number (default 11434)"
    echo " - OLLAMA_MODEL: Model name (e.g., mistral, neural-chat)"
    echo ""
    echo "Then run this script again!"
    exit 0
fi

echo "✓ .env file found"

# Check Ollama connection
echo ""
echo "Checking Ollama connection..."
python3 -c "
import os
from dotenv import load_dotenv
import requests
load_dotenv()
ip = os.getenv('OLLAMA_IP')
port = os.getenv('OLLAMA_PORT')
print(f'Checking {ip}:{port}...')
requests.get(f'http://{ip}:{port}/api/tags', timeout=5)
print('✓ Ollama is reachable!')
" &> /dev/null

if [ $? -ne 0 ]; then
    echo "✗ Cannot reach Ollama server!"
    echo ""
    echo "Make sure:"
    echo " 1. Ollama is running (ollama serve)"
    echo " 2. OLLAMA_IP in .env is correct"
    echo " 3. OLLAMA_PORT in .env is correct (default 11434)"
    echo " 4. Firewall allows connection to Ollama port"
    echo ""
    echo "You can test connection with:"
    echo "   curl http://YOUR_IP:11434/api/tags"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════"
echo "✓ Everything looks good!"
echo ""
echo "Starting Rina-chan backend server..."
echo "Server will run on http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "═══════════════════════════════════════════"
echo ""

# Start the server
python3 app.py
