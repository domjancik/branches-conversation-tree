#!/usr/bin/env python3
"""
Test script to validate YouTube audio extraction dependencies and functionality
"""

import sys
import os
from pathlib import Path

# Add the script directory to the Python path so we can import our module
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from youtube_to_recording import YouTubeAudioProcessor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dependencies():
    """Test that all required dependencies are available."""
    print("Testing YouTube Audio Recording Dependencies")
    print("=" * 50)
    
    # Create a temporary processor instance
    temp_recordings_dir = "./temp_test_recordings"
    temp_api_url = "http://localhost:8000"  # This won't be tested, just used for init
    
    try:
        processor = YouTubeAudioProcessor(temp_recordings_dir, temp_api_url)
        
        print("✓ YouTubeAudioProcessor class initialized successfully")
        
        # Test dependency checking
        if processor.check_dependencies():
            print("✓ All system dependencies are available")
            print("  - yt-dlp: Available")
            print("  - ffmpeg: Available")
            return True
        else:
            print("✗ Some system dependencies are missing")
            return False
            
    except Exception as e:
        print(f"✗ Error during dependency check: {e}")
        return False
    finally:
        # Clean up temp directory if it was created
        temp_path = Path(temp_recordings_dir)
        if temp_path.exists() and temp_path.is_dir():
            try:
                temp_path.rmdir()
                print("✓ Cleaned up temporary test directory")
            except OSError:
                print("⚠ Could not clean up temporary test directory (may not be empty)")

def test_video_info_extraction():
    """Test video information extraction without downloading."""
    print("\nTesting Video Information Extraction")
    print("=" * 40)
    
    # Use a reliable, short video for testing
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - first YouTube video
    
    temp_recordings_dir = "./temp_test_recordings"
    temp_api_url = "http://localhost:8000"
    
    try:
        processor = YouTubeAudioProcessor(temp_recordings_dir, temp_api_url)
        
        print(f"Testing with URL: {test_url}")
        video_info = processor.get_video_info(test_url)
        
        print("✓ Video information extracted successfully")
        print(f"  - Title: {video_info.get('title', 'Unknown')}")
        print(f"  - Duration: {video_info.get('duration', 'Unknown')} seconds")
        print(f"  - Uploader: {video_info.get('uploader', 'Unknown')}")
        print(f"  - Upload Date: {video_info.get('upload_date', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during video info extraction: {e}")
        return False
    finally:
        # Clean up temp directory if it was created
        temp_path = Path(temp_recordings_dir)
        if temp_path.exists() and temp_path.is_dir():
            try:
                temp_path.rmdir()
            except OSError:
                pass

def main():
    """Run all tests."""
    print("YouTube to Audio Recording Script - Dependency Test")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test 1: Dependencies
    if not test_dependencies():
        all_tests_passed = False
    
    # Test 2: Video info extraction (requires internet)
    try:
        if not test_video_info_extraction():
            all_tests_passed = False
    except Exception as e:
        print(f"⚠ Skipped video info test due to error: {e}")
        print("  This might be due to network connectivity issues")
    
    # Summary
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED")
        print("\nThe YouTube audio extraction script should work correctly.")
        print("You can now use it with:")
        print('  python youtube_to_recording.py "https://www.youtube.com/watch?v=VIDEO_ID"')
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease resolve the issues above before using the script.")
    
    print("=" * 60)
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())
