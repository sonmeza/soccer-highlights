#!/usr/bin/env python3
"""
Dependency installation script for Soccer Analysis App
Run this before starting the application to install required packages
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a Python package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ Failed to install {package}")
        return False

def check_ffmpeg():
    """Check if ffmpeg is available"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✓ FFmpeg is available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ FFmpeg not found")
        print("Please install FFmpeg:")
        print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  macOS: brew install ffmpeg")
        print("  Windows: Download from https://ffmpeg.org/download.html")
        return False

def main():
    print("Installing Soccer Analysis App dependencies...")
    print("=" * 50)
    
    # Required packages
    packages = [
        "streamlit>=1.46.0",
        "speechrecognition>=3.10.0", 
        "pydub>=0.25.1",
        "moviepy>=1.0.3"
    ]
    
    # Optional packages
    optional_packages = [
        "boto3>=1.34.0",  # For AWS transcription
        "openai>=1.0.0"   # For future AI features
    ]
    
    success_count = 0
    
    print("\nInstalling required packages:")
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print("\nInstalling optional packages:")
    for package in optional_packages:
        if install_package(package):
            success_count += 1
    
    print("\nChecking system dependencies:")
    ffmpeg_ok = check_ffmpeg()
    
    print("\n" + "=" * 50)
    print("Installation Summary:")
    print(f"✓ {success_count}/{len(packages + optional_packages)} Python packages installed")
    print(f"{'✓' if ffmpeg_ok else '✗'} FFmpeg availability")
    
    if success_count >= len(packages) and ffmpeg_ok:
        print("\n🎉 All dependencies ready! You can now run:")
        print("   streamlit run app.py")
    else:
        print("\n⚠️  Some dependencies missing. App may have limited functionality.")

if __name__ == "__main__":
    main()