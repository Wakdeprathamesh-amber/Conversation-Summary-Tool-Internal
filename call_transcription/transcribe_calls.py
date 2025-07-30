import os
import json
import logging
import time
import requests
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse
import re
import assemblyai as aai
from dotenv import load_dotenv

# FastAPI imports for API endpoint
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse, JSONResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# Import storage manager
from storage_manager import StorageManager

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('transcribe_calls.log'),
        logging.StreamHandler()
    ]
)

# Configuration
aai.settings.api_key = os.getenv('ASSEMBLYAI_API_KEY', 'YOUR_API_KEY_HERE')
TRANSCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'transcripts')
CALLS_INPUT_FILE = 'calls_to_transcribe.json'
PROGRESS_FILE = 'transcription_progress.json'

# Initialize storage manager
storage_manager = StorageManager(max_age_days=7, max_files_per_mobile=50)

# Transcription configuration
TRANSCRIPTION_CONFIG = {
    'speech_model': aai.SpeechModel.best,
    'speaker_labels': True,
    'format_text': True,
    'punctuate': True,
    'dual_channel': False,
    'word_boost': [],
    'boost_param': 'default',
    'language_detection': True,
    'auto_highlights': True
}

# Processing configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
RATE_LIMIT_DELAY = 1.5  # seconds between requests
REQUEST_TIMEOUT = 30  # seconds

os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

class TranscriptionManager:
    def __init__(self):
        self.progress = self.load_progress()
        self.failed_urls = []
        self.successful_count = 0
        self.failed_count = 0
    
    def load_progress(self) -> Dict:
        """Load progress from previous runs"""
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Could not load progress file: {e}")
        return {'completed_urls': [], 'failed_urls': []}
    
    def save_progress(self):
        """Save current progress"""
        try:
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Could not save progress: {e}")
    
    def is_url_completed(self, audio_url: str) -> bool:
        """Check if URL was already successfully transcribed"""
        return audio_url in self.progress.get('completed_urls', [])
    
    def mark_url_completed(self, audio_url: str):
        """Mark URL as successfully completed"""
        if 'completed_urls' not in self.progress:
            self.progress['completed_urls'] = []
        if audio_url not in self.progress['completed_urls']:
            self.progress['completed_urls'].append(audio_url)
        self.save_progress()
    
    def mark_url_failed(self, audio_url: str):
        """Mark URL as failed"""
        if 'failed_urls' not in self.progress:
            self.progress['failed_urls'] = []
        if audio_url not in self.progress['failed_urls']:
            self.progress['failed_urls'].append(audio_url)
        self.save_progress()

# --- Utility to convert Plivo record_url to S3 URL ---
def get_plivo_s3_url(record_url: str) -> str:
    match = re.search(r'/([a-f0-9\-]+)\.wav$', record_url)
    if not match:
        raise ValueError(f"Could not extract Recording ID from {record_url}")
    recording_id = match.group(1)
    return f"https://plivo-assets-prod.s3.eu-west-1.amazonaws.com/voice/recordings/{recording_id}.wav"

# --- FastAPI setup ---
app = FastAPI()

# Enable CORS for frontend development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        "http://localhost:3000",  # Alternative local port
        "https://summary-frontend.onrender.com",  # Render frontend
        "https://*.onrender.com",  # Any Render subdomain
        "*"  # Fallback for any origin
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class TranscribeRequest(BaseModel):
    record_url: str
    mobile_number: Optional[str] = None
    serial: Optional[int] = None
    call_id: Optional[int] = None  # <-- Add call_id for timeline update

# Utility to format utterances for diarization

def format_utterances(utterances):
    return '\n'.join([f'Speaker {u.speaker}: {u.text}' for u in utterances])

# Utility to append transcript to timeline JSON
import json

