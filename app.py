import streamlit as st
import streamlit.components.v1 as components
import re
from datetime import datetime
import tempfile
import os
import time
import json
import base64

# AWS imports - will be imported only when needed
try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

# Local speech recognition imports
try:
    import speech_recognition as sr
    from pydub import AudioSegment
    LOCAL_STT_AVAILABLE = True
except ImportError:
    LOCAL_STT_AVAILABLE = False

class VideoProcessor:
    def __init__(self):
        self.s3_client = None
        self.transcribe_client = None
        self.aws_available = AWS_AVAILABLE
        self.local_stt_available = LOCAL_STT_AVAILABLE
        if self.aws_available:
            self._initialize_aws_clients()
    
    def _initialize_aws_clients(self):
        """Initialize AWS clients if credentials are available"""
        if not self.aws_available:
            return False
        try:
            # Check if AWS credentials are configured
            session = boto3.Session()
            credentials = session.get_credentials()
            
            if credentials:
                self.s3_client = boto3.client('s3')
                self.transcribe_client = boto3.client('transcribe')
                return True
            else:
                return False
        except Exception as e:
            return False
    
    def extract_audio_from_video(self, video_file):
        """Extract audio from MP4 video file using ffmpeg"""
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
                temp_video.write(video_file.read())
                temp_video_path = temp_video.name
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
            
            # Use ffmpeg to extract audio
            import subprocess
            result = subprocess.run([
                'ffmpeg', '-i', temp_video_path, 
                '-acodec', 'pcm_s16le', 
                '-ar', '16000', 
                '-ac', '1',
                temp_audio_path, '-y'
            ], capture_output=True, text=True)
            
            # Clean up video file
            os.unlink(temp_video_path)
            
            if result.returncode == 0:
                return temp_audio_path
            else:
                st.error(f"FFmpeg error: {result.stderr}")
                return None
        
        except Exception as e:
            st.error(f"Error extracting audio: {str(e)}")
            return None
    
    def transcribe_audio_locally(self, audio_file_path, language='en'):
        """Transcribe audio using local speech recognition with enhanced processing"""
        if not self.local_stt_available:
            st.error("Local speech recognition libraries not available.")
            return None
        
        try:
            # Initialize recognizer
            recognizer = sr.Recognizer()
            
            # Adjust recognizer settings for better detection
            recognizer.energy_threshold = 300  # Minimum audio energy to consider for recording
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = 0.8  # Seconds of non-speaking before considering phrase complete
            recognizer.operation_timeout = None  # No timeout
            
            # Convert audio to WAV format with enhanced settings
            audio = AudioSegment.from_file(audio_file_path)
            
            # Enhance audio quality
            audio = audio.set_frame_rate(16000)  # Standard rate for speech recognition
            audio = audio.set_channels(1)  # Mono audio
            audio = audio.normalize()  # Normalize volume
            
            # Apply audio filters to improve speech detection
            # Amplify audio if it's too quiet
            if audio.dBFS < -20:
                audio = audio + (abs(audio.dBFS) - 10)
            
            # Split audio into smaller chunks for better processing
            chunk_length_ms = 15000  # 15 seconds per chunk (smaller for better detection)
            overlap_ms = 2000  # 2 seconds overlap between chunks
            
            chunks = []
            for i in range(0, len(audio), chunk_length_ms - overlap_ms):
                chunk = audio[i:i + chunk_length_ms]
                if len(chunk) > 1000:  # Only process chunks longer than 1 second
                    chunks.append((chunk, i))
            
            full_transcript = []
            successful_chunks = 0
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Set language code for Google Speech Recognition
            lang_code = 'es-ES' if language == 'es' else 'en-US'
            
            for i, (chunk, start_time) in enumerate(chunks):
                try:
                    # Export chunk to temporary WAV file with better settings
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                        chunk.export(temp_wav.name, format="wav", parameters=["-ar", "16000", "-ac", "1"])
                        
                        # Recognize speech with language parameter
                        with sr.AudioFile(temp_wav.name) as source:
                            # Adjust ambient noise
                            recognizer.adjust_for_ambient_noise(source, duration=0.5)
                            audio_data = recognizer.record(source)
                            
                            # Try multiple recognition methods for better results
                            text = None
                            try:
                                text = recognizer.recognize_google(audio_data, language=lang_code)
                            except sr.UnknownValueError:
                                # Try with different language if first attempt fails
                                try:
                                    fallback_lang = 'en-US' if language == 'es' else 'es-ES'
                                    text = recognizer.recognize_google(audio_data, language=fallback_lang)
                                except sr.UnknownValueError:
                                    pass
                            
                            if text and text.strip():
                                # Calculate more accurate timestamp
                                timestamp_minutes = start_time // 60000
                                timestamp_seconds = (start_time % 60000) // 1000
                                timestamp = f"{timestamp_minutes}:{timestamp_seconds:02d}"
                                full_transcript.append(f"{timestamp}' {text.strip()}")
                                successful_chunks += 1
                        
                        # Clean up temporary file
                        os.unlink(temp_wav.name)
                
                except sr.UnknownValueError:
                    # Speech not understood in this chunk
                    pass
                except sr.RequestError as e:
                    st.warning(f"Speech recognition service error: {e}")
                except Exception as e:
                    # Continue processing other chunks even if one fails
                    pass
                
                # Update progress
                progress_percentage = int((i + 1) / len(chunks) * 100)
                progress_bar.progress(progress_percentage)
                status_text.text(f"Processing audio chunk {i + 1} of {len(chunks)}... Found speech in {successful_chunks} chunks")
            
            progress_bar.progress(100)
            status_text.text(f"Complete! Found speech in {successful_chunks} out of {len(chunks)} chunks")
            
            if full_transcript:
                return "\n".join(full_transcript)
            else:
                # Provide more helpful feedback
                total_duration = len(audio) / 1000  # in seconds
                status_text.text(f"No speech detected in {total_duration:.1f} second video. Audio may be too quiet, unclear, or in a different language.")
                return None
        
        except Exception as e:
            st.error(f"Error during local transcription: {str(e)}")
            return None
    
    def analyze_audio_quality(self, audio_path):
        """Analyze audio file to provide diagnostic information"""
        try:
            audio = AudioSegment.from_file(audio_path)
            
            # Audio diagnostics
            duration = len(audio) / 1000.0  # in seconds
            sample_rate = audio.frame_rate
            channels = audio.channels
            volume_db = audio.dBFS
            
            # Check if audio is too quiet
            is_quiet = volume_db < -30
            
            # Check for silence
            silence_threshold = volume_db + 10
            non_silent_chunks = [chunk for chunk in audio[::1000] if chunk.dBFS > silence_threshold]
            speech_ratio = len(non_silent_chunks) / max(1, len(audio[::1000]))
            
            return {
                'duration': duration,
                'sample_rate': sample_rate,
                'channels': channels,
                'volume_db': volume_db,
                'is_quiet': is_quiet,
                'speech_ratio': speech_ratio,
                'has_potential_speech': speech_ratio > 0.1 and not is_quiet
            }
        except Exception as e:
            return {'error': str(e)}
    
    def process_video_locally(self, video_file, language='en'):
        """Process video using local tools only with enhanced diagnostics"""
        try:
            # Step 1: Extract audio
            st.info("Extracting audio from video...")
            audio_path = self.extract_audio_from_video(video_file)
            if not audio_path:
                return None
            
            # Step 2: Analyze audio quality
            st.info("Analyzing audio quality...")
            audio_analysis = self.analyze_audio_quality(audio_path)
            
            if 'error' not in audio_analysis:
                # Display audio diagnostics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Duration", f"{audio_analysis['duration']:.1f}s")
                with col2:
                    st.metric("Volume", f"{audio_analysis['volume_db']:.1f} dB")
                with col3:
                    st.metric("Speech Ratio", f"{audio_analysis['speech_ratio']:.1f}")
                
                # Provide recommendations based on analysis
                if audio_analysis['is_quiet']:
                    st.warning("Audio is very quiet. The video may have low volume or background audio only.")
                elif audio_analysis['speech_ratio'] < 0.1:
                    st.warning("Very little speech detected in audio. The video may contain mostly music, crowd noise, or silence.")
                elif not audio_analysis['has_potential_speech']:
                    st.warning("Audio quality may not be suitable for speech recognition.")
                else:
                    st.success("Audio quality looks good for speech recognition.")
            
            # Step 3: Transcribe locally with language support
            st.info("Transcribing audio locally... This may take a few minutes.")
            transcript = self.transcribe_audio_locally(audio_path, language)
            
            # Clean up audio file
            if audio_path and os.path.exists(audio_path):
                os.unlink(audio_path)
            
            if transcript:
                return {
                    'status': 'completed',
                    'transcript': transcript,
                    'method': 'local',
                    'audio_analysis': audio_analysis
                }
            else:
                # Provide helpful suggestions when no speech is detected
                suggestions = []
                if 'error' not in audio_analysis:
                    if audio_analysis['is_quiet']:
                        suggestions.append("Try increasing the video volume before uploading")
                    if audio_analysis['speech_ratio'] < 0.1:
                        suggestions.append("Ensure the video contains clear speech commentary")
                    suggestions.append("Try a different video segment with clearer audio")
                    suggestions.append("Consider using text input instead for better results")
                
                return {
                    'status': 'no_speech',
                    'message': 'No clear speech detected',
                    'suggestions': suggestions,
                    'audio_analysis': audio_analysis
                }
        
        except Exception as e:
            st.error(f"Error processing video locally: {str(e)}")
            return None
    
    def upload_to_s3_and_transcribe(self, audio_file_path, bucket_name="soccer-analysis-temp"):
        """Upload audio to S3 and start transcription job"""
        if not self.s3_client or not self.transcribe_client:
            st.error("AWS services not initialized. Please configure your AWS credentials.")
            return None
        
        try:
            # Generate unique job name
            job_name = f"soccer-transcription-{int(time.time())}"
            s3_key = f"audio/{job_name}.wav"
            
            # Upload to S3
            self.s3_client.upload_file(audio_file_path, bucket_name, s3_key)
            s3_uri = f"s3://{bucket_name}/{s3_key}"
            
            # Start transcription job
            response = self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': s3_uri},
                MediaFormat='wav',
                LanguageCode='en-US',
                Settings={
                    'ShowSpeakerLabels': True,
                    'MaxSpeakerLabels': 3  # Usually 2 commentators + referee
                }
            )
            
            return job_name
        
        except Exception as e:
            st.error(f"Error starting transcription: {str(e)}")
            return None
    
    def get_transcription_result(self, job_name):
        """Get transcription result from AWS Transcribe"""
        if not self.transcribe_client:
            return None
        
        try:
            response = self.transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )
            
            status = response['TranscriptionJob']['TranscriptionJobStatus']
            
            if status == 'COMPLETED':
                # Get the transcript
                transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                
                # For simplicity, we'll return the basic transcript
                # In a full implementation, you'd download and parse the JSON result
                return {
                    'status': 'completed',
                    'transcript': "Transcription completed. Download the full transcript from AWS console for detailed analysis.",
                    'transcript_uri': transcript_uri
                }
            elif status == 'FAILED':
                return {
                    'status': 'failed',
                    'error': response['TranscriptionJob'].get('FailureReason', 'Unknown error')
                }
            else:
                return {
                    'status': 'in_progress',
                    'progress': status
                }
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def process_video_file(self, video_file):
        """Complete workflow: extract audio, upload, and transcribe"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        audio_path = None
        try:
            # Step 1: Extract audio
            status_text.text("Extracting audio from video...")
            progress_bar.progress(25)
            
            audio_path = self.extract_audio_from_video(video_file)
            if not audio_path:
                return None
            
            # Step 2: Upload and start transcription
            status_text.text("Uploading to AWS and starting transcription...")
            progress_bar.progress(50)
            
            job_name = self.upload_to_s3_and_transcribe(audio_path)
            if not job_name:
                if audio_path and os.path.exists(audio_path):
                    os.unlink(audio_path)  # Clean up
                return None
            
            # Step 3: Wait for completion (with timeout)
            status_text.text("Transcribing audio... This may take a few minutes.")
            progress_bar.progress(75)
            
            max_wait_time = 300  # 5 minutes
            wait_time = 0
            
            while wait_time < max_wait_time:
                result = self.get_transcription_result(job_name)
                
                if result and result['status'] == 'completed':
                    progress_bar.progress(100)
                    status_text.text("Transcription completed!")
                    if audio_path and os.path.exists(audio_path):
                        os.unlink(audio_path)  # Clean up
                    return result
                elif result and result['status'] == 'failed':
                    st.error(f"Transcription failed: {result.get('error', 'Unknown error')}")
                    if audio_path and os.path.exists(audio_path):
                        os.unlink(audio_path)  # Clean up
                    return None
                
                time.sleep(10)  # Wait 10 seconds before checking again
                wait_time += 10
                
                # Update progress
                progress_percentage = min(75 + (wait_time / max_wait_time) * 20, 95)
                progress_bar.progress(int(progress_percentage))
            
            # Timeout reached
            st.warning("Transcription is taking longer than expected. Check AWS console for job status.")
            if audio_path and os.path.exists(audio_path):
                os.unlink(audio_path)  # Clean up
            return {
                'status': 'timeout',
                'job_name': job_name,
                'message': 'Transcription job started but not completed within timeout. Check AWS console.'
            }
        
        except Exception as e:
            st.error(f"Error processing video: {str(e)}")
            # Clean up any temporary files
            if audio_path and os.path.exists(audio_path):
                os.unlink(audio_path)
            return None

class VideoPlayerWithAds:
    def __init__(self):
        # AWS services for enhanced goal detection (optional)
        self.aws_available = AWS_AVAILABLE
        if self.aws_available:
            try:
                self.comprehend = boto3.client('comprehend')
                self.rekognition = boto3.client('rekognition')
                self.textract = boto3.client('textract')
            except Exception:
                self.aws_available = False
        
        # Sample merchandise database for demonstrations
        self.merchandise_db = {
            # Real player examples for demonstration
            'messi': {
                'name': 'Lionel Messi',
                'team': 'Inter Miami',
                'jersey_price': 89.99,
                'image_url': 'https://via.placeholder.com/200x250/ff69b4/ffffff?text=Messi+Jersey',
                'description': 'Official Inter Miami Messi #10 Jersey'
            },
            'ronaldo': {
                'name': 'Cristiano Ronaldo', 
                'team': 'Al Nassr',
                'jersey_price': 79.99,
                'image_url': 'https://via.placeholder.com/200x250/ffd700/000000?text=Ronaldo+Jersey',
                'description': 'Official Al Nassr Ronaldo #7 Jersey'
            },
            'mbappe': {
                'name': 'Kylian Mbappé',
                'team': 'Real Madrid',
                'jersey_price': 94.99,
                'image_url': 'https://via.placeholder.com/200x250/ffffff/000000?text=Mbappe+Jersey',
                'description': 'Official Real Madrid Mbappé #9 Jersey'
            },
            'haaland': {
                'name': 'Erling Haaland',
                'team': 'Manchester City',
                'jersey_price': 89.99,
                'image_url': 'https://via.placeholder.com/200x250/87ceeb/000000?text=Haaland+Jersey',
                'description': 'Official Manchester City Haaland #9 Jersey'
            }
        }
        
        # Generic merchandise for unknown players
        self.generic_items = [
            {
                'name': 'Premium Soccer Ball',
                'price': 29.99,
                'image_url': 'https://via.placeholder.com/200x250/32cd32/ffffff?text=Soccer+Ball',
                'description': 'Professional Match Quality Soccer Ball'
            },
            {
                'name': 'Soccer Cleats',
                'price': 119.99,
                'image_url': 'https://via.placeholder.com/200x250/ff4500/ffffff?text=Soccer+Cleats',
                'description': 'Premium Performance Soccer Cleats'
            },
            {
                'name': 'Team Scarf',
                'price': 24.99,
                'image_url': 'https://via.placeholder.com/200x250/800080/ffffff?text=Team+Scarf',
                'description': 'Official Team Supporter Scarf'
            }
        ]
    
    def extract_player_from_event(self, event_text):
        """Extract player name from event description with optional AWS enhancement"""
        
        # Try AWS Comprehend for enhanced entity recognition if available
        if self.aws_available:
            try:
                response = self.comprehend.detect_entities(
                    Text=event_text,
                    LanguageCode='en'
                )
                
                # Look for PERSON entities in AWS results
                for entity in response['Entities']:
                    if entity['Type'] == 'PERSON' and entity['Score'] > 0.8:
                        entity_text = entity['Text']
                        # Check against known players
                        for key, data in self.merchandise_db.items():
                            if (key.lower() in entity_text.lower() or 
                                entity_text.lower() in data['name'].lower()):
                                return key
            except Exception:
                pass  # Fall back to local processing
        
        # Local pattern matching for player names
        patterns = [
            r"(?:goal by|scored by|assist by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:scores|goal|assist)",
            r"([A-Z][a-z]+)\s+(?:with the goal|finds the net)",
            r"([A-Z][a-z]+)\s+(?:strikes|nets|converts)",
            r"(?:brilliant|amazing|incredible)\s+(?:goal|strike|finish)\s+(?:by|from)\s+([A-Z][a-z]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, event_text, re.IGNORECASE)
            if match:
                player_name = match.group(1).strip()
                # Check if it matches known players
                for key, data in self.merchandise_db.items():
                    if key.lower() in player_name.lower() or player_name.lower() in data['name'].lower():
                        return key
        return None
    
    def get_merchandise_for_event(self, event_text, event_type):
        """Get relevant merchandise based on the event"""
        player_key = self.extract_player_from_event(event_text)
        
        if player_key and player_key in self.merchandise_db:
            return self.merchandise_db[player_key]
        else:
            # Return generic soccer merchandise for highlights
            if any(keyword in event_type.lower() for keyword in ['goal', 'score']):
                return self.generic_items[0]  # Soccer ball for goals
            elif 'card' in event_type.lower():
                return self.generic_items[2]  # Team scarf for cards
            else:
                return self.generic_items[1]  # Cleats for other events
    
    def display_advertisement(self, merchandise, event_type, timestamp):
        """Display contextual advertisement with purchase option"""
        st.markdown("### 🛍️ Featured Merchandise")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Display product image placeholder
            st.image(merchandise.get('image_url', ''), width=150)
        
        with col2:
            if 'name' in merchandise and 'team' in merchandise:
                # Player jersey
                st.markdown(f"**{merchandise['name']}**")
                st.markdown(f"*{merchandise['team']}*")
                st.markdown(f"**${merchandise['jersey_price']:.2f}**")
                st.markdown(f"_{merchandise['description']}_")
                
                # Purchase buttons
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(f"🛒 Buy Now", key=f"buy_{timestamp}"):
                        st.success(f"Added {merchandise['name']} jersey to cart!")
                with col_b:
                    if st.button(f"❤️ Save", key=f"save_{timestamp}"):
                        st.info(f"Saved {merchandise['name']} jersey to wishlist!")
            else:
                # Generic merchandise
                st.markdown(f"**{merchandise['name']}**")
                st.markdown(f"**${merchandise['price']:.2f}**")
                st.markdown(f"_{merchandise['description']}_")
                
                # Purchase buttons
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(f"🛒 Buy Now", key=f"buy_{timestamp}"):
                        st.success(f"Added {merchandise['name']} to cart!")
                with col_b:
                    if st.button(f"❤️ Save", key=f"save_{timestamp}"):
                        st.info(f"Saved {merchandise['name']} to wishlist!")
        
        # Add relevance note
        st.markdown(f"*Relevant to: {event_type} at {timestamp}*")
    
    def create_video_overlay_html(self, video_base64, goal_events):
        """Create HTML video player with true overlay advertisements for goals only"""
        
        # Generate ad data only for goals
        goal_ads = []
        for i, event in enumerate(goal_events):
            timestamp_str = event.get('timestamp', f'{i*60}:00')
            # Convert timestamp to seconds
            if ':' in timestamp_str:
                parts = timestamp_str.split(':')
                if len(parts) == 2:
                    timestamp_seconds = int(parts[0]) * 60 + int(parts[1])
                else:
                    timestamp_seconds = i * 60
            else:
                timestamp_seconds = i * 60
            
            # Extract player name from goal description
            description = event.get('description', '')
            player_key = self.extract_player_from_event(description)
            
            if player_key and player_key in self.merchandise_db:
                merchandise = self.merchandise_db[player_key]
            else:
                # Default to Messi for demo goals
                merchandise = self.merchandise_db['messi']
            
            goal_ads.append({
                'time': timestamp_seconds,
                'duration': 6,
                'player': merchandise['name'],
                'team': merchandise['team'],
                'price': merchandise['jersey_price'],
                'description': merchandise['description'],
                'goal_description': description
            })
        
        # Create iframe-compatible HTML
        html_content = f"""
        <div style="position: relative; width: 100%; height: 450px; background: #000; border-radius: 10px; overflow: hidden;">
            <video id="soccerVideo" 
                   style="width: 100%; height: 100%; object-fit: contain;" 
                   controls 
                   onloadedmetadata="initializeAds()">
                <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
            </video>
            
            <!-- Goal Advertisement Overlay -->
            <div id="goalAdOverlay" style="
                position: absolute;
                top: 20px;
                right: 20px;
                width: 300px;
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                color: white;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.4);
                display: none;
                font-family: 'Arial', sans-serif;
                z-index: 1000;
                animation: slideInFromRight 0.6s ease-out;
            ">
                <div style="position: absolute; top: 8px; right: 12px;">
                    <button onclick="hideGoalAd()" style="
                        background: none; 
                        border: none; 
                        color: white; 
                        font-size: 20px; 
                        cursor: pointer;
                        opacity: 0.8;
                    ">&times;</button>
                </div>
                
                <div style="text-align: center; margin-bottom: 15px;">
                    <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">⚽ GOAL SCORER</div>
                    <div id="playerName" style="font-size: 20px; font-weight: bold; margin-bottom: 4px;">Player Name</div>
                    <div id="teamName" style="font-size: 14px; opacity: 0.9; margin-bottom: 12px;">Team Name</div>
                </div>
                
                <div style="background: rgba(255,255,255,0.15); padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                    <div style="font-size: 14px; margin-bottom: 8px;">Get the official jersey!</div>
                    <div id="jerseyPrice" style="font-size: 24px; font-weight: bold; color: #90EE90;">$89.99</div>
                    <div id="jerseyDescription" style="font-size: 12px; opacity: 0.9; margin-top: 4px;">Official Team Jersey</div>
                </div>
                
                <div style="display: flex; gap: 10px;">
                    <button onclick="buyJersey()" style="
                        flex: 1;
                        background: #4CAF50;
                        color: white;
                        border: none;
                        padding: 12px;
                        border-radius: 8px;
                        font-weight: bold;
                        cursor: pointer;
                        transition: all 0.3s;
                    " onmouseover="this.style.background='#45a049'" onmouseout="this.style.background='#4CAF50'">
                        🛒 Buy Now
                    </button>
                    <button onclick="saveJersey()" style="
                        flex: 1;
                        background: rgba(255,255,255,0.2);
                        color: white;
                        border: 1px solid white;
                        padding: 12px;
                        border-radius: 8px;
                        font-weight: bold;
                        cursor: pointer;
                        transition: all 0.3s;
                    " onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                        ❤️ Save
                    </button>
                </div>
            </div>
        </div>
        
        <style>
        @keyframes slideInFromRight {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        </style>
        
        <script>
        const video = document.getElementById('soccerVideo');
        const goalAdOverlay = document.getElementById('goalAdOverlay');
        
        // Goal advertisement data
        const goalAds = {json.dumps(goal_ads)};
        let currentGoalAd = null;
        let adTimeout = null;
        let shownAds = new Set();
        
        function initializeAds() {{
            console.log('Video loaded, initializing goal detection...');
            console.log('Goal ads configured:', goalAds);
        }}
        
        // Monitor video progress for goal moments
        video.addEventListener('timeupdate', function() {{
            const currentTime = Math.floor(video.currentTime);
            
            goalAds.forEach((ad, index) => {{
                // Show ad when reaching goal timestamp (only once per ad)
                if (currentTime >= ad.time && currentTime <= ad.time + 2) {{
                    const adKey = `goal_${{index}}_${{ad.time}}`;
                    if (!shownAds.has(adKey)) {{
                        showGoalAd(ad);
                        shownAds.add(adKey);
                    }}
                }}
            }});
        }});
        
        function showGoalAd(ad) {{
            currentGoalAd = ad;
            
            // Update ad content
            document.getElementById('playerName').textContent = ad.player;
            document.getElementById('teamName').textContent = ad.team;
            document.getElementById('jerseyPrice').textContent = '$' + ad.price.toFixed(2);
            document.getElementById('jerseyDescription').textContent = ad.description;
            
            // Show the overlay
            goalAdOverlay.style.display = 'block';
            
            // Auto-hide after duration
            if (adTimeout) clearTimeout(adTimeout);
            adTimeout = setTimeout(() => {{
                hideGoalAd();
            }}, ad.duration * 1000);
            
            console.log('Showing goal ad for:', ad.player);
        }}
        
        function hideGoalAd() {{
            goalAdOverlay.style.display = 'none';
            currentGoalAd = null;
            if (adTimeout) clearTimeout(adTimeout);
        }}
        
        function buyJersey() {{
            if (currentGoalAd) {{
                alert('🎉 Added ' + currentGoalAd.player + ' jersey to cart for $' + currentGoalAd.price.toFixed(2) + '!');
                hideGoalAd();
            }}
        }}
        
        function saveJersey() {{
            if (currentGoalAd) {{
                alert('❤️ Saved ' + currentGoalAd.player + ' jersey to wishlist!');
                hideGoalAd();
            }}
        }}
        
        // Hide ad when video is paused
        video.addEventListener('pause', hideGoalAd);
        </script>
        """
        
        return html_content

    def create_overlay_video_container(self, video_file, goal_events):
        """Create video container with CSS positioned overlay advertisements"""
        
        # Convert video to base64 for embedding
        video_bytes = video_file.read()
        video_base64 = base64.b64encode(video_bytes).decode()
        
        # Generate goal timing data
        goal_ads = []
        for i, event in enumerate(goal_events):
            timestamp_str = event.get('timestamp', f'{i*60}:00')
            # Convert timestamp to seconds
            if ':' in timestamp_str:
                parts = timestamp_str.split(':')
                if len(parts) == 2:
                    timestamp_seconds = int(parts[0]) * 60 + int(parts[1])
                else:
                    timestamp_seconds = i * 60
            else:
                timestamp_seconds = i * 60
            
            # Get player merchandise
            description = event.get('description', '')
            player_key = self.extract_player_from_event(description)
            if player_key and player_key in self.merchandise_db:
                merchandise = self.merchandise_db[player_key]
            else:
                merchandise = self.merchandise_db['messi']
            
            goal_ads.append({
                'time': timestamp_seconds,
                'player': merchandise['name'],
                'team': merchandise['team'],
                'price': merchandise['jersey_price'],
                'description': merchandise['description']
            })
        
        # Create HTML with true overlay positioning
        overlay_html = f"""
        <div style="position: relative; width: 100%; max-width: 800px; margin: 0 auto; background: #000; border-radius: 10px; overflow: hidden;">
            <!-- Video Element -->
            <video id="overlayVideo" 
                   style="width: 100%; height: 450px; object-fit: contain; display: block;" 
                   controls 
                   preload="metadata">
                <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            
            <!-- Advertisement Overlay (Initially Hidden) -->
            <div id="adOverlay" style="
                position: absolute;
                top: 20px;
                right: 20px;
                width: 280px;
                max-width: 35%;
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                color: white;
                padding: 18px;
                border-radius: 12px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.5);
                display: none;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                z-index: 9999;
                transform: translateX(100%);
                transition: transform 0.5s ease-out;
            ">
                <div style="position: absolute; top: 8px; right: 10px;">
                    <button onclick="hideAd()" style="
                        background: none; 
                        border: none; 
                        color: white; 
                        font-size: 18px; 
                        cursor: pointer;
                        opacity: 0.8;
                        padding: 2px 6px;
                        border-radius: 3px;
                    " onmouseover="this.style.background='rgba(255,255,255,0.2)'" onmouseout="this.style.background='none'">×</button>
                </div>
                
                <div style="text-align: center; margin-bottom: 12px;">
                    <div style="font-size: 14px; font-weight: bold; margin-bottom: 6px; color: #90EE90;">⚽ GOAL SCORER</div>
                    <div id="playerName" style="font-size: 18px; font-weight: bold; margin-bottom: 4px;">Player Name</div>
                    <div id="teamName" style="font-size: 13px; opacity: 0.85; margin-bottom: 10px;">Team Name</div>
                </div>
                
                <div style="background: rgba(255,255,255,0.15); padding: 12px; border-radius: 8px; margin-bottom: 12px; text-align: center;">
                    <div style="font-size: 12px; margin-bottom: 6px; opacity: 0.9;">Official Jersey</div>
                    <div id="jerseyPrice" style="font-size: 22px; font-weight: bold; color: #90EE90; margin-bottom: 4px;">$89.99</div>
                    <div style="font-size: 10px; opacity: 0.8;">Limited Time Offer</div>
                </div>
                
                <div style="display: flex; gap: 8px;">
                    <button onclick="purchaseJersey()" style="
                        flex: 1;
                        background: #4CAF50;
                        color: white;
                        border: none;
                        padding: 10px 12px;
                        border-radius: 6px;
                        font-size: 12px;
                        font-weight: bold;
                        cursor: pointer;
                        transition: background 0.3s;
                    " onmouseover="this.style.background='#45a049'" onmouseout="this.style.background='#4CAF50'">
                        🛒 Buy Now
                    </button>
                    <button onclick="saveJersey()" style="
                        flex: 1;
                        background: rgba(255,255,255,0.2);
                        color: white;
                        border: 1px solid rgba(255,255,255,0.5);
                        padding: 10px 12px;
                        border-radius: 6px;
                        font-size: 12px;
                        font-weight: bold;
                        cursor: pointer;
                        transition: background 0.3s;
                    " onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                        ❤️ Save
                    </button>
                </div>
            </div>
        </div>
        
        <script>
        (function() {{
            const video = document.getElementById('overlayVideo');
            const adOverlay = document.getElementById('adOverlay');
            const goalAds = {json.dumps(goal_ads)};
            
            let currentAd = null;
            let adTimeout = null;
            let shownAds = new Set();
            
            console.log('Video overlay system initialized with', goalAds.length, 'goal ads');
            
            // Monitor video time for goal triggers
            video.addEventListener('timeupdate', function() {{
                const currentTime = Math.floor(video.currentTime);
                
                goalAds.forEach((ad, index) => {{
                    if (currentTime >= ad.time && currentTime <= ad.time + 3) {{
                        const adKey = 'goal_' + index + '_' + ad.time;
                        if (!shownAds.has(adKey)) {{
                            showGoalAd(ad);
                            shownAds.add(adKey);
                        }}
                    }}
                }});
            }});
            
            window.showGoalAd = function(ad) {{
                currentAd = ad;
                
                // Update overlay content
                document.getElementById('playerName').textContent = ad.player;
                document.getElementById('teamName').textContent = ad.team;
                document.getElementById('jerseyPrice').textContent = '$' + ad.price.toFixed(2);
                
                // Show and animate overlay
                adOverlay.style.display = 'block';
                setTimeout(() => {{
                    adOverlay.style.transform = 'translateX(0)';
                }}, 100);
                
                // Auto-hide after 6 seconds
                if (adTimeout) clearTimeout(adTimeout);
                adTimeout = setTimeout(() => {{
                    hideAd();
                }}, 6000);
                
                console.log('Showing goal ad for:', ad.player);
            }};
            
            window.hideAd = function() {{
                adOverlay.style.transform = 'translateX(100%)';
                setTimeout(() => {{
                    adOverlay.style.display = 'none';
                }}, 500);
                currentAd = null;
                if (adTimeout) clearTimeout(adTimeout);
            }};
            
            window.purchaseJersey = function() {{
                if (currentAd) {{
                    alert('🎉 Added ' + currentAd.player + ' jersey to cart for $' + currentAd.price.toFixed(2) + '!');
                    hideAd();
                }}
            }};
            
            window.saveJersey = function() {{
                if (currentAd) {{
                    alert('❤️ Saved ' + currentAd.player + ' jersey to wishlist!');
                    hideAd();
                }}
            }};
            
            // Hide ad when video is paused
            video.addEventListener('pause', hideAd);
            
            // Test ad trigger for demo (show at 5 seconds)
            video.addEventListener('loadeddata', function() {{
                setTimeout(() => {{
                    if (goalAds.length > 0) {{
                        console.log('Demo: Triggering test ad in 5 seconds...');
                        setTimeout(() => {{
                            showGoalAd(goalAds[0]);
                        }}, 5000);
                    }}
                }}, 1000);
            }});
        }})();
        </script>
        """
        
        return overlay_html

    def create_timed_overlay_system(self, goal_events):
        """Create a timed overlay advertisement system"""
        
        # Create advertisement cards for each goal
        for i, event in enumerate(goal_events):
            timestamp_str = event.get('timestamp', f'{i*60}:00')
            description = event.get('description', '')
            
            # Get player merchandise
            player_key = self.extract_player_from_event(description)
            if player_key and player_key in self.merchandise_db:
                merchandise = self.merchandise_db[player_key]
            else:
                merchandise = self.merchandise_db['messi']
            
            # Create expandable advertisement card
            with st.expander(f"⚽ Goal at {timestamp_str} - {merchandise['name']} Jersey Ad", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                        color: white;
                        padding: 20px;
                        border-radius: 12px;
                        margin: 10px 0;
                        text-align: center;
                    ">
                        <h3 style="margin: 0 0 10px 0;">⚽ GOAL SCORER</h3>
                        <h2 style="margin: 0 0 5px 0; font-size: 24px;">{merchandise['name']}</h2>
                        <p style="margin: 0 0 15px 0; opacity: 0.9;">{merchandise['team']}</p>
                        <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;">
                            <p style="margin: 0 0 8px 0; font-size: 14px;">Official Jersey</p>
                            <h1 style="margin: 0; color: #90EE90; font-size: 32px;">${merchandise['jersey_price']:.2f}</h1>
                            <p style="margin: 8px 0 0 0; font-size: 12px; opacity: 0.8;">{merchandise['description']}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button(f"🛒 Buy {merchandise['name']} Jersey", key=f"buy_timed_{i}", type="primary"):
                        st.success(f"Added {merchandise['name']} jersey to cart for ${merchandise['jersey_price']:.2f}!")
                        st.balloons()
                    
                    if st.button(f"❤️ Save Jersey", key=f"save_timed_{i}"):
                        st.info(f"Saved {merchandise['name']} jersey to wishlist!")
                    
                    st.markdown(f"**Goal Time:** {timestamp_str}")
                    st.markdown(f"**Event:** {description}")
        
        # Add automatic overlay simulation
        st.markdown("---")
        st.markdown("#### Overlay Advertisement Simulation")
        
        # Create a simulated overlay that appears automatically
        placeholder = st.empty()
        
        if st.button("🎬 Simulate Goal Advertisement Overlay", type="secondary"):
            if goal_events:
                # Show first goal's advertisement
                event = goal_events[0]
                player_key = self.extract_player_from_event(event.get('description', ''))
                if player_key and player_key in self.merchandise_db:
                    merchandise = self.merchandise_db[player_key]
                else:
                    merchandise = self.merchandise_db['messi']
                
                # Display overlay-style advertisement
                with placeholder.container():
                    st.markdown(f"""
                    <div style="
                        position: fixed;
                        top: 100px;
                        right: 20px;
                        width: 300px;
                        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                        color: white;
                        padding: 20px;
                        border-radius: 15px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                        z-index: 9999;
                        animation: slideIn 0.8s ease-out;
                        border: 2px solid #fff;
                    ">
                        <div style="text-align: center;">
                            <h2 style="margin: 0 0 10px 0; font-size: 20px;">⚽ GOAL!</h2>
                            <h3 style="margin: 0 0 5px 0;">{merchandise['name']}</h3>
                            <p style="margin: 0 0 15px 0; opacity: 0.9;">{merchandise['team']}</p>
                            <div style="background: rgba(255,255,255,0.2); padding: 12px; border-radius: 8px;">
                                <p style="margin: 0 0 8px 0; font-size: 12px;">Get the Jersey!</p>
                                <h2 style="margin: 0; color: #90EE90;">${merchandise['jersey_price']:.2f}</h2>
                            </div>
                        </div>
                    </div>
                    <style>
                    @keyframes slideIn {{
                        from {{ transform: translateX(100%); opacity: 0; }}
                        to {{ transform: translateX(0); opacity: 1; }}
                    }}
                    </style>
                    """, unsafe_allow_html=True)
                
                # Auto-clear after 3 seconds
                import time
                time.sleep(3)
                placeholder.empty()
                
                st.success("Advertisement overlay simulation complete!")

    def create_interactive_video_player(self, video_file, goal_events):
        """Create an interactive video player with working overlay advertisements"""
        
        # Display the video using Streamlit's native player
        st.video(video_file)
        
        # Create goal-based advertisement system
        if goal_events:
            st.markdown("### Goal-Triggered Jersey Advertisements")
            st.info(f"Found {len(goal_events)} goal moments with automatic jersey targeting")
            
            # Create advertisement display area
            # Removed problematic placeholder
            
            # Show goal timeline with interactive advertisements
            st.markdown("#### Goal Timeline & Advertisement System")
            
            for i, event in enumerate(goal_events):
                timestamp_str = event.get('timestamp', f'{i*60}:00')
                description = event.get('description', '')
                
                # Get player merchandise
                player_key = self.extract_player_from_event(description)
                if player_key and player_key in self.merchandise_db:
                    merchandise = self.merchandise_db[player_key]
                else:
                    merchandise = self.merchandise_db['messi']
                
                # Create collapsible goal advertisement
                with st.expander(f"⚽ {timestamp_str} - {merchandise['name']} Goal Advertisement"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(45deg, #ff6b6b, #ee5a52);
                            color: white;
                            padding: 20px;
                            border-radius: 15px;
                            text-align: center;
                            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
                        ">
                            <h3 style="margin: 0 0 10px 0; color: #90EE90;">⚽ GOAL SCORER</h3>
                            <h2 style="margin: 0 0 8px 0; font-size: 28px;">{merchandise['name']}</h2>
                            <p style="margin: 0 0 15px 0; font-size: 16px; opacity: 0.9;">{merchandise['team']}</p>
                            <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px;">
                                <p style="margin: 0 0 8px 0; font-size: 14px;">Official Jersey</p>
                                <h1 style="margin: 0; color: #90EE90; font-size: 36px;">${merchandise['jersey_price']:.2f}</h1>
                                <p style="margin: 8px 0 0 0; font-size: 12px; opacity: 0.8;">{merchandise['description']}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if st.button(f"🛒 Buy Jersey", key=f"buy_interactive_{i}", type="primary"):
                            st.success(f"Added {merchandise['name']} jersey to cart!")
                            st.balloons()
                        
                        if st.button(f"❤️ Save", key=f"save_interactive_{i}"):
                            st.info(f"Saved {merchandise['name']} jersey to wishlist!")
                    
                    with col3:
                        st.metric("Goal Time", timestamp_str)
                        st.metric("Price", f"${merchandise['jersey_price']:.2f}")
                        st.write(f"**Player:** {merchandise['name']}")
                        st.write(f"**Team:** {merchandise['team']}")
            
            # Add overlay simulation button
            st.markdown("---")
            if st.button("🎬 Test Overlay Advertisement", type="secondary"):
                if goal_events:
                    event = goal_events[0]
                    player_key = self.extract_player_from_event(event.get('description', ''))
                    if player_key and player_key in self.merchandise_db:
                        merchandise = self.merchandise_db[player_key]
                    else:
                        merchandise = self.merchandise_db['messi']
                    
                    # Display overlay advertisement
                    st.markdown(f"""
                        <div style="
                            position: relative;
                            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                            color: white;
                            padding: 25px;
                            border-radius: 20px;
                            margin: 20px 0;
                            box-shadow: 0 15px 35px rgba(255,107,107,0.4);
                            border: 3px solid #fff;
                            text-align: center;
                            animation: bounce 1s ease-in-out;
                        ">
                            <h1 style="margin: 0 0 15px 0; font-size: 32px; color: #90EE90;">⚽ GOAL!</h1>
                            <h2 style="margin: 0 0 10px 0; font-size: 28px;">{merchandise['name']}</h2>
                            <p style="margin: 0 0 20px 0; font-size: 18px; opacity: 0.9;">{merchandise['team']}</p>
                            <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 15px; margin-bottom: 20px;">
                                <p style="margin: 0 0 10px 0; font-size: 16px;">Get the Official Jersey!</p>
                                <h1 style="margin: 0; color: #90EE90; font-size: 40px;">${merchandise['jersey_price']:.2f}</h1>
                                <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.8;">Limited Time Offer</p>
                            </div>
                            <p style="margin: 0; font-size: 14px; opacity: 0.7;">This overlay would appear automatically during the goal moment</p>
                        </div>
                        <style>
                        @keyframes bounce {{
                            0%, 20%, 50%, 80%, 100% {{ transform: translateY(0); }}
                            40% {{ transform: translateY(-10px); }}
                            60% {{ transform: translateY(-5px); }}
                        }}
                        </style>
                        """, unsafe_allow_html=True)
                    
                    st.success("Overlay advertisement test complete! In a full implementation, this would appear automatically during goal moments.")

    def display_video_with_overlay_ads(self, video_file, commentary_text, language='en'):
        """Display video with true overlay advertisements for goals only"""
        
        # Convert video to base64
        video_bytes = video_file.read()
        video_base64 = base64.b64encode(video_bytes).decode()
        
        # Extract only goal events from commentary
        analyzer = SoccerAnalyzer(language)
        analysis_result = analyzer.analyze_commentary(commentary_text)
        
        goal_events = []
        if analysis_result and isinstance(analysis_result, dict) and 'events' in analysis_result:
            events = analysis_result['events']
            for event in events:
                event_type = event.get('type', '').lower()
                if 'goal' in event_type or 'score' in event_type:
                    goal_events.append(event)
        
        # If no goals detected, create demo goals for testing
        if not goal_events:
            goal_events = [
                {'timestamp': '0:30', 'type': 'goal', 'description': 'Amazing goal by Messi'},
                {'timestamp': '1:45', 'type': 'goal', 'description': 'Brilliant strike by Ronaldo'}
            ]
        
        # Display video with overlay ads
        st.markdown("#### Video Player with Goal-Triggered Jersey Advertisements")
        st.info(f"Found {len(goal_events)} goal moments - jersey ads will appear automatically during goals!")
        
        # Display the video using Streamlit's native player
        st.video(video_file)
        
        # Create goal-based advertisement system
        if goal_events:
            st.markdown("### Goal-Triggered Jersey Advertisements")
            st.info(f"Found {len(goal_events)} goal moments with automatic jersey targeting")
            
            # Create advertisement display area
            # Removed problematic placeholder
            
            # Show goal timeline with interactive advertisements
            st.markdown("#### Goal Timeline & Advertisement System")
            
            for i, event in enumerate(goal_events):
                timestamp_str = event.get('timestamp', f'{i*60}:00')
                description = event.get('description', '')
                
                # Get player merchandise
                player_key = self.extract_player_from_event(description)
                if player_key and player_key in self.merchandise_db:
                    merchandise = self.merchandise_db[player_key]
                else:
                    merchandise = self.merchandise_db['messi']
                
                # Create collapsible goal advertisement
                with st.expander(f"⚽ {timestamp_str} - {merchandise['name']} Goal Advertisement"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(45deg, #ff6b6b, #ee5a52);
                            color: white;
                            padding: 20px;
                            border-radius: 15px;
                            text-align: center;
                            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
                        ">
                            <h3 style="margin: 0 0 10px 0; color: #90EE90;">⚽ GOAL SCORER</h3>
                            <h2 style="margin: 0 0 8px 0; font-size: 28px;">{merchandise['name']}</h2>
                            <p style="margin: 0 0 15px 0; font-size: 16px; opacity: 0.9;">{merchandise['team']}</p>
                            <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px;">
                                <p style="margin: 0 0 8px 0; font-size: 14px;">Official Jersey</p>
                                <h1 style="margin: 0; color: #90EE90; font-size: 36px;">${merchandise['jersey_price']:.2f}</h1>
                                <p style="margin: 8px 0 0 0; font-size: 12px; opacity: 0.8;">{merchandise['description']}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if st.button(f"🛒 Buy Jersey", key=f"buy_interactive_{i}", type="primary"):
                            st.success(f"Added {merchandise['name']} jersey to cart!")
                            st.balloons()
                        
                        if st.button(f"❤️ Save", key=f"save_interactive_{i}"):
                            st.info(f"Saved {merchandise['name']} jersey to wishlist!")
                    
                    with col3:
                        st.metric("Goal Time", timestamp_str)
                        st.metric("Price", f"${merchandise['jersey_price']:.2f}")
                        st.write(f"**Player:** {merchandise['name']}")
                        st.write(f"**Team:** {merchandise['team']}")
            
            # Add overlay simulation button
            st.markdown("---")
            if st.button("🎬 Test Overlay Advertisement", type="secondary"):
                if goal_events:
                    event = goal_events[0]
                    player_key = self.extract_player_from_event(event.get('description', ''))
                    if player_key and player_key in self.merchandise_db:
                        merchandise = self.merchandise_db[player_key]
                    else:
                        merchandise = self.merchandise_db['messi']
                    
                    # Display overlay advertisement
                    st.markdown(f"""
                        <div style="
                            position: relative;
                            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                            color: white;
                            padding: 25px;
                            border-radius: 20px;
                            margin: 20px 0;
                            box-shadow: 0 15px 35px rgba(255,107,107,0.4);
                            border: 3px solid #fff;
                            text-align: center;
                            animation: bounce 1s ease-in-out;
                        ">
                            <h1 style="margin: 0 0 15px 0; font-size: 32px; color: #90EE90;">⚽ GOAL!</h1>
                            <h2 style="margin: 0 0 10px 0; font-size: 28px;">{merchandise['name']}</h2>
                            <p style="margin: 0 0 20px 0; font-size: 18px; opacity: 0.9;">{merchandise['team']}</p>
                            <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 15px; margin-bottom: 20px;">
                                <p style="margin: 0 0 10px 0; font-size: 16px;">Get the Official Jersey!</p>
                                <h1 style="margin: 0; color: #90EE90; font-size: 40px;">${merchandise['jersey_price']:.2f}</h1>
                                <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.8;">Limited Time Offer</p>
                            </div>
                            <p style="margin: 0; font-size: 14px; opacity: 0.7;">This overlay would appear automatically during the goal moment</p>
                        </div>
                        <style>
                        @keyframes bounce {{
                            0%, 20%, 50%, 80%, 100% {{ transform: translateY(0); }}
                            40% {{ transform: translateY(-10px); }}
                            60% {{ transform: translateY(-5px); }}
                        }}
                        </style>
                        """, unsafe_allow_html=True)
                    
                    st.success("Overlay advertisement test complete! In a full implementation, this would appear automatically during goal moments.")
        
        # Add manual goal trigger for testing
        st.markdown("---")
        st.markdown("### 🎯 Test Advertisement System")
        
        if goal_events:
            selected_goal = st.selectbox(
                "Test advertisement for goal:",
                options=range(len(goal_events)),
                format_func=lambda x: f"{goal_events[x].get('timestamp', f'{x*60}:00')} - {goal_events[x].get('description', '')}"
            )
            
            if st.button("🎬 Show Goal Advertisement", type="secondary"):
                goal = goal_events[selected_goal]
                player_key = self.extract_player_from_event(goal.get('description', ''))
                if player_key and player_key in self.merchandise_db:
                    merchandise = self.merchandise_db[player_key]
                else:
                    merchandise = self.merchandise_db['messi']
                
                st.markdown(f"""
                <div style="
                    position: relative;
                    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 15px;
                    margin: 10px 0;
                    box-shadow: 0 8px 32px rgba(255,107,107,0.4);
                    animation: slideIn 0.8s ease-out;
                ">
                    <div style="text-align: center; margin-bottom: 15px;">
                        <h2 style="margin: 0; font-size: 24px;">⚽ GOAL!</h2>
                        <h3 style="margin: 5px 0; font-size: 20px;">{merchandise['name']}</h3>
                        <p style="margin: 0; font-size: 16px; opacity: 0.9;">{merchandise['team']}</p>
                    </div>
                    <div style="background: rgba(255,255,255,0.15); padding: 15px; border-radius: 10px; text-align: center;">
                        <p style="margin: 0 0 10px 0; font-size: 14px;">Get the official jersey!</p>
                        <h2 style="margin: 0; font-size: 28px; color: #90EE90;">${merchandise['jersey_price']:.2f}</h2>
                        <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.8;">{merchandise['description']}</p>
                    </div>
                </div>
                <style>
                @keyframes slideIn {{
                    from {{ transform: translateX(100%); opacity: 0; }}
                    to {{ transform: translateX(0); opacity: 1; }}
                }}
                </style>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"🛒 Buy {merchandise['name']} Jersey", key="demo_buy", type="primary"):
                        st.success(f"Added {merchandise['name']} jersey to cart!")
                        st.balloons()
                with col2:
                    if st.button(f"❤️ Save Jersey", key="demo_save"):
                        st.info(f"Saved {merchandise['name']} jersey to wishlist!")
        
        # Show goal summary
        if goal_events:
            st.markdown("---")
            st.markdown("#### Goal Moments & Jersey Advertisements")
            
            for i, goal in enumerate(goal_events):
                timestamp = goal.get('timestamp', f'{i*60}:00')
                description = goal.get('description', '')
                
                # Determine jersey to show
                player_key = self.extract_player_from_event(description)
                if player_key and player_key in self.merchandise_db:
                    merchandise = self.merchandise_db[player_key]
                    jersey_info = f"{merchandise['name']} ({merchandise['team']}) - ${merchandise['jersey_price']:.2f}"
                else:
                    jersey_info = "Messi Jersey (Demo) - $89.99"
                
                st.write(f"**{timestamp}** - {description} → {jersey_info}")
        
        st.success("🎯 Goal detection active! Jersey ads will pop up automatically when goals occur in the video.")

    def display_video_player(self, video_file, commentary_text, language='en'):
        """Display video player with contextual advertisements"""
        
        # Convert video file to base64 for display
        video_bytes = video_file.read()
        video_base64 = base64.b64encode(video_bytes).decode()
        
        # Extract events from commentary for ad targeting
        analyzer = SoccerAnalyzer(language)
        analysis_result = analyzer.analyze_commentary(commentary_text)
        
        highlight_events = []
        if analysis_result and isinstance(analysis_result, dict) and 'events' in analysis_result:
            events = analysis_result['events']
            for event in events:
                event_type = event.get('type', '').lower()
                if any(keyword in event_type for keyword in ['goal', 'score', 'card', 'assist']):
                    highlight_events.append(event)
        
        # If no highlights found, create demo ads for testing
        if not highlight_events:
            highlight_events = [
                {'timestamp': '0:30', 'type': 'goal', 'description': 'Amazing goal by Messi'},
                {'timestamp': '1:15', 'type': 'card', 'description': 'Yellow card shown'},
                {'timestamp': '2:00', 'type': 'highlight', 'description': 'Great play'}
            ]
        
        # Create and display the video player with goal-triggered jersey ads
        self.display_video_with_overlay_ads(video_file, commentary_text, language)

