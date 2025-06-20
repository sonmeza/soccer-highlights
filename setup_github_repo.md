# Setting Up Your Soccer Analysis App on GitHub

## Quick Setup Guide

### 1. Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and sign in
2. Click "New repository" (+ icon in top right)
3. Name it: `soccer-analysis-app`
4. Make it public or private (your choice)
5. Don't initialize with README (we already have one)
6. Click "Create repository"

### 2. Upload Your Code

**Option A: Using GitHub Web Interface (Easiest)**
1. On your new repo page, click "uploading an existing file"
2. Drag and drop these files from your Replit:
   - `app.py`
   - `README.md`
   - `install_dependencies.py`
   - `.gitignore`
   - `.streamlit/config.toml`
   - `replit.md`
3. Write commit message: "Initial commit - Soccer analysis app with video player"
4. Click "Commit changes"

**Option B: Using Git Commands**
```bash
git clone https://github.com/yourusername/soccer-analysis-app.git
cd soccer-analysis-app
# Copy your files here
git add .
git commit -m "Initial commit - Soccer analysis app with video player"
git push origin main
```

### 3. Run Locally

On your computer:

```bash
# Clone your repo
git clone https://github.com/yourusername/soccer-analysis-app.git
cd soccer-analysis-app

# Install dependencies
python install_dependencies.py

# Run the app
streamlit run app.py
```

### 4. AWS Usage (Optional)

**Current AWS Usage:**
- Only used for optional cloud transcription
- App works 100% locally without AWS
- If you want cloud transcription, set environment variables:
  ```bash
  export AWS_ACCESS_KEY_ID=your_key
  export AWS_SECRET_ACCESS_KEY=your_secret
  export AWS_DEFAULT_REGION=us-east-1
  ```

**To Remove AWS Completely:**
Edit `app.py` and remove the AWS imports at the top:
```python
# Remove or comment out these lines:
try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
```

### 5. Key Features Working Locally

- Text commentary analysis (no cloud needed)
- Video upload and audio extraction (uses FFmpeg)
- Local speech recognition (uses Google's free API)
- HTML video player with overlay advertisements
- Bilingual support (English/Spanish)
- Smart merchandise recommendations

### 6. Deployment Options

**Streamlit Cloud (Free):**
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repo
3. Deploy directly from GitHub

**Heroku:**
```bash
# Add to requirements.txt:
streamlit
speechrecognition
pydub
moviepy

# Create Procfile:
web: streamlit run app.py --server.port=$PORT
```

**Local Network:**
```bash
streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

## No Cloud Dependencies Required

Your app is designed to work completely offline with:
- Local pattern matching for event detection
- Client-side JavaScript for video advertisements
- FFmpeg for video/audio processing
- Free Google Speech API for transcription

The AWS integration is purely optional for enhanced transcription accuracy.