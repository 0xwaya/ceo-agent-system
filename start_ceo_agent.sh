#!/bin/bash

# CEO Agent - Executive AI System Launcher
# Simple script to start the CEO Agent admin dashboard

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -d ".venv" ]; then
    ENV_DIR=".venv"
elif [ -d "venv" ]; then
    ENV_DIR="venv"
else
    ENV_DIR=".venv"
fi

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Banner
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  👔 CEO AGENT - EXECUTIVE AI SYSTEM"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.10"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]]; then
    echo -e "${GREEN}✓ Python $python_version detected${NC}"
else
    echo -e "${RED}✗ Python 3.10+ required (found $python_version)${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$ENV_DIR" ]; then
    echo -e "${YELLOW}⚠ No virtual environment found${NC}"
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv "$ENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source "$ENV_DIR/bin/activate"
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Check dependencies
echo -e "${BLUE}Checking dependencies...${NC}"
if ! python3 -c "import flask" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Dependencies not installed${NC}"
    echo -e "${BLUE}Installing dependencies...${NC}"
    pip3 install -r requirements.txt --quiet
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dependencies OK${NC}"
fi

# Check port availability
echo -e "${BLUE}Checking port 5001...${NC}"
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}⚠ Port 5001 is in use${NC}"
    echo -e "${BLUE}Killing existing process...${NC}"
    lsof -ti:5001 | xargs kill -9 2>/dev/null
    sleep 2
    echo -e "${GREEN}✓ Port 5001 cleared${NC}"
else
    echo -e "${GREEN}✓ Port 5001 available${NC}"
fi

# Create necessary directories
mkdir -p logs
mkdir -p static/css
mkdir -p static/js
mkdir -p templates

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🚀 Starting CEO Agent System...${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}  Admin Dashboard:${NC} http://localhost:5001/admin"
echo -e "${BLUE}  Legacy Interface:${NC} http://localhost:5001"
echo ""
echo -e "${YELLOW}  Mode:${NC} TRAINING (Safe for development)"
echo -e "${YELLOW}  Budget:${NC} \$50,000 (98% requires user approval)"
echo ""
echo -e "${GREEN}  Press CTRL+C to stop the server${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""

# Start the application
python3 app.py
