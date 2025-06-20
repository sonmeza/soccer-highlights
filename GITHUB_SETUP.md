# Complete GitHub Setup Guide for Soccer Analysis App

## Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and create a new repository
2. Name it: `soccer-analysis-app`
3. Make it public (recommended for easy sharing)
4. Don't initialize with README (we have existing files)
5. Click "Create repository"

## Step 2: Upload Files to GitHub

**Method A: GitHub Web Interface (Recommended)**

1. On your new repo page, click "uploading an existing file"
2. Upload these files from your Replit project:
   - `app.py` (main application)
   - `README.md` (project documentation)
   - `install_dependencies.py` (dependency installer)
   - `.gitignore` (Git ignore file)
   - `replit.md` (project overview)
   - `github_requirements.txt` (rename to `requirements.txt`)
   - `.streamlit/config.toml` (Streamlit configuration)
   - `.devcontainer/` folder (Codespaces configuration)

3. Commit message: "Initial commit - Soccer analysis app with video overlay ads"
4. Click "Commit changes"

**Method B: Git Commands**

```bash
git clone https://github.com/yourusername/soccer-analysis-app.git
cd soccer-analysis-app
# Copy your files here
git add .
git commit -m "Initial commit - Soccer analysis app"
git push origin main
```

## Step 3: Enable GitHub Codespaces

1. In your repository, click the green "Code" button
2. Select "Codespaces" tab
3. Click "Create codespace on main"
4. Wait for the environment to build (5-10 minutes first time)

**Codespaces will automatically:**
- Install Python 3.11
- Install FFmpeg for video processing
- Install all Python dependencies
- Forward ports 5000 and 8501
- Set up the development environment

## Step 4: Run in Codespaces

Once Codespaces loads:

```bash
# Start the application
streamlit run app.py --server.port 5000

# Or use the default Streamlit port
streamlit run app.py
```

The app will be available through the forwarded port in Codespaces.

## Step 5: Local Development Setup

To run on your local machine:

```bash
# Clone the repository
git clone https://github.com/yourusername/soccer-analysis-app.git
cd soccer-analysis-app

# Install system dependencies
# On Ubuntu/Debian:
sudo apt-get install ffmpeg

# On macOS:
brew install ffmpeg

# On Windows:
# Download FFmpeg from https://ffmpeg.org/download.html

# Install Python dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## Step 6: Deployment Options

**Streamlit Community Cloud (Free)**
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub account
3. Select your repository
4. Deploy with one click

**Heroku Deployment**
1. Create `Procfile`:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

2. Add `system-packages.txt`:
```
ffmpeg
```

**Railway/Render Deployment**
- Both support automatic deployment from GitHub
- Use the provided requirements.txt
- Set buildpack to Python

## Features Working Out of the Box

✅ **Text commentary analysis** - Pattern matching and NLP
✅ **Video upload processing** - Up to 300MB files
✅ **Audio extraction** - FFmpeg-powered
✅ **Speech recognition** - Local and cloud options
✅ **Goal detection** - Smart pattern recognition
✅ **Player identification** - Name extraction from commentary
✅ **Jersey advertisements** - Overlay system with purchase buttons
✅ **Bilingual support** - English and Spanish
✅ **Manual commentary editing** - Text area for refinements

## Optional AWS Integration

The app works completely without AWS. For enhanced transcription:

1. Set environment variables in Codespaces:
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

2. In Codespaces settings, add these as secrets for persistence

## Troubleshooting

**Port Issues in Codespaces:**
- Use port 5000 (configured to auto-forward)
- If port 5000 is busy, try 8501

**FFmpeg Missing:**
- Codespaces setup script installs it automatically
- For local: install FFmpeg for your OS

**Large File Uploads:**
- 300MB limit is configured in `.streamlit/config.toml`
- Increase if needed for larger videos

**Speech Recognition Errors:**
- App falls back gracefully to manual input
- Google's free API has rate limits

## Repository Structure

```
soccer-analysis-app/
├── app.py                      # Main Streamlit application
├── README.md                   # Project documentation
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
├── replit.md                   # Project overview
├── .streamlit/
│   └── config.toml            # Streamlit configuration
├── .devcontainer/
│   ├── devcontainer.json      # Codespaces configuration
│   └── setup.sh               # Environment setup script
└── install_dependencies.py    # Dependency installer
```

Your app is now ready for GitHub and Codespaces deployment with full video analysis capabilities!