class SoccerAnalyzer:
    def __init__(self, language='en'):
        self.language = language
        
        # Soccer-specific keywords and patterns (English)
        self.event_patterns_en = {
            'goal': r'\b(?:goal|scores?|scored|scoring|nets?|finds?\s+the\s+net|back\s+of\s+the\s+net)\b',
            'assist': r'\b(?:assist|assists|assisted|sets?\s+up|crosses?|passes?)\b',
            'yellow_card': r'\b(?:yellow\s+card|booked|cautioned|warning)\b',
            'red_card': r'\b(?:red\s+card|sent\s+off|dismissed|ejected)\b',
            'substitution': r'\b(?:substitut\w+|sub\w+|replaces?|comes?\s+on|off\s+for)\b',
            'corner': r'\b(?:corner|corner\s+kick)\b',
            'free_kick': r'\b(?:free\s+kick|direct\s+kick|indirect\s+kick)\b',
            'penalty': r'\b(?:penalty|penalty\s+kick|from\s+the\s+spot)\b',
            'offside': r'\b(?:offside|offside\s+trap)\b',
            'foul': r'\b(?:foul|fouled|commits?\s+a\s+foul)\b',
            'save': r'\b(?:save|saves?|saved|blocks?|stopped)\b',
            'shot': r'\b(?:shot|shoots?|shooting|attempt)\b',
            'header': r'\b(?:header|heads?|heading)\b',
            'tackle': r'\b(?:tackle|tackles?|tackled)\b'
        }
        
        # Soccer-specific keywords and patterns (Spanish)
        self.event_patterns_es = {
            'goal': r'\b(?:gol|goles|marca|anota|anotó|anotando|convierte|convertir)\b',
            'assist': r'\b(?:asistencia|asiste|pase|habilitación|habilita|centro|centrar)\b',
            'yellow_card': r'\b(?:tarjeta\s+amarilla|amarilla|amonestado|amonestación|advertencia)\b',
            'red_card': r'\b(?:tarjeta\s+roja|roja|expulsado|expulsión|echado)\b',
            'substitution': r'\b(?:sustitución|cambio|sustituye|reemplaza|entra|sale|ingresa)\b',
            'corner': r'\b(?:córner|corner|saque\s+de\s+esquina|tiro\s+de\s+esquina)\b',
            'free_kick': r'\b(?:tiro\s+libre|libre|falta|directo|indirecto)\b',
            'penalty': r'\b(?:penalty|penalti|penal|desde\s+los\s+once\s+metros)\b',
            'offside': r'\b(?:fuera\s+de\s+juego|offside|posición\s+adelantada)\b',
            'foul': r'\b(?:falta|infracción|comete\s+falta|golpe)\b',
            'save': r'\b(?:atajada|parada|ataja|para|detiene|bloquea)\b',
            'shot': r'\b(?:disparo|tiro|remate|intento|lanza|patea)\b',
            'header': r'\b(?:cabezazo|cabecea|de\s+cabeza|remate\s+de\s+cabeza)\b',
            'tackle': r'\b(?:entrada|barrida|anticipo|recupera|quita)\b'
        }
        
        # Select patterns based on language
        self.event_patterns = self.event_patterns_es if language == 'es' else self.event_patterns_en
        
        # Common soccer player names (English/International)
        self.common_player_names_en = [
            'Messi', 'Ronaldo', 'Neymar', 'Mbappe', 'Benzema', 'Modric', 'Ramos', 
            'Pique', 'Iniesta', 'Xavi', 'Busquets', 'Griezmann', 'Haaland', 
            'Lewandowski', 'Salah', 'Kane', 'Sterling', 'De Bruyne', 'Mahrez',
            'Giroud', 'Casemiro', 'Kroos', 'Bale', 'Suarez', 'Alba', 'Ter Stegen'
        ]
        
        # Common soccer player names (Spanish/Latin American)
        self.common_player_names_es = [
            'Messi', 'Ronaldo', 'Neymar', 'Mbappé', 'Benzema', 'Modrić', 'Ramos',
            'Piqué', 'Iniesta', 'Xavi', 'Busquets', 'Griezmann', 'Haaland',
            'Lewandowski', 'Salah', 'Kane', 'Sterling', 'De Bruyne', 'Mahrez',
            'Giroud', 'Casemiro', 'Kroos', 'Bale', 'Suárez', 'Alba', 'Ter Stegen',
            'Vinicius', 'Pedri', 'Gavi', 'Ansu Fati', 'Rodrygo', 'Valverde',
            'Camavinga', 'Tchouaméni', 'Bellingham', 'Luka Modrić', 'Toni Kroos'
        ]
        
        # Common team names (English)
        self.team_names_en = [
            'Barcelona', 'Real Madrid', 'PSG', 'Manchester United', 'Manchester City',
            'Liverpool', 'Chelsea', 'Arsenal', 'Tottenham', 'Bayern Munich',
            'Borussia Dortmund', 'Juventus', 'AC Milan', 'Inter Milan', 'Atletico Madrid'
        ]
        
        # Common team names (Spanish)
        self.team_names_es = [
            'Barcelona', 'Real Madrid', 'Atlético Madrid', 'Sevilla', 'Valencia',
            'Athletic Bilbao', 'Real Sociedad', 'Villarreal', 'Betis', 'Getafe',
            'Boca Juniors', 'River Plate', 'Independiente', 'Racing', 'San Lorenzo',
            'América', 'Chivas', 'Cruz Azul', 'Pumas', 'Tigres'
        ]
        
        # Select names based on language
        self.common_player_names = self.common_player_names_es if language == 'es' else self.common_player_names_en
        self.team_names = self.team_names_es if language == 'es' else self.team_names_en
    
    def extract_timestamps(self, text):
        """Extract timestamps from text in various formats"""
        # Pattern for MM:SS or HH:MM:SS format
        timestamp_patterns = [
            r'\b(\d{1,2}):(\d{2})\b',  # MM:SS
            r'\b(\d{1,2}):(\d{2}):(\d{2})\b',  # HH:MM:SS
            r'\b(\d{1,3})\'',  # 45' format (minutes with apostrophe)
            r'\b(\d{1,3})\s*min\b',  # 45 min format
        ]
        
        timestamps = []
        for pattern in timestamp_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                timestamps.append({
                    'raw': match.group(0),
                    'start': match.start(),
                    'end': match.end(),
                    'groups': match.groups()
                })
        
        return timestamps
    
    def extract_events(self, text):
        """Extract soccer events from text"""
        events = []
        
        for event_type, pattern in self.event_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                events.append({
                    'type': event_type,
                    'text': match.group(0),
                    'start': match.start(),
                    'end': match.end()
                })
        
        return events
    
    def extract_players_and_entities(self, text):
        """Extract player names and entities using pattern matching"""
        entities = []
        
        # Find player names
        for player in self.common_player_names:
            pattern = r'\b' + re.escape(player) + r'\b'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group(0),
                    'label': 'PERSON',
                    'start': match.start(),
                    'end': match.end()
                })
        
        # Find team names
        for team in self.team_names:
            pattern = r'\b' + re.escape(team) + r'\b'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group(0),
                    'label': 'ORG',
                    'start': match.start(),
                    'end': match.end()
                })
        
        # Find capitalized words that might be player names (simple heuristic)
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b'
        matches = re.finditer(name_pattern, text)
        for match in matches:
            name = match.group(0)
            # Skip common words and already found names
            if (name not in ['Goal', 'Card', 'Free', 'Corner', 'Penalty', 'The', 'And', 'But', 'After'] and 
                not any(entity['text'].lower() == name.lower() for entity in entities)):
                entities.append({
                    'text': name,
                    'label': 'PERSON',
                    'start': match.start(),
                    'end': match.end()
                })
        
        return entities
    
    def find_nearby_elements(self, timestamps, events, entities, text, window=50):
        """Find events and entities near timestamps"""
        results = []
        
        for timestamp in timestamps:
            ts_start = timestamp['start']
            ts_end = timestamp['end']
            
            # Find events and entities within the window
            nearby_events = []
            nearby_entities = []
            
            # Look for events within the window around the timestamp
            for event in events:
                if abs(event['start'] - ts_start) <= window or abs(event['end'] - ts_end) <= window:
                    nearby_events.append(event)
            
            # Look for entities within the window around the timestamp
            for entity in entities:
                if abs(entity['start'] - ts_start) <= window or abs(entity['end'] - ts_end) <= window:
                    nearby_entities.append(entity)
            
            # Extract surrounding context
            context_start = max(0, ts_start - window)
            context_end = min(len(text), ts_end + window)
            context = text[context_start:context_end].strip()
            
            results.append({
                'timestamp': timestamp['raw'],
                'events': nearby_events,
                'entities': nearby_entities,
                'context': context
            })
        
        return results
    
    def analyze_commentary(self, text):
        """Main analysis function"""
        if not text.strip():
            return []
        
        # Extract all components
        timestamps = self.extract_timestamps(text)
        events = self.extract_events(text)
        entities = self.extract_players_and_entities(text)
        
        # Find relationships between timestamps and events/entities
        analysis_results = self.find_nearby_elements(timestamps, events, entities, text)
        
        # Format results
        formatted_results = []
        for result in analysis_results:
            event_types = list(set([event['type'] for event in result['events']]))
            player_names = [entity['text'] for entity in result['entities'] if entity['label'] == 'PERSON']
            team_names = [entity['text'] for entity in result['entities'] if entity['label'] == 'ORG']
            
            tags = []
            tags.extend(event_types)
            tags.extend(player_names)
            tags.extend(team_names)
            
            formatted_results.append({
                'Time': result['timestamp'],
                'Tags': ', '.join(tags) if tags else 'General mention',
                'Context': result['context'][:100] + '...' if len(result['context']) > 100 else result['context']
            })
        
        return formatted_results

