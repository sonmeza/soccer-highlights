# Soccer Analysis App

## Overview

This is a Streamlit-based web application designed for analyzing soccer match commentary from both text input and MP4 video files. The application extracts meaningful insights from soccer-related content, including match events, player actions, and game statistics. It supports dual processing modes: local offline processing and AWS cloud-based processing for video transcription.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit - chosen for rapid prototyping and easy deployment of data science applications
- **UI Pattern**: Single-page application with interactive widgets for text input and analysis results display
- **Deployment**: Autoscale deployment on Replit with port 5000 configuration

### Backend Architecture
- **Language**: Python 3.11
- **Video Processing**: FFmpeg for audio extraction from MP4 files
- **Speech Recognition**: Dual-mode support for both local and cloud-based transcription
  - Local: SpeechRecognition library with Google's free API
  - Cloud: Amazon Transcribe for professional-grade accuracy
- **Audio Processing**: PyDub for audio format conversion and chunking
- **Data Processing**: Pattern matching and regex for soccer event detection
- **Caching**: Streamlit's `@st.cache_resource` for efficient model loading

### Processing Pipeline
The application supports dual input modes with comprehensive processing pipelines:

**Text Commentary Pipeline:**
1. Text input validation and preprocessing
2. Pattern matching for soccer-specific events and timestamps
3. Entity recognition for player and team names
4. Data extraction and structuring
5. Results presentation through Streamlit interface

**Video Processing Pipeline:**
1. MP4 video file upload and validation
2. Audio extraction using FFmpeg
3. Speech-to-text conversion (local or AWS Transcribe)
4. Commentary text generation with timestamps
5. Automatic analysis using text pipeline
6. Cleanup of temporary files

## Key Components

### SoccerAnalyzer Class
- **Purpose**: Core analysis engine that processes soccer commentary text
- **Key Features**:
  - Event pattern recognition (goals, assists, cards, substitutions, etc.)
  - Timestamp extraction from match commentary
  - Position and role identification
  - Soccer-specific vocabulary and terminology handling

### Event Detection Patterns
The application recognizes various soccer events through regex patterns:
- **Goals**: Scoring events and goal-related actions
- **Disciplinary Actions**: Yellow cards, red cards, dismissals
- **Game Events**: Corners, free kicks, penalties, offsides
- **Player Actions**: Shots, saves, tackles, headers
- **Administrative**: Substitutions and player changes

### NLP Model Integration
- Uses spaCy's pre-trained English model for named entity recognition
- Implements fallback error handling for missing model installations
- Caches the model to improve application performance

## Data Flow

1. **Input Stage**: User provides soccer commentary text through Streamlit interface
2. **Preprocessing**: Text is cleaned and prepared for analysis
3. **NLP Analysis**: spaCy model processes text for entities and linguistic features
4. **Pattern Matching**: Regex patterns identify soccer-specific events and actions
5. **Data Structuring**: Extracted information is organized into structured format
6. **Visualization**: Results are displayed through Streamlit's interactive components

## External Dependencies

### Core Libraries
- **Streamlit (≥1.46.0)**: Web application framework for the user interface
- **spaCy (≥3.8.7)**: Natural language processing library for text analysis
- **Pandas (≥2.3.0)**: Data manipulation and analysis library

### NLP Model Dependency
- **en_core_web_sm**: spaCy's English language model (must be downloaded separately)
- Application includes error handling for missing model scenarios

### System Requirements
- **Python**: Version 3.11 or higher
- **Nix Environment**: Stable channel 24_05 with glibc locales support

## Deployment Strategy

### Replit Configuration
- **Target**: Autoscale deployment for automatic scaling based on demand
- **Runtime**: Python 3.11 module with Nix package management
- **Port Configuration**: Application runs on port 5000 with proper server settings
- **Workflow**: Parallel execution support with shell commands for Streamlit

### Server Configuration
- **Headless Mode**: Enabled for deployment environments
- **Network**: Configured to bind to all interfaces (0.0.0.0)
- **Port**: Fixed to 5000 for consistent deployment

### Scalability Considerations
- Model caching reduces computational overhead on repeated requests
- Stateless design allows for horizontal scaling
- Lightweight dependencies minimize resource requirements

## Changelog

```
Changelog:
- June 19, 2025. Initial setup and app creation completed
- June 19, 2025. Created working soccer analysis tool that extracts timestamped events and player mentions from match commentary
- June 19, 2025. Enhanced with dual video processing modes: local offline speech-to-text and AWS cloud transcription capabilities
- June 19, 2025. Added complete Spanish language support for both text analysis and speech recognition
- June 19, 2025. Built HTML5 video player with JavaScript-powered overlay advertisements that appear during highlights
- June 19, 2025. Created GitHub deployment package with setup instructions for independent hosting
- June 20, 2025. Fixed overlay advertisement system and removed app reset issues
- June 20, 2025. Added comprehensive GitHub Codespaces integration with automatic environment setup
- June 20, 2025. Created complete deployment configuration for GitHub, Heroku, and Streamlit Cloud
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```