#!/bin/bash

# Setup script for Soccer Analysis App in GitHub Codespaces
echo "🏈 Setting up Soccer Analysis App..."

# Update system packages
sudo apt-get update

# Install FFmpeg for video processing
echo "📹 Installing FFmpeg..."
sudo apt-get install -y ffmpeg

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install --upgrade pip
pip install streamlit>=1.46.0
pip install pandas>=2.3.0
pip install moviepy>=1.0.3
pip install pydub>=0.25.1
pip install SpeechRecognition>=3.10.0
pip install boto3>=1.34.0

# Optional: Install PyAudio for microphone support
echo "🎤 Installing audio dependencies..."
sudo apt-get install -y portaudio19-dev python3-pyaudio
pip install pyaudio || echo "PyAudio installation failed (optional dependency)"

# Create .streamlit directory if it doesn't exist
mkdir -p .streamlit

# Set up Git configuration (if not already set)
if [ -z "$(git config --global user.name)" ]; then
    echo "⚙️ Setting up Git configuration..."
    echo "Please configure Git with your information:"
    echo "git config --global user.name 'Your Name'"
    echo "git config --global user.email 'your.email@example.com'"
fi

echo "✅ Setup complete! Your Soccer Analysis App is ready to use."
echo ""
echo "To start the app:"
echo "  streamlit run app.py"
echo ""
echo "The app will be available at:"
echo "  - Local: http://localhost:5000"
echo "  - Codespaces: Use the forwarded port 5000"
echo ""
echo "Features available:"
echo "  - Video analysis with speech-to-text"
echo "  - Goal detection and player recognition"
echo "  - Overlay advertisements for jerseys"
echo "  - Support for English and Spanish"
echo "  - 300MB file upload limit"