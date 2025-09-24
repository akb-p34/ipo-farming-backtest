#!/usr/bin/env python3
"""
IPO Backtest Terminal Launcher
Launches the Streamlit app with custom dark theme
"""

import streamlit.web.cli as stcli
import sys
from pathlib import Path
import os

def main():
    # Change to app directory
    app_dir = Path(__file__).parent
    os.chdir(app_dir)

    # Configure Streamlit with dark theme
    sys.argv = [
        "streamlit",
        "run",
        "app/main.py",
        "--theme.base=dark",
        "--theme.primaryColor=#ffffff",
        "--theme.backgroundColor=#0a0a0a",
        "--theme.secondaryBackgroundColor=#1a1a1a",
        "--theme.textColor=#ffffff",
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]

    print("\n" + "="*60)
    print("         IPO BACKTEST TERMINAL")
    print("="*60)
    print("\n✨ Starting application...")
    print("📊 Opening browser window...")
    print("\nPress Ctrl+C to stop the server\n")

    sys.exit(stcli.main())

if __name__ == "__main__":
    main()