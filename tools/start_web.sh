#!/bin/bash

# Multi-Agent System Web Interface Startup Script

PYTHON_BIN="python3"

echo ""
echo "========================================================================"
echo "🚀 SURFACECRAFT STUDIO - Multi-Agent System"
echo "    Web Interface Launcher"
echo "========================================================================"
echo ""

# Check if Python is installed
if ! command -v "$PYTHON_BIN" &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "   Please install Python 3.8 or higher"
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."

REQUIRED_PACKAGES=("Flask" "flask-socketio" "eventlet")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! "$PYTHON_BIN" -c "import ${package,,}" &> /dev/null; then
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo "❌ Missing packages: ${MISSING_PACKAGES[*]}"
    echo ""
    echo "Installing missing packages..."
    "$PYTHON_BIN" -m pip install Flask flask-socketio eventlet python-socketio

    if [ $? -ne 0 ]; then
        echo "❌ Failed to install packages"
        exit 1
    fi
fi

echo "✅ All dependencies installed"
echo ""

# Check if port 5000 is available
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 5000 is already in use"
    echo ""
    read -p "   Kill existing process and restart? (y/n): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   Stopping existing process..."
        lsof -ti:5000 | xargs kill -9 2>/dev/null
        sleep 2
    else
        echo "   Exiting..."
        exit 1
    fi
fi

echo "🌐 Starting web server..."
echo ""

# Start the Flask app
"$PYTHON_BIN" app.py

# If the script reaches here, the server has stopped
echo ""
echo "========================================================================"
echo "👋 Web server stopped"
echo "========================================================================"
