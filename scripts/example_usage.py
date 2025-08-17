#!/usr/bin/env python3
"""
Example usage of the YouTube to Audio Recording functionality

This script demonstrates different ways to use the YouTube audio extraction features.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the script directory to path
sys.path.insert(0, str(Path(__file__).parent))

from youtube_to_recording import YouTubeAudioProcessor
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def example_basic_usage():
    """Example of basic YouTube audio extraction."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Usage")
    print("="*60)
    
    # Load environment variables
    load_dotenv()
    
    # Configuration
    recordings_dir = os.getenv('RECORDINGS_DIR', 'C:\\Users\\magne\\Documents\\Branches-ConversationTree\\audio_recordings')
    api_url = os.getenv('DATA_API_URL', 'http://localhost:8000')
    
    # Use a very short, safe video for demonstration
    youtube_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - 19 seconds
    
    print(f"Recordings directory: {recordings_dir}")
    print(f"API URL: {api_url}")
    print(f"YouTube URL: {youtube_url}")
    
    try:
        # Create processor
        processor = YouTubeAudioProcessor(recordings_dir, api_url)
        
        # NOTE: This would actually download the video and create a recording
        # For this example, we'll just show the video info extraction
        print("\nExtracting video information...")
        video_info = processor.get_video_info(youtube_url)
        
        print(f"✓ Video Title: {video_info.get('title')}")
        print(f"✓ Duration: {video_info.get('duration')} seconds")
        print(f"✓ Uploader: {video_info.get('uploader')}")
        
        print("\n⚠ To actually download and process the audio, uncomment the following lines:")
        print("# result = processor.process_youtube_video(youtube_url)")
        print("# print(f'Audio saved to: {result[\"audio_file_path\"]}')")
        print("# print(f'Recording ID: {result[\"recording\"][\"id\"]}')")
        
    except Exception as e:
        print(f"✗ Error: {e}")

def example_with_parent_recording():
    """Example of linking to a parent recording."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Linking to Parent Recording")
    print("="*60)
    
    youtube_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    parent_recording_id = 123  # Example parent ID
    parent_time = 45.5  # 45.5 seconds into the parent recording
    
    print(f"YouTube URL: {youtube_url}")
    print(f"Parent Recording ID: {parent_recording_id}")
    print(f"Parent Time: {parent_time} seconds")
    
    print("\n⚠ Example code (requires API to be running):")
    print("processor = YouTubeAudioProcessor('./audio_recordings', 'http://localhost:8000')")
    print("result = processor.process_youtube_video(")
    print(f"    youtube_url='{youtube_url}',")
    print(f"    parent_id={parent_recording_id},")
    print(f"    parent_time={parent_time}")
    print(")")

def example_batch_processing():
    """Example of processing multiple videos."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Batch Processing Multiple Videos")
    print("="*60)
    
    video_urls = [
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Very short video
        "https://www.youtube.com/watch?v=BaW_jenozKc",  # Another short video
        # Add more URLs as needed
    ]
    
    print("Video URLs to process:")
    for i, url in enumerate(video_urls, 1):
        print(f"  {i}. {url}")
    
    print("\n⚠ Example batch processing code:")
    print("processor = YouTubeAudioProcessor('./audio_recordings', 'http://localhost:8000')")
    print("results = []")
    print("for url in video_urls:")
    print("    try:")
    print("        result = processor.process_youtube_video(url)")
    print("        results.append(result)")
    print("        print(f'✓ Processed: {result[\"video_info\"][\"title\"]}')")
    print("    except Exception as e:")
    print("        print(f'✗ Failed to process {url}: {e}')")

def example_custom_configuration():
    """Example of using custom configuration."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Custom Configuration")
    print("="*60)
    
    # Custom configuration
    custom_recordings_dir = "./my_custom_recordings"
    custom_api_url = "http://localhost:9000"  # Different port
    
    print("Custom configuration:")
    print(f"  Recordings directory: {custom_recordings_dir}")
    print(f"  API URL: {custom_api_url}")
    
    print("\n⚠ Example code:")
    print("from youtube_to_recording import YouTubeAudioProcessor")
    print("")
    print("# Initialize with custom configuration")
    print(f"processor = YouTubeAudioProcessor('{custom_recordings_dir}', '{custom_api_url}')")
    print("")
    print("# Process video")
    print("result = processor.process_youtube_video('https://www.youtube.com/watch?v=VIDEO_ID')")

def main():
    """Run all examples."""
    print("YouTube to Audio Recording - Usage Examples")
    print("="*60)
    print("This script demonstrates different ways to use the YouTube audio extraction functionality.")
    print("\n⚠ NOTE: These examples show the code structure without actually downloading videos.")
    print("To run real downloads, ensure the data API service is running and uncomment the processing calls.")
    
    # Run examples
    example_basic_usage()
    example_with_parent_recording()
    example_batch_processing()
    example_custom_configuration()
    
    print("\n" + "="*60)
    print("REAL USAGE EXAMPLES:")
    print("="*60)
    print("To actually use the script from command line:")
    print("")
    print("# Basic usage:")
    print('python youtube_to_recording.py "https://www.youtube.com/watch?v=VIDEO_ID"')
    print("")
    print("# With parent recording:")
    print('python youtube_to_recording.py "https://youtu.be/VIDEO_ID" --parent-id 123 --parent-time 45.5')
    print("")
    print("# With custom output directory:")
    print('python youtube_to_recording.py "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir "./my_recordings"')
    print("")
    print("# With verbose logging:")
    print('python youtube_to_recording.py "https://www.youtube.com/watch?v=VIDEO_ID" --verbose')
    print("\n" + "="*60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
