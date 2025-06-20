# Soccer Analysis App with Video Player & Smart Advertisements

A comprehensive soccer game analysis tool that extracts key moments from match commentary and displays contextual advertisements during video highlights.

## Features

- **Text Commentary Analysis**: Extract goals, cards, player actions, and timestamps from soccer commentary
- **Video Processing**: Upload MP4 videos and automatically transcribe audio to text
- **Bilingual Support**: Works with both English and Spanish commentary
- **Smart Video Player**: HTML5 video player with JavaScript-powered overlay advertisements
- **Contextual Advertising**: Pop-up ads showing player jerseys and soccer merchandise during highlights
- **Local Processing**: Works completely offline without cloud dependencies

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/soccer-analysis-app.git
cd soccer-analysis-app
```

2. Install dependencies:
```bash
pip install streamlit speechrecognition pydub moviepy boto3 openai
```

3. Install system dependencies (for audio processing):
```bash
# On Ubuntu/Debian:
sudo apt-get install ffmpeg

# On macOS:
brew install ffmpeg

# On Windows:
# Download ffmpeg from https://ffmpeg.org/download.html
```

### Running the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

### Text Analysis
1. Select "Text Commentary" mode
2. Choose language (English/Spanish)
3. Paste soccer commentary text or use provided examples
4. Click "Analyze Commentary" to extract events and player mentions

### Video Analysis
1. Select "Video Upload" mode
2. Choose processing method (Local recommended)
3. Upload an MP4 video with soccer commentary
4. Wait for audio extraction and transcription
5. View the video player with smart overlay advertisements

## Video Player Features

- **Overlay Advertisements**: Pop-up ads appear in bottom-right corner during highlights
- **Smart Targeting**: Shows relevant merchandise based on events (goals → jerseys, cards → accessories)
- **Interactive Shopping**: Buy Now and Save buttons with shopping cart functionality
- **Automatic Timing**: Ads appear at specific timestamps based on commentary analysis

## Configuration

### Local Processing (Default)
The app works completely offline using:
- Local speech recognition via Google's free API
- FFmpeg for audio extraction
- Pattern matching for event detection

### Optional AWS Integration
For enhanced transcription accuracy, you can optionally configure AWS:

1. Set up AWS credentials:
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

2. The app will automatically detect AWS availability and offer cloud transcription

## Dependencies

### Core Requirements
- `streamlit`: Web framework for the user interface
- `speechrecognition`: Local speech-to-text conversion
- `pydub`: Audio processing and format conversion
- `moviepy`: Video processing and audio extraction

### Optional Requirements
- `boto3`: AWS integration for cloud transcription (optional)
- `openai`: Future AI integrations (not currently used)

## Project Structure

```
├── app.py                 # Main application file
├── .streamlit/
│   └── config.toml       # Streamlit configuration
├── README.md             # This file
├── replit.md             # Project documentation
└── requirements.txt      # Python dependencies
```

## Language Support

### English
- Recognizes Premier League, MLS, and international soccer terminology
- Supports standard English player and team names
- Compatible with English audio transcription

### Spanish
- Includes La Liga, Liga MX, and Spanish soccer vocabulary
- Recognizes Spanish player names and soccer terms
- Supports Spanish audio processing (es-ES)

## Browser Compatibility

The video player with overlay advertisements works in:
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Troubleshooting

### Video Upload Issues
- Ensure video files are in MP4 format
- Check that audio track contains clear speech
- Try shorter video clips (under 5 minutes) for faster processing

### Audio Quality
- Use videos with clear commentary audio
- Avoid videos with loud background music or crowd noise
- Consider using the AWS transcription option for better accuracy

### Performance
- Local processing works best with clear, high-quality audio
- Large video files may take several minutes to process
- Consider using AWS transcription for production environments

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the video quality requirements
3. Open an issue on GitHub with detailed error information