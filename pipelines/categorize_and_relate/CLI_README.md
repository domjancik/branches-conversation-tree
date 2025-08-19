# Audio Pipeline CLI

A minimal command-line interface for operating the Audio → Whisper → Categorize & Relate pipeline.

## Installation

The CLI uses the same UV environment as the project:

```bash
# Already installed if you set up the project
uv add requests
```

## Usage

### Basic Commands

```bash
# Run via Python
uv run python cli.py <command>

# Or use the PowerShell wrapper
.\pipeline.ps1 <command>
```

### Available Commands

#### `serve` - Start and run servers (recommended)
```bash
uv run python cli.py serve
# Starts both servers and keeps them running
# Press Ctrl+C to stop gracefully
```

#### `start` - Start servers
```bash
uv run python cli.py start
# Starts backend (port 8000) and web UI (port 5173)
# Returns immediately after starting
```

#### `stop` - Stop servers
```bash
uv run python cli.py stop
# Stops both backend and web UI servers
```

#### `status` - Check server status
```bash
uv run python cli.py status
# Shows:
# - Backend status (http://localhost:8000)
# - Web UI status (http://localhost:5173)  
# - Number of saved recordings
```

#### `process` - Process an audio file
```bash
uv run python cli.py process path/to/audio.wav
# Processes audio file through the pipeline:
# 1. Transcribes with Whisper
# 2. Runs categorize_and_relate
# 3. Saves to recordings/ folder
# 4. Shows results
```

#### `recordings` - List saved recordings
```bash
uv run python cli.py recordings
# Shows all saved recordings with:
# - Timestamps
# - Audio filenames
# - Transcript previews
# - File existence status
```

## Examples

### Quick Start
```bash
# Start servers and keep running
uv run python cli.py serve

# In another terminal, check status
uv run python cli.py status

# Process an audio file
uv run python cli.py process recording.webm

# List all recordings
uv run python cli.py recordings
```

### PowerShell Wrapper
```powershell
# Same commands but shorter
.\pipeline.ps1 serve
.\pipeline.ps1 status
.\pipeline.ps1 process recording.webm
.\pipeline.ps1 recordings
```

### Typical Workflow
1. **Start servers:** `uv run python cli.py serve`
2. **Record audio:** Go to http://localhost:5173/index.html
3. **Check recordings:** `uv run python cli.py recordings`
4. **Process files:** `uv run python cli.py process audio_file.wav`
5. **Stop servers:** Ctrl+C (or `uv run python cli.py stop` from another terminal)

## Features

- ✅ **Graceful shutdown** - Ctrl+C properly stops servers
- ✅ **Health checks** - Verifies servers are responding
- ✅ **File processing** - Process audio files from command line
- ✅ **Recording management** - List and view saved recordings
- ✅ **Status monitoring** - Check server and storage status
- ✅ **Error handling** - Clear error messages and recovery

## Prerequisites

Same as the main project:
- UV environment with dependencies installed
- Ollama running with model pulled (default: gemma3:4b)
- ffmpeg available on PATH

## Output

All recordings are saved to `recordings/` directory:
- `YYYYMMDD_HHMMSS_recording.webm` - Audio files
- `YYYYMMDD_HHMMSS_metadata.json` - Metadata with transcript and results

## Troubleshooting

### Servers won't start
- Check if ports 8000 and 5173 are available
- Ensure UV environment is set up: `uv sync`
- Verify Ollama is running: `ollama list`

### Processing fails
- Check server status: `uv run python cli.py status`
- Ensure Ollama model is available
- Check audio file format (supports webm, wav, mp3, etc.)

### Web UI not accessible
- Verify web server is running on port 5173
- Try accessing http://localhost:5173/index.html directly
- Check firewall/antivirus blocking the port
