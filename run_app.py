#!/usr/bin/env python3
"""
Quick start script for Soccer Analysis App
Run this script to start the application with proper configuration
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['streamlit', 'pandas', 'moviepy', 'pydub', 'speech_recognition']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing packages: {', '.join(missing_packages)}")
        print("Run: python install_dependencies.py")
        return False
    return True

def main():
    """Start the Soccer Analysis App"""
    print("🏈 Starting Soccer Analysis App...")
    
    # Check dependencies
    if not check_dependencies():
        print("Please install dependencies first")
        sys.exit(1)
    
    # Start Streamlit with proper configuration
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port=5000",
        "--server.address=0.0.0.0",
        "--server.headless=true"
    ]
    
    print("App will be available at:")
    print("- Local: http://localhost:5000")
    print("- Network: http://0.0.0.0:5000")
    print("\nPress Ctrl+C to stop the application")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Stopping Soccer Analysis App...")

if __name__ == "__main__":
    main()