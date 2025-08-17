# YouTube to Audio Recording Script

This script allows you to extract audio from YouTube videos and automatically create recording entries in the branches-conversation-tree system. The extracted audio files are stored in the recordings folder and processed through the existing audio processing pipeline.

## Features

- **YouTube Video Download**: Download videos from YouTube URLs
- **Audio Extraction**: Extract high-quality audio in WAV format
- **Automatic Integration**: Create recording entries via the data API
- **Parent Recording Support**: Link new recordings to existing parent recordings
- **Error Handling**: Comprehensive error handling and logging
- **Dependency Validation**: Automatic validation of required dependencies

## Prerequisites

### System Dependencies

- **Python 3.8+**: Required for running the script
- **ffmpeg**: Required for audio processing and format conversion
- **Internet Connection**: Required for downloading YouTube videos

### Python Dependencies

- `yt-dlp`: YouTube video downloader
- `requests`: HTTP requests for API communication
- `python-dotenv`: Environment variable management

## Installation

### Quick Setup (Recommended)

1. **Run the setup script**:
   ```powershell
   .\setup.ps1 -InstallSystemDeps -CreateVenv
   ```

2. **Or manually install**:
   ```powershell
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Install ffmpeg (choose one method)
   winget install Gyan.FFmpeg        # Using winget
   choco install ffmpeg              # Using chocolatey
   ```

### Manual Installation

1. **Install Python dependencies**:
   ```bash
   pip install yt-dlp requests python-dotenv
   ```

2. **Install ffmpeg**:
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use `winget install Gyan.FFmpeg`
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt install ffmpeg`

## Configuration

### Environment Variables

Create a `.env` file in the scripts directory:

```env
# Directory where audio recordings will be stored
RECORDINGS_DIR=../audio_recordings

# Data API URL (adjust port if different)
DATA_API_URL=http://localhost:8000

# Audio Processing API URL (adjust port if different)  
AUDIO_PROCESSOR_URL=http://localhost:8001

# Database path (for reference)
DB_PATH=../data_store/conversation_tree.db
```

### Service Dependencies

Ensure these services are running before using the script:

1. **Data API Service**: Usually runs on `http://localhost:8000`
   ```bash
   cd data_store
   python -m uvicorn data_api:app --host 0.0.0.0 --port 8000
   ```

2. **Audio Processing Service**: Usually runs on `http://localhost:8001`
   ```bash
   cd audio-llm-processing
   python -m uvicorn process_audio_file:app --host 0.0.0.0 --port 8001
   ```

## Usage

### Basic Usage

Extract audio from a YouTube video:
```bash
python youtube_to_recording.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Advanced Usage

```bash
# Link to a parent recording
python youtube_to_recording.py "https://youtu.be/VIDEO_ID" --parent-id 123 --parent-time 45.5

# Specify custom output directory
python youtube_to_recording.py "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir "./my_recordings"

# Use custom API endpoint
python youtube_to_recording.py "https://www.youtube.com/watch?v=VIDEO_ID" --data-api-url "http://localhost:9000"

# Enable verbose logging
python youtube_to_recording.py "https://www.youtube.com/watch?v=VIDEO_ID" --verbose
```

### Command Line Options

- `youtube_url` (required): YouTube video URL
- `--parent-id`: Parent recording ID to link this recording to
- `--parent-time`: Time offset in the parent recording (in seconds)
- `--output-dir`: Directory to store audio files (default: from env var or `./audio_recordings`)
- `--data-api-url`: Data API URL (default: from env var or `http://localhost:8000`)
- `--verbose`, `-v`: Enable verbose logging

## How It Works

1. **Video Information Extraction**: Uses yt-dlp to get video metadata
2. **Audio Download**: Downloads and extracts audio in high-quality WAV format  
3. **File Management**: Saves audio file with sanitized filename including timestamp
4. **API Integration**: Creates recording entry via the data API
5. **Processing Pipeline**: Audio processing begins automatically via the existing pipeline

## File Naming Convention

Audio files are saved with the following naming pattern:
```
youtube_{safe_title}_{timestamp}.wav
```

Where:
- `{safe_title}`: Sanitized video title (alphanumeric, spaces, hyphens, underscores only)
- `{timestamp}`: Current timestamp in `YYYYMMDD_HHMMSS` format

## Example Output

```
============================================================
PROCESSING COMPLETED SUCCESSFULLY
============================================================
Audio file: C:\path\to\audio_recordings\youtube_Example Video_20240101_120000.wav
Video title: Example Video Title
Video duration: 300 seconds
Recording ID: 42
Created: 2024-01-01T12:00:00

The audio file has been saved and a recording entry created.
Audio processing will begin automatically via the processing pipeline.
============================================================
```

## Integration with Existing System

The script integrates seamlessly with the existing branches-conversation-tree system:

- **Database Integration**: Creates entries in the `audio_recordings` table
- **Processing Pipeline**: Triggers automatic transcription and analysis
- **Tree Structure**: Supports parent-child relationships between recordings
- **API Compatibility**: Uses the same data models and API endpoints

## Error Handling

The script includes comprehensive error handling for common scenarios:

- **Invalid YouTube URLs**: Validates and provides helpful error messages
- **Network Issues**: Handles download failures and timeouts
- **API Errors**: Provides detailed error information for API failures
- **Dependency Issues**: Checks for required system dependencies
- **File System Errors**: Handles directory creation and file writing issues

## Troubleshooting

### Common Issues

1. **"yt-dlp not found"**
   - Solution: Install yt-dlp with `pip install yt-dlp`

2. **"ffmpeg not found"**
   - Solution: Install ffmpeg using your system's package manager

3. **"Connection refused"**
   - Solution: Ensure the data API service is running on the specified port

4. **"Permission denied"**
   - Solution: Check directory permissions for the recordings folder

### Debug Mode

Enable verbose logging to see detailed information:
```bash
python youtube_to_recording.py "VIDEO_URL" --verbose
```

### Log Output

The script logs important information including:
- Video metadata extraction
- Download progress  
- File creation
- API requests and responses
- Error details

## Security Considerations

- **URL Validation**: The script validates YouTube URLs but exercise caution with untrusted URLs
- **File System**: Audio files are saved to a specified directory with sanitized filenames
- **API Communication**: Uses standard HTTP requests to communicate with local APIs
- **No Credential Storage**: The script doesn't store or handle user credentials

## Performance Notes

- **Download Speed**: Depends on internet connection and video size
- **Audio Quality**: Uses highest available quality (typically 320kbps or higher)
- **Processing Time**: Audio processing happens asynchronously via the processing pipeline
- **Storage Requirements**: WAV files require approximately 10MB per minute of audio

## Contributing

To contribute to this script:

1. Follow the existing code style and patterns
2. Add appropriate logging and error handling
3. Update documentation for any new features
4. Test with various YouTube video types and lengths

## Related Files

- `youtube_to_recording.py`: Main script
- `requirements.txt`: Python dependencies
- `setup.ps1`: Setup and installation script
- `.env`: Configuration file (create from template)
- `../data_store/data_api.py`: Data API service
- `../audio-llm-processing/`: Audio processing pipeline

## License

This script is part of the branches-conversation-tree project and follows the same license terms.
