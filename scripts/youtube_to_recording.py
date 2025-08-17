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
    
    def sanitize_filename(self, title: str) -> str:
        """Create a safe filename from video title."""
        # Remove or replace problematic characters, remove spaces
        safe_title = re.sub(r'[^\w\-_.]', '', title.replace(' ', '_'))
        # Limit length and ensure it's not empty
        safe_title = safe_title[:30] if safe_title else 'unknown'
        return safe_title.lower()
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds using ffmpeg."""
        try:
            result = subprocess.run([
                'ffmpeg', '-i', audio_path, '-f', 'null', '-'
            ], capture_output=True, text=True)
            
            # ffmpeg outputs to stderr, so check both stdout and stderr
            output = result.stderr + result.stdout
            
            # Parse duration from ffmpeg output
            duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', output)
            if duration_match:
                hours, minutes, seconds, centiseconds = map(int, duration_match.groups())
                return hours * 3600 + minutes * 60 + seconds + centiseconds / 100
            return 0.0
        except Exception as e:
            logger.warning(f"Could not get audio duration: {e}")
            return 0.0
    
    def split_audio(self, audio_path: str, chunk_duration: int = 60) -> list[str]:
        """Split audio file into chunks of specified duration (seconds)."""
        audio_path = Path(audio_path)
        total_duration = self.get_audio_duration(str(audio_path))
        
        if total_duration <= chunk_duration:
            logger.info(f"Audio duration ({total_duration:.1f}s) is shorter than chunk size ({chunk_duration}s), not splitting")
            return [str(audio_path)]
        
        chunks = []
        chunk_count = math.ceil(total_duration / chunk_duration)
        
        logger.info(f"Splitting audio into {chunk_count} chunks of ~{chunk_duration}s each")
        
        # Create base filename for chunks
        base_name = audio_path.stem
        
        for i in range(chunk_count):
            start_time = i * chunk_duration
            chunk_filename = f"{base_name}_part{i+1:02d}.wav"
            chunk_path = audio_path.parent / chunk_filename
            
            try:
                # Use ffmpeg to extract chunk
                result = subprocess.run([
                    'ffmpeg', '-i', str(audio_path),
                    '-ss', str(start_time),
                    '-t', str(chunk_duration),
                    '-c', 'copy',
                    str(chunk_path),
                    '-y'  # Overwrite output files
                ], capture_output=True, text=True, check=True)
                
                chunks.append(str(chunk_path))
                logger.info(f"Created chunk {i+1}/{chunk_count}: {chunk_path.name}")
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create chunk {i+1}: {e}")
                continue
        
        # Remove original file after successful splitting
        if chunks and len(chunks) > 1:
            try:
                audio_path.unlink()
                logger.info(f"Removed original file: {audio_path.name}")
            except Exception as e:
                logger.warning(f"Could not remove original file: {e}")
        
        return chunks
    
    def download_audio(self, youtube_url: str) -> tuple[str, dict]:
        """
        Download and extract audio from YouTube video.
        
        Returns:
            tuple: (path_to_audio_file, video_info_dict)
        """
        logger.info(f"Getting video information for: {youtube_url}")
        video_info = self.get_video_info(youtube_url)
        
        # Create filename with yt_ prefix and no spaces
        title = video_info.get('title', 'Unknown')
        safe_title = self.sanitize_filename(title)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        audio_filename = f"yt_{safe_title}_{timestamp}.wav"
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
        # Convert to just the filename for storage (no folder prefix)
        audio_file_path = Path(audio_file_path)
        filename_only = audio_file_path.name
        
        payload = {
            "audio_file_path": filename_only,
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
    
    def process_youtube_video_with_splitting(self, youtube_url: str, parent_id: int = None, parent_time: float = None, 
                                           chunk_duration: int = 60, split_audio: bool = True) -> dict:
        """
        Complete process: download audio, split into chunks, and create recording entries.
        
        Returns:
            dict: Combined result with audio chunks, video info, and all recording data
        """
        if not self.check_dependencies():
            raise RuntimeError("Required dependencies are not available")
        
        # Download and extract audio
        audio_path, video_info = self.download_audio(youtube_url)
        
        # Split audio into chunks if requested
        if split_audio:
            audio_chunks = self.split_audio(audio_path, chunk_duration)
        else:
            audio_chunks = [audio_path]
        
        recordings = []
        main_recording_id = None
        
        logger.info(f"Creating {len(audio_chunks)} recording entries")
        
        for i, chunk_path in enumerate(audio_chunks):
            # Calculate parent time for this chunk
            chunk_parent_time = (parent_time or 0.0) + (i * chunk_duration)
            
            # For the first chunk, use provided parent_id
            # For subsequent chunks, use the main recording as parent with random time offsets
            if i == 0:
                # First chunk - main recording
                recording_data = self.create_recording_entry(chunk_path, parent_id, parent_time)
                main_recording_id = recording_data.get('id')
                recordings.append({
                    'chunk_index': i + 1,
                    'audio_file_path': chunk_path,
                    'recording': recording_data,
                    'is_main': True
                })
            else:
                # Subsequent chunks - create as children of main recording with random time offsets
                random_time = round(random.uniform(0.1, chunk_duration * 0.8), 2)
                recording_data = self.create_recording_entry(chunk_path, main_recording_id, random_time)
                recordings.append({
                    'chunk_index': i + 1,
                    'audio_file_path': chunk_path,
                    'recording': recording_data,
                    'is_main': False,
                    'parent_recording_id': main_recording_id,
                    'random_parent_time': random_time
                })
            
            logger.info(f"Created recording {i+1}/{len(audio_chunks)}: ID {recording_data.get('id')}")
        
        return {
            'video_info': {
                'title': video_info.get('title'),
                'duration': video_info.get('duration'),
                'uploader': video_info.get('uploader'),
                'upload_date': video_info.get('upload_date'),
                'url': youtube_url
            },
            'recordings': recordings,
            'main_recording_id': main_recording_id,
            'total_chunks': len(audio_chunks)
        }
    
    def process_youtube_video(self, youtube_url: str, parent_id: int = None, parent_time: float = None) -> dict:
        """
        Complete process: download audio and create recording entry (backward compatibility).
        
        Returns:
            dict: Combined result with audio path, video info, and recording data
        """
        # Use the new splitting function but don't split by default for backward compatibility
        result = self.process_youtube_video_with_splitting(
            youtube_url, parent_id, parent_time, split_audio=False
        )
        
        # Convert to old format for backward compatibility
        main_recording = next((r for r in result['recordings'] if r.get('is_main', True)), result['recordings'][0])
        
        return {
            'audio_file_path': main_recording['audio_file_path'],
            'video_info': result['video_info'],
            'recording': main_recording['recording']
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
        '--split', '-s',
        action='store_true',
        help='Split audio into chunks and create parent-child relationships'
    )
    parser.add_argument(
        '--chunk-duration',
        type=int,
        default=60,
        help='Duration of each audio chunk in seconds (default: 60)'
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
        
        # Process the video with or without splitting
        logger.info(f"Processing YouTube video: {args.youtube_url}")
        
        if args.split:
            # Use splitting functionality
            result = processor.process_youtube_video_with_splitting(
                args.youtube_url,
                args.parent_id,
                args.parent_time,
                args.chunk_duration,
                split_audio=True
            )
            
            # Output results for split processing
            print("\n" + "="*80)
            print("SPLIT PROCESSING COMPLETED SUCCESSFULLY")
            print("="*80)
            print(f"Video title: {result['video_info']['title']}")
            print(f"Video duration: {result['video_info']['duration']} seconds")
            print(f"Total chunks created: {result['total_chunks']}")
            print(f"Chunk duration: {args.chunk_duration} seconds")
            print(f"Main recording ID: {result['main_recording_id']}")
            
            if args.parent_id:
                print(f"Original parent recording ID: {args.parent_id}")
            if args.parent_time:
                print(f"Original parent time offset: {args.parent_time} seconds")
            
            print("\nRecording chunks created:")
            print("-" * 50)
            
            for recording in result['recordings']:
                chunk_info = f"Chunk {recording['chunk_index']}: ID {recording['recording']['id']}"
                if recording.get('is_main'):
                    chunk_info += " (MAIN)"
                else:
                    chunk_info += f" (child of {recording['parent_recording_id']}, random time: {recording['random_parent_time']}s)"
                
                print(chunk_info)
                print(f"  File: {Path(recording['audio_file_path']).name}")
                print(f"  Created: {recording['recording']['created_date']}")
                print()
            
        else:
            # Use standard processing (no splitting)
            result = processor.process_youtube_video(
                args.youtube_url,
                args.parent_id,
                args.parent_time
            )
            
            # Output results for standard processing
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
        
        print("\nThe audio files have been saved and recording entries created.")
        print("Audio processing will begin automatically via the processing pipeline.")
        print("="*80 if args.split else "="*60)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
