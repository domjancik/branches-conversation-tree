#!/usr/bin/env python3
"""
YouTube to Audio Recording Script

This script downloads audio from YouTube videos and creates new recording entries 
in the branches-conversation-tree system. The extracted audio is stored in the 
recordings folder and processed through the existing audio processing pipeline.

Usage:
    python youtube_to_recording.py <youtube_url> [--parent-id <id>] [--parent-time <time>] [--output-dir <path>]

Requirements:
    - yt-dlp
    - requests
    - python-dotenv
    - ffmpeg (system dependency)
"""

import os
import sys
import argparse
import logging
import requests
import tempfile
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import subprocess
import json
import random
import re
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class YouTubeAudioProcessor:
    """Handles YouTube video download and audio extraction."""
    
    def __init__(self, recordings_dir: str, data_api_url: str):
        self.recordings_dir = Path(recordings_dir)
        self.data_api_url = data_api_url
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        
    def check_dependencies(self):
        """Check if required system dependencies are available."""
        try:
            subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
            logger.info("yt-dlp is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("yt-dlp is not installed. Install with: pip install yt-dlp")
            return False
            
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            logger.info("ffmpeg is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("ffmpeg is not installed. Please install ffmpeg")
            return False
            
        return True
    
    def get_video_info(self, youtube_url: str) -> dict:
        """Get video information without downloading."""
        try:
            result = subprocess.run([
                'yt-dlp',
                '--dump-json',
                '--no-download',
                youtube_url
            ], capture_output=True, text=True, check=True)
            
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get video info: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse video info JSON: {e}")
            raise
    
    def download_audio(self, youtube_url: str) -> tuple[str, dict]:
        """
        Download and extract audio from YouTube video.
        
        Returns:
            tuple: (path_to_audio_file, video_info_dict)
        """
        logger.info(f"Getting video information for: {youtube_url}")
        video_info = self.get_video_info(youtube_url)
        
        # Create filename based on video title and timestamp
        title = video_info.get('title', 'Unknown')
        # Sanitize filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        audio_filename = f"youtube_{safe_title}_{timestamp}.wav"
        audio_path = self.recordings_dir / audio_filename
        
        logger.info(f"Downloading and extracting audio: {title}")
        logger.info(f"Output file: {audio_path}")
        
        try:
            # Use yt-dlp to download and extract audio
            result = subprocess.run([
                'yt-dlp',
                '--extract-audio',
                '--audio-format', 'wav',
                '--audio-quality', '0',  # Best quality
                '--output', str(audio_path.with_suffix('')),  # yt-dlp will add .wav
                youtube_url
            ], capture_output=True, text=True, check=True)
            
            logger.info("Audio extraction completed successfully")
            return str(audio_path), video_info
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio extraction failed: {e}")
            logger.error(f"stderr: {e.stderr}")
            raise
    
    def create_recording_entry(self, audio_file_path: str, parent_id: int = None, parent_time: float = None) -> dict:
        """
        Create a new recording entry via the data API.
        
        Args:
            audio_file_path: Path to the audio file
            parent_id: Optional parent recording ID
            parent_time: Optional parent time offset
            
        Returns:
            dict: Response from the API
        """
        # Convert to relative path for storage
        audio_file_path = Path(audio_file_path)
        if audio_file_path.is_absolute():
            try:
                audio_file_path = audio_file_path.relative_to(self.recordings_dir.parent)
            except ValueError:
                # If path is not relative to recordings parent, use just filename
                audio_file_path = audio_file_path.name
        
        payload = {
            "audio_file_path": str(audio_file_path),
            "parent_audio_recording_id": parent_id,
            "parent_time": parent_time
        }
        
        try:
            logger.info(f"Creating recording entry via API: {self.data_api_url}/recordings/")
            response = requests.post(
                f"{self.data_api_url}/recordings/",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Recording created with ID: {result.get('id')}")
            return result
            
        except requests.RequestException as e:
            logger.error(f"Failed to create recording entry: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def process_youtube_video(self, youtube_url: str, parent_id: int = None, parent_time: float = None) -> dict:
        """
        Complete process: download audio and create recording entry.
        
        Returns:
            dict: Combined result with audio path, video info, and recording data
        """
        if not self.check_dependencies():
            raise RuntimeError("Required dependencies are not available")
        
        # Download and extract audio
        audio_path, video_info = self.download_audio(youtube_url)
        
        # Create recording entry
        recording_data = self.create_recording_entry(audio_path, parent_id, parent_time)
        
        return {
            'audio_file_path': audio_path,
            'video_info': {
                'title': video_info.get('title'),
                'duration': video_info.get('duration'),
                'uploader': video_info.get('uploader'),
                'upload_date': video_info.get('upload_date'),
                'url': youtube_url
            },
            'recording': recording_data
        }


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description='Extract audio from YouTube videos and create recording entries',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python youtube_to_recording.py "https://www.youtube.com/watch?v=VIDEO_ID"
  python youtube_to_recording.py "https://youtu.be/VIDEO_ID" --parent-id 123 --parent-time 45.5
  python youtube_to_recording.py "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir "./my_recordings"
        """
    )
    
    parser.add_argument(
        'youtube_url',
        help='YouTube video URL'
    )
    parser.add_argument(
        '--parent-id',
        type=int,
        help='Parent recording ID (optional)'
    )
    parser.add_argument(
        '--parent-time',
        type=float,
        help='Parent time offset in seconds (optional)'
    )
    parser.add_argument(
        '--output-dir',
        default=os.getenv('RECORDINGS_DIR', 'C:\\Users\\magne\\Documents\\Branches-ConversationTree\\audio_recordings'),
        help='Directory to store audio files (default: from RECORDINGS_DIR env var or C:\\Users\\magne\\Documents\\Branches-ConversationTree\\audio_recordings)'
    )
    parser.add_argument(
        '--data-api-url',
        default=os.getenv('DATA_API_URL', 'http://localhost:8000'),
        help='Data API URL (default: from DATA_API_URL env var or http://localhost:8000)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize processor
        processor = YouTubeAudioProcessor(args.output_dir, args.data_api_url)
        
        # Process the video
        logger.info(f"Processing YouTube video: {args.youtube_url}")
        result = processor.process_youtube_video(
            args.youtube_url,
            args.parent_id,
            args.parent_time
        )
        
        # Output results
        print("\n" + "="*60)
        print("PROCESSING COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Audio file: {result['audio_file_path']}")
        print(f"Video title: {result['video_info']['title']}")
        print(f"Video duration: {result['video_info']['duration']} seconds")
        print(f"Recording ID: {result['recording']['id']}")
        print(f"Created: {result['recording']['created_date']}")
        
        if args.parent_id:
            print(f"Parent recording ID: {args.parent_id}")
        if args.parent_time:
            print(f"Parent time offset: {args.parent_time} seconds")
        
        print("\nThe audio file has been saved and a recording entry created.")
        print("Audio processing will begin automatically via the processing pipeline.")
        print("="*60)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
