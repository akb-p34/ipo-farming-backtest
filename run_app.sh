#!/bin/bash

# IPO Backtest Terminal Launcher for Mac/Linux

# Get the directory of this script
DIR="$(cd "$(dirname "$0")" && pwd)"

# Change to project directory
cd "$DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements if needed
echo "📦 Checking dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt 2>/dev/null || true
pip install -q -r requirements_app.txt 2>/dev/null || true

# ASCII art header
echo ""
echo "╔════════════════════════════════════════════╗"
echo "║       IPO BACKTEST TERMINAL v1.0           ║"
echo "║     Modern Finance Analytics Platform      ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Run the application
python3 run_app.py