def append_transcript_to_timeline(mobile_number, call_id, transcript_text):
    # Use absolute path based on script location
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    timeline_path = os.path.join(base_dir, "data", f"timeline_{mobile_number}.json")
    print(f"[DEBUG] Trying to update timeline: {timeline_path} for call_id: {call_id}")
    try:
        if not os.path.exists(timeline_path):
            print(f"[DEBUG] Timeline file does not exist: {timeline_path}")
            return
        with open(timeline_path, "r", encoding="utf-8") as f:
            timeline = json.load(f)
        updated = False
        for event in timeline:
            print(f"[DEBUG] Checking event: id={event.get('id')} type={event.get('type')}")
            if event.get("type") == "call" and str(event.get("id")) == str(call_id):
                print(f"[DEBUG] Match found for call_id {call_id}, updating transcript.")
                event["transcript"] = transcript_text
                updated = True
                break
        if updated:
            with open(timeline_path, "w", encoding="utf-8") as f:
                json.dump(timeline, f, indent=2, ensure_ascii=False)
            print(f"[DEBUG] Timeline updated successfully for call_id {call_id}.")
        else:
            print(f"[DEBUG] No matching call event found in timeline for call_id {call_id}.")
    except Exception as e:
        print(f"[DEBUG] Failed to update timeline: {e}")

@app.post("/transcribe-call", response_class=PlainTextResponse)
def transcribe_call_api(req: TranscribeRequest):
    try:
        # Check if cleanup is needed before processing
        if storage_manager.should_cleanup():
            logging.info("Storage cleanup needed, running cleanup...")
            cleanup_stats = storage_manager.cleanup_old_files()
            logging.info(f"Storage cleanup completed: {cleanup_stats}")
        
        s3_url = get_plivo_s3_url(req.record_url)
        mobile_number = req.mobile_number or "apiuser"
        serial = req.serial or int(datetime.now().timestamp())
        call_id = req.call_id
        logging.info(f"[API] Transcribing Plivo call for {mobile_number} from {s3_url}")
        # Transcribe
        config = aai.TranscriptionConfig(**TRANSCRIPTION_CONFIG)
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(s3_url)
        while transcript.status in ['queued', 'processing']:
            time.sleep(2)
            transcript = transcriber.get_transcript(transcript.id)
        if transcript.status == 'error':
            raise RuntimeError(f"Transcription failed: {getattr(transcript, 'error', 'Unknown error')}")
        if not transcript.text or transcript.text.strip() == "":
            raise RuntimeError("Transcript is empty")
        # --- Diarization: use utterances if present ---
        diarized_text = None
        if hasattr(transcript, 'utterances') and transcript.utterances:
            diarized_text = format_utterances(transcript.utterances)
        transcript_text = diarized_text if diarized_text else transcript.text
        # Save as .txt for consistency
        out_path = os.path.join(TRANSCRIPTS_DIR, f"{mobile_number}_{serial}.txt")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        logging.info(f"[API] Saved transcript text to {out_path}")
        # --- Append transcript to timeline JSON ---
        if mobile_number and call_id is not None:
            append_transcript_to_timeline(mobile_number, call_id, transcript_text)
        return transcript_text
    except Exception as e:
        logging.error(f"[API] Failed to transcribe: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/storage/stats", response_class=JSONResponse)
def get_storage_stats():
    """Get current storage statistics"""
    try:
        stats = storage_manager.get_storage_stats()
        return stats
    except Exception as e:
        logging.error(f"Failed to get storage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/storage/cleanup", response_class=JSONResponse)
