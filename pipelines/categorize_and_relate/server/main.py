import io
import json
import os
import tempfile
import subprocess
import sys
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent
RUN_PY = PIPELINE_DIR / "run.py"
CATEGORIES_JSON = PIPELINE_DIR / "categories.json"
RECORDINGS_DIR = PIPELINE_DIR / "recordings"

# Ensure recordings directory exists
RECORDINGS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Categorize & Relate Audio Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/recordings")
def list_recordings():
    """List all saved recordings with metadata."""
    recordings = []
    
    for metadata_file in RECORDINGS_DIR.glob("*_metadata.json"):
        try:
            metadata = json.loads(metadata_file.read_text())
            # Check if audio file still exists
            audio_path = RECORDINGS_DIR / metadata.get("audio_file", "")
            metadata["audio_exists"] = audio_path.exists()
            recordings.append(metadata)
        except Exception as e:
            continue
    
    # Sort by timestamp descending (newest first)
    recordings.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {
        "recordings": recordings,
        "count": len(recordings)
    }


def transcribe_with_whisper(audio_path: Path) -> str:
    """Transcribe audio using faster-whisper. Returns transcript string."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Audio transcription failed: faster-whisper package not installed. Install with: pip install faster-whisper. Error: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Audio transcription failed: Could not import faster-whisper. Error: {e}"
        )

    # Model size: small or base for speed; make configurable via env FAST_WHISPER_MODEL
    model_name = os.environ.get("FAST_WHISPER_MODEL", "small")
    device = os.environ.get("WHISPER_DEVICE", "cpu")
    
    try:
        model = WhisperModel(model_name, device=device)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Audio transcription failed: Could not load Whisper model '{model_name}' on device '{device}'. "
                   f"Try setting FAST_WHISPER_MODEL to 'tiny' or 'base' for smaller models. Error: {e}"
        )

    try:
        segments, info = model.transcribe(str(audio_path), beam_size=1)
        # Concatenate segments
        parts = []
        for seg in segments:
            parts.append(seg.text)
        transcript = " ".join(parts).strip()
        
        if not transcript:
            raise HTTPException(
                status_code=500,
                detail="Audio transcription failed: Whisper produced empty transcript. "
                       "The audio file may be too quiet, corrupted, or contain no speech."
            )
        
        return transcript
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Audio transcription failed: Error during transcription process. "
                   f"Audio file: {audio_path.name}. Error: {e}"
        )


def run_categorize_and_relate(transcript: str) -> str:
    """Run run.py by piping transcript to stdin. Returns stdout string (expected JSON)."""
    if not RUN_PY.is_file():
        raise HTTPException(
            status_code=500, 
            detail=f"Categorization pipeline not found: run.py missing at {RUN_PY}. "
                   f"Ensure the pipeline script exists and is accessible."
        )

    # Validate transcript
    if not transcript or not transcript.strip():
        raise HTTPException(
            status_code=400,
            detail="Categorization failed: Empty transcript provided. The audio may not contain any speech."
        )

    cmd = [
        "uv", "run", "python",
        str(RUN_PY),
    ]
    if CATEGORIES_JSON.is_file():
        cmd += ["--categories", str(CATEGORIES_JSON)]

    try:
        proc = subprocess.run(
            cmd,
            input=transcript,
            text=True,
            capture_output=True,
            cwd=str(PIPELINE_DIR),
            check=False,
            timeout=60  # Add timeout to prevent hanging
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500, 
            detail="Categorization failed: Pipeline timed out after 60 seconds. "
                   "The transcript may be too long or the AI model is not responding."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Categorization failed: Could not start pipeline process. "
                   f"Command: {' '.join(cmd)}. Error: {e}"
        )

    if proc.returncode != 0:
        # Parse different types of errors
        error_output = proc.stderr or proc.stdout or "Unknown error"
        
        if "ollama" in error_output.lower():
            if "failed to connect" in error_output.lower():
                raise HTTPException(
                    status_code=500, 
                    detail="Categorization failed: Cannot connect to Ollama AI service. "
                           "Please ensure Ollama is installed and running. Visit https://ollama.com for setup instructions."
                )
            elif "model not found" in error_output.lower():
                raise HTTPException(
                    status_code=500,
                    detail="Categorization failed: AI model not found. "
                           "Please run 'ollama pull gemma3:4b' to install the required model."
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Categorization failed: Ollama AI service error. {error_output}"
                )
        elif "prompt.md" in error_output.lower():
            raise HTTPException(
                status_code=500,
                detail="Categorization failed: Pipeline configuration missing (prompt.md not found). "
                       "The pipeline may be misconfigured."
            )
        elif "importerror" in error_output.lower():
            raise HTTPException(
                status_code=500,
                detail="Categorization failed: Missing required Python packages. "
                       "Please install dependencies with 'uv sync' or 'pip install -r requirements.txt'."
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Categorization failed: Pipeline error (exit code {proc.returncode}). "
                       f"Error details: {error_output[:500]}{'...' if len(error_output) > 500 else ''}"
            )

    if not proc.stdout or not proc.stdout.strip():
        raise HTTPException(
            status_code=500,
            detail="Categorization failed: Pipeline produced no output. The AI model may have failed to process the transcript."
        )

    return proc.stdout


@app.post("/test-categorization")
async def test_categorization(text: str):
    """Test endpoint to categorize text directly without audio processing."""
    try:
        output_text = run_categorize_and_relate(text)
        obj = json.loads(output_text)
        return JSONResponse({
            "result": obj,
            "metadata": {
                "test_input": text,
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {e}")

@app.post("/process-audio")
async def process_audio(file: UploadFile = File(...)):
    # Validate file upload
    if not file or not file.filename:
        raise HTTPException(
            status_code=400, 
            detail="Audio processing failed: No file uploaded. Please select an audio file to process."
        )
    
    # Check file size (optional, but helpful)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Audio processing failed: File too large ({file.size / 1024 / 1024:.1f}MB). Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB."
        )
    
    # Generate timestamp-based filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = Path(file.filename or "upload").suffix or ".webm"
    audio_filename = f"{timestamp}_recording{suffix}"
    audio_path = RECORDINGS_DIR / audio_filename
    
    try:
        # Save uploaded audio persistently
        try:
            data = await file.read()
            if not data:
                raise HTTPException(
                    status_code=400,
                    detail="Audio processing failed: Empty file uploaded. Please record some audio first."
                )
            audio_path.write_bytes(data)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Audio processing failed: Could not save uploaded file. Error: {e}"
            )
        
        # Transcribe audio
        try:
            transcript = transcribe_with_whisper(audio_path)
        except HTTPException:
            raise  # Re-raise detailed transcription errors
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Audio processing failed: Unexpected error during transcription. Error: {e}"
            )
        
        # Categorize transcript
        try:
            output_text = run_categorize_and_relate(transcript)
        except HTTPException:
            raise  # Re-raise detailed categorization errors
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Audio processing failed: Unexpected error during categorization. Error: {e}"
            )

        # Save metadata alongside audio
        try:
            metadata = {
                "timestamp": timestamp,
                "audio_file": audio_filename,
                "transcript": transcript,
                "processing_result": output_text
            }
            metadata_path = RECORDINGS_DIR / f"{timestamp}_metadata.json"
            metadata_path.write_text(json.dumps(metadata, indent=2))
        except Exception as e:
            # Non-critical error - log but don't fail
            print(f"Warning: Could not save metadata: {e}")

        # Parse and return results
        try:
            obj = json.loads(output_text)
            # Include metadata in response
            response_obj = {
                "result": obj,
                "metadata": {
                    "audio_file": audio_filename,
                    "transcript": transcript,
                    "timestamp": timestamp
                }
            }
            return JSONResponse(response_obj)
        except json.JSONDecodeError as e:
            # AI returned non-JSON - this might be a problem but let's return it anyway
            return JSONResponse({
                "result": output_text,
                "metadata": {
                    "audio_file": audio_filename,
                    "transcript": transcript,
                    "timestamp": timestamp
                },
                "warning": "AI returned non-JSON response - this may indicate an issue with the categorization."
            })
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Audio processing failed: Could not format response. Raw output available but may be malformed. Error: {e}"
            )
            
    except HTTPException:
        # Clean up on HTTP errors (these have user-friendly messages)
        if audio_path.exists():
            try:
                audio_path.unlink()
            except Exception:
                pass
        raise
    except Exception as e:
        # Clean up on unexpected errors
        if audio_path.exists():
            try:
                audio_path.unlink()
            except Exception:
                pass
        raise HTTPException(
            status_code=500,
            detail=f"Audio processing failed: An unexpected error occurred. Please try again. Error: {e}"
        )