def main():
    st.title("Soccer Game Analysis Tool")
    st.markdown("Extract timestamped key events and player mentions from match commentary or MP4 videos")
    
    # Language selection
    st.header("Language Selection")
    language = st.selectbox(
        "Choose the language for analysis:",
        ["English", "Español (Spanish)"],
        help="Select the language of your commentary or video audio"
    )
    
    # Convert to language code
    lang_code = 'es' if language == "Español (Spanish)" else 'en'
    
    # Initialize components with selected language
    analyzer = SoccerAnalyzer(language=lang_code)
    video_processor = VideoProcessor()
    
    # Input method selection
    st.header("Choose Input Method")
    input_method = st.radio(
        "Select how you want to provide the soccer content:",
        ["Text Commentary", "MP4 Video File"],
        help="Choose text for manual commentary input, or video to automatically extract and analyze audio"
    )
    
    commentary_text = ""
    
    if input_method == "MP4 Video File":
        st.header("Video Upload")
        
        # Check available processing methods
        aws_available = video_processor.s3_client and video_processor.transcribe_client
        local_available = video_processor.local_stt_available
        
        if not aws_available and not local_available:
            st.error("No video processing methods available. Please install required dependencies.")
            st.markdown("""
            **Available Options:**
            1. **AWS Processing**: Requires AWS credentials and account setup
            2. **Local Processing**: Requires speech recognition libraries (already installed)
            """)
        else:
            # Processing method selection
            processing_options = []
            if local_available:
                processing_options.append("Local Processing (No Cloud)")
            if aws_available:
                processing_options.append("AWS Cloud Processing")
            
            if len(processing_options) > 1:
                processing_method = st.radio(
                    "Choose processing method:",
                    processing_options,
                    help="Local processing works offline but may be less accurate. AWS processing requires credentials but is more accurate."
                )
            else:
                processing_method = processing_options[0]
                st.info(f"Using: {processing_method}")
            
            if not aws_available and "AWS" in processing_method:
                st.warning("AWS credentials not configured.")
                st.markdown("""
                **To use AWS processing:**
                1. An AWS account
                2. AWS credentials configured (Access Key ID and Secret Access Key)
                3. Permissions for S3 and Transcribe services
                """)
            else:
                uploaded_file = st.file_uploader(
                    "Upload your soccer match MP4 video (up to 300MB)",
                    type=['mp4'],
                    help="Upload an MP4 video file containing soccer commentary. The audio will be extracted and transcribed automatically."
                )
                
                if uploaded_file is not None:
                    st.success(f"Video uploaded: {uploaded_file.name} ({uploaded_file.size} bytes)")
                    
                    if st.button("Process Video and Extract Commentary", type="primary"):
                        with st.spinner("Processing video... This may take several minutes."):
                            try:
                                # Choose processing method
                                if "Local" in processing_method:
                                    result = video_processor.process_video_locally(uploaded_file, lang_code)
                                else:
                                    result = video_processor.process_video_file(uploaded_file)
                                
                                if result and result.get('status') == 'completed':
                                    st.success("Video processed successfully!")
                                    
                                    # Use the actual transcript from processing
                                    commentary_text = result.get('transcript', '')
                                    if commentary_text and commentary_text != "No speech detected in the audio.":
                                        st.text_area("Generated Commentary:", value=commentary_text, height=200)
                                    else:
                                        st.warning("No clear speech was detected in the video.")
                                        commentary_text = ""
                                        
                                elif result and result.get('status') == 'no_speech':
                                    st.warning("No clear speech detected in the video")
                                    
                                    # Show suggestions to help the user
                                    if result.get('suggestions'):
                                        st.info("**Suggestions to improve results:**")
                                        for suggestion in result['suggestions']:
                                            st.write(f"• {suggestion}")
                                    
                                    # Show audio analysis if available
                                    if result.get('audio_analysis'):
                                        analysis = result['audio_analysis']
                                        st.write("**Audio Analysis:**")
                                        st.write(f"Duration: {analysis.get('duration', 0):.1f} seconds")
                                        st.write(f"Volume: {analysis.get('volume_db', 0):.1f} dB")
                                        st.write(f"Speech activity: {analysis.get('speech_ratio', 0):.1%}")
                                    
                                    commentary_text = ""
                
                                elif result and result.get('status') == 'timeout':
                                    st.warning(f"Transcription started but not completed: {result.get('message')}")
                                    st.info("Job Name: " + result.get('job_name', 'Unknown'))
                                    commentary_text = ""
                                else:
                                    st.error("Failed to process video. Please try again.")
                                    commentary_text = ""
                                    
                            except Exception as e:
                                st.error(f"Error processing video: {str(e)}")
                                commentary_text = ""
                        
                        # Manual commentary input option
                        if uploaded_file:
                            st.markdown("---")
                            st.markdown("#### Manual Commentary Input")
                            st.info("Add or edit commentary to improve goal detection accuracy")
                            
                            manual_commentary = st.text_area(
                                "Add or edit commentary:",
                                value=commentary_text,
                                height=150,
                                help="Add goal descriptions like '15:30 - Amazing goal by Messi' or '2:45 - Ronaldo scores from penalty'"
                            )
                            
                            if manual_commentary.strip():
                                commentary_text = manual_commentary
                        
                        # If we have a video and commentary, show video player with ads
                        if uploaded_file and commentary_text:
                            st.markdown("---")
                            st.subheader("Video Player with Goal-Triggered Jersey Advertisements")
                            
                            # Create video player with advertisement system
                            video_player = VideoPlayerWithAds()
                            video_player.display_video_with_overlay_ads(uploaded_file, commentary_text, lang_code)
    
    else:  # Text Commentary
        st.header("Input Commentary")
        
        # Option to use example or custom input
        input_option = st.radio(
            "Choose input method:",
            ["Enter custom commentary", "Use example commentary"]
        )
        
        if input_option == "Use example commentary":
            if lang_code == 'es':
                example_text = """15' Gran disparo de Ronaldo, pero el portero hace una excelente atajada
23' ¡GOL! Messi anota un gol brillante después de una perfecta asistencia de Neymar
31' Tarjeta amarilla para Ramos después de una fuerte entrada al mediocampista
45' Córner para el Barcelona, Piqué cabecea pero se va desviado
67' Sustitución: Benzema entra por Giroud
78' ¡Penalty! Mbappé es derribado en el área
79' ¡GOL! Mbappé convierte el penal para hacer el 2-0
85' ¡Tarjeta roja! Casemiro es expulsado por una entrada peligrosa
90' Silbato final, el Barcelona gana 2-0"""
            else:
                example_text = """15' Great shot by Ronaldo, but the goalkeeper makes an excellent save
23' GOAL! Messi scores a brilliant goal after a perfect assist from Neymar
31' Yellow card for Ramos after a hard tackle on the midfielder
45' Corner kick for Barcelona, Pique heads it just wide
67' Substitution: Benzema comes on for Giroud
78' Penalty! Mbappé is fouled in the box
79' GOAL! Mbappé converts the penalty to make it 2-0
85' Red card! Casemiro is sent off for a dangerous tackle
90' Full time whistle, Barcelona wins 2-0"""
            commentary_text = st.text_area(
                "Commentary text:",
                value=example_text,
                height=200,
                help="You can edit this example or paste your own commentary"
            )
        else:
            if lang_code == 'es':
                placeholder_text = "Ingrese comentarios del partido con marcas de tiempo (ej: '15' Gol de Ronaldo...')"
                help_text = "Incluya marcas de tiempo en formatos como 15', 1:23, o 1:23:45"
            else:
                placeholder_text = "Enter match commentary with timestamps (e.g., '15' Goal by Ronaldo...')"
                help_text = "Include timestamps in formats like 15', 1:23, or 1:23:45"
                
            commentary_text = st.text_area(
                "Paste match commentary here:" if lang_code == 'en' else "Pegue aquí los comentarios del partido:",
                height=200,
                placeholder=placeholder_text,
                help=help_text
            )
    
    # Analysis section
    if st.button("Analyze Commentary", type="primary"):
        if not commentary_text.strip():
            st.warning("Please enter some commentary text to analyze.")
            return
        
        with st.spinner("Analyzing commentary..."):
            try:
                results = analyzer.analyze_commentary(commentary_text)
                
                if not results:
                    st.info("No timestamped events found in the commentary. Make sure to include timestamps in formats like '15', '1:23', or '1:23:45'.")
                else:
                    st.success(f"Found {len(results)} timestamped events!")
                    
                    # Display results
                    st.header("Analysis Results")
                    
                    # Display results as a simple table
                    for i, result in enumerate(results, 1):
                        st.write(f"**{i}. {result['Time']}** - {result['Tags']}")
                        if result['Context']:
                            st.write(f"   *{result['Context']}*")
                        st.write("---")
                    
                    # Summary statistics
                    st.header("Summary")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Events", len(results))
                    
                    with col2:
                        # Count unique event types mentioned
                        all_tags = []
                        for result in results:
                            if result['Tags'] != 'General mention':
                                all_tags.extend([tag.strip() for tag in result['Tags'].split(',')])
                        unique_events = len(set(all_tags))
                        st.metric("Unique Event Types", unique_events)
                    
                    with col3:
                        # Count player mentions
                        player_mentions = sum(1 for result in results if any(tag.strip().istitle() and len(tag.strip().split()) <= 2 for tag in result['Tags'].split(',') if tag.strip() != 'General mention'))
                        st.metric("Player Mentions", player_mentions)
            
            except Exception as e:
                st.error(f"An error occurred during analysis: {str(e)}")
                st.error("Please check your input format and try again.")
    
    # Instructions section
    with st.expander("How to use this tool"):
        st.markdown("""
        **Input Format:**
        - Include timestamps in your commentary (e.g., 15', 1:23, 90+2')
        - Mention player names and events clearly
        - Use standard soccer terminology
        
        **Supported Events:**
        - Goals and assists
        - Cards (yellow/red)
        - Substitutions
        - Corners, free kicks, penalties
        - Fouls, saves, shots
        - And more!
        
        **Video Processing:**
        - Upload MP4 files to automatically extract and analyze audio
        - Requires AWS credentials for transcription services
        - Supports automatic speech-to-text conversion
        
        **Example Input:**
        ```
        23' GOAL! Messi scores after assist from Iniesta
        45' Yellow card for Sergio Ramos
        67' Substitution: Benzema replaces Giroud
        ```
        """)

if __name__ == "__main__":
    main()