def cleanup_storage():
    """Manually trigger storage cleanup"""
    try:
        stats = storage_manager.cleanup_old_files()
        return {"message": "Storage cleanup completed", "stats": stats}
    except Exception as e:
        logging.error(f"Storage cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def load_calls_list(filename: str) -> List[Dict]:
    """Load calls list with validation"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            calls = json.load(f)
        
        if not isinstance(calls, list):
            raise ValueError("Input file must contain a JSON array")
        
        logging.info(f"Loaded {len(calls)} calls from {filename}")
        return calls
    
    except FileNotFoundError:
        logging.error(f"Input file {filename} not found")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in {filename}: {e}")
        return []
    except Exception as e:
        logging.error(f"Error loading calls list: {e}")
        return []

def validate_call_data(call: Dict) -> bool:
    """Validate required fields in call data"""
    if not isinstance(call, dict):
        logging.error("Call data must be a dictionary")
        return False
    
    required_fields = ['mobile_number', 'audio_url']
    for field in required_fields:
        if field not in call or not call[field]:
            logging.error(f"Missing or empty field: {field} in call data")
            return False
    
    # Validate mobile number format
    mobile_number = str(call['mobile_number']).strip()
    if not mobile_number:
        logging.error("Mobile number is empty")
        return False
    
    # Validate URL format
    audio_url = call['audio_url'].strip()
    try:
        parsed_url = urlparse(audio_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            logging.error(f"Invalid URL format: {audio_url}")
            return False
    except Exception as e:
        logging.error(f"URL validation failed: {e}")
        return False
    
    return True

def test_audio_url(audio_url: str) -> bool:
    """Test if audio URL is accessible"""
    try:
        response = requests.head(audio_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            if 'audio' in content_type or any(ext in audio_url.lower() for ext in ['.mp3', '.wav', '.m4a', '.flac', '.ogg']):
                return True
            else:
                logging.warning(f"URL may not be audio file: {audio_url} (content-type: {content_type})")
                return True  # Still try to transcribe
        else:
            logging.error(f"Audio URL not accessible: {audio_url} (status: {response.status_code})")
            return False
    except Exception as e:
        logging.error(f"Cannot access audio URL {audio_url}: {e}")
        return False

def get_next_serial(mobile_number: str) -> int:
    """Get next serial number for a mobile number"""
    try:
        files = [f for f in os.listdir(TRANSCRIPTS_DIR) if f.startswith(f"{mobile_number}_") and f.endswith('.json')]
        if not files:
            return 1
        
        serials = []
        for f in files:
            try:
                # Extract serial from filename like "mobile_123.json"
                parts = f.replace('.json', '').split('_')
                if len(parts) >= 2:
                    serial = int(parts[1])
                    serials.append(serial)
            except (ValueError, IndexError):
                continue
        
        return max(serials, default=0) + 1
    except Exception as e:
        logging.error(f"Error getting serial number: {e}")
        return 1

def is_already_transcribed(mobile_number: str, audio_url: str) -> bool:
    """Check if this exact URL was already transcribed for this mobile number"""
    try:
        files = [f for f in os.listdir(TRANSCRIPTS_DIR) if f.startswith(f"{mobile_number}_") and f.endswith('.json')]
        for file in files:
            file_path = os.path.join(TRANSCRIPTS_DIR, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('metadata', {}).get('audio_url') == audio_url:
                        logging.info(f"Already transcribed: {audio_url} for {mobile_number}")
                        return True
            except (json.JSONDecodeError, KeyError):
                continue
        return False
    except Exception as e:
        logging.error(f"Error checking if already transcribed: {e}")
        return False

def transcribe_and_save(call: Dict, serial: int, manager: TranscriptionManager) -> bool:
    """Transcribe audio and save with retry logic"""
    mobile_number = str(call['mobile_number']).strip()
    audio_url = call['audio_url'].strip()
    
    # Check if already completed
    if manager.is_url_completed(audio_url):
        logging.info(f"Skipping already completed: {audio_url}")
        return True
    
    # Check if already transcribed locally
    if is_already_transcribed(mobile_number, audio_url):
        manager.mark_url_completed(audio_url)
        return True
    
    # Test audio URL accessibility
    if not test_audio_url(audio_url):
        manager.mark_url_failed(audio_url)
        return False
    
    for attempt in range(MAX_RETRIES):
        try:
            logging.info(f"Transcribing for {mobile_number} (serial {serial}, attempt {attempt + 1}): {audio_url}")
            
            # Create transcription config
            config = aai.TranscriptionConfig(**TRANSCRIPTION_CONFIG)
            transcriber = aai.Transcriber(config=config)
            
            # Start transcription
            transcript = transcriber.transcribe(audio_url)
            
            # Wait for completion with status checks
            while transcript.status in ['queued', 'processing']:
                logging.info(f"Transcription status: {transcript.status}")
                time.sleep(5)
                # Refresh transcript status
                transcript = transcriber.get_transcript(transcript.id)
            
            # Check final status
            if transcript.status == 'error':
                error_msg = getattr(transcript, 'error', 'Unknown error')
                raise RuntimeError(f"Transcription failed: {error_msg}")
            
            if transcript.status != 'completed':
                raise RuntimeError(f"Unexpected transcription status: {transcript.status}")
            
            # Verify transcript has content
            if not transcript.text or transcript.text.strip() == "":
                raise RuntimeError("Transcript is empty")
            
            # Save only the transcript text as .txt
            out_path = os.path.join(TRANSCRIPTS_DIR, f"{mobile_number}_{serial}.txt")
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(transcript.text)
            
            logging.info(f"Successfully saved transcript text to {out_path} (length: {len(transcript.text)} chars)")
            manager.mark_url_completed(audio_url)
            return True
            
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed for {audio_url}: {e}")
            if attempt < MAX_RETRIES - 1:
                sleep_time = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                logging.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logging.error(f"All {MAX_RETRIES} attempts failed for {audio_url}")
                manager.mark_url_failed(audio_url)
                return False
    
    return False

def main():
    """Main transcription function"""
    manager = TranscriptionManager()
    
    try:
        # Load and validate calls
        calls = load_calls_list(CALLS_INPUT_FILE)
        if not calls:
            logging.error("No calls to process")
            return
        
        # Filter valid calls
        valid_calls = [call for call in calls if validate_call_data(call)]
        logging.info(f"Processing {len(valid_calls)} valid calls out of {len(calls)} total")
        
        if not valid_calls:
            logging.error("No valid calls to process")
            return
        
        # Process each call
        for i, call in enumerate(valid_calls, 1):
            mobile_number = str(call['mobile_number']).strip()
            audio_url = call['audio_url'].strip()
            
            logging.info(f"Processing call {i}/{len(valid_calls)} for {mobile_number}")
            
            # Get serial number
            serial = get_next_serial(mobile_number)
            
            # Transcribe and save
            success = transcribe_and_save(call, serial, manager)
            
            if success:
                manager.successful_count += 1
                logging.info(f"✓ Successfully processed {mobile_number} ({i}/{len(valid_calls)})")
            else:
                manager.failed_count += 1
                manager.failed_urls.append(audio_url)
                logging.error(f"✗ Failed to process {mobile_number} ({i}/{len(valid_calls)})")
            
            # Rate limiting
            if i < len(valid_calls):  # Don't delay after last item
                time.sleep(RATE_LIMIT_DELAY)
        
        # Final summary
        logging.info("=" * 60)
        logging.info("TRANSCRIPTION BATCH COMPLETE")
        logging.info(f"Total processed: {len(valid_calls)}")
        logging.info(f"Successful: {manager.successful_count}")
        logging.info(f"Failed: {manager.failed_count}")
        
        if manager.failed_urls:
            logging.info("Failed URLs:")
            for url in manager.failed_urls:
                logging.info(f"  - {url}")
        
        # Save final progress
        manager.save_progress()
        
    except KeyboardInterrupt:
        logging.info("Transcription interrupted by user")
        manager.save_progress()
    except Exception as e:
        logging.critical(f"Batch transcription failed: {e}")
        manager.save_progress()

if __name__ == "__main__":
    # Validate API key
    if not aai.settings.api_key or aai.settings.api_key == 'YOUR_API_KEY_HERE':
        logging.error("Please set your AssemblyAI API key in environment variables or .env file")
        exit(1)
    
    main() 