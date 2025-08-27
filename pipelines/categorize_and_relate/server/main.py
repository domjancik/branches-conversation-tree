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

# Import session manager
sys.path.append(str(Path(__file__).parent.parent))
from session_manager import SessionManager, SessionContext

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent
RUN_PY = PIPELINE_DIR / "run.py"
CATEGORIES_JSON = PIPELINE_DIR / "categories.json"
RECORDINGS_DIR = PIPELINE_DIR / "recordings"

# Ensure recordings directory exists
RECORDINGS_DIR.mkdir(exist_ok=True)

# Initialize session manager
session_manager = SessionManager(RECORDINGS_DIR)

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
    """List all saved recordings with metadata (backwards compatibility)."""
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


@app.get("/sessions")
def list_sessions():
    """List all pipeline sessions with metadata."""
    sessions = session_manager.list_sessions()
    return {
        "sessions": sessions,
        "count": len(sessions)
    }


@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    """Get detailed information about a specific session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    return {
        "session_id": session_id,
        "metadata": session.get_metadata(),
        "artifacts": session.list_artifacts(),
        "summary": session.get_summary()
    }


@app.get("/sessions/{session_id}/artifacts/{artifact_name}")
def get_session_artifact(session_id: str, artifact_name: str):
    """Retrieve a specific artifact from a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    if not session.has_artifact(artifact_name):
        raise HTTPException(
            status_code=404,
            detail=f"Artifact {artifact_name} not found in session {session_id}"
        )
    
    artifact = session.get_artifact(artifact_name)
    artifact_info = session.get_artifact_info(artifact_name)
    
    return {
        "artifact_name": artifact_name,
        "content": artifact,
        "metadata": artifact_info
    }


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete a session and all its artifacts."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    try:
        session.cleanup()
        return {"message": f"Session {session_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session {session_id}: {e}"
        )


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
    """Process audio file with session-based artifact storage."""
    # Validate file upload
    if not file or not file.filename:
        raise HTTPException(
            status_code=400, 
            detail="Audio processing failed: No file uploaded. Please select an audio file to process."
        )
    
    # Check file size
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Audio processing failed: File too large ({file.size / 1024 / 1024:.1f}MB). Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB."
        )
    
    # Use session manager for organized artifact storage
    with SessionContext(session_manager) as session:
        try:
            session.update_status('audio_upload', 'Processing uploaded audio file')
            
            # Read and validate audio data
            audio_data = await file.read()
            if not audio_data:
                raise HTTPException(
                    status_code=400,
                    detail="Audio processing failed: Empty file uploaded. Please record some audio first."
                )
            
            # Save original audio file
            original_filename = file.filename or "upload.webm"
            suffix = Path(original_filename).suffix or ".webm"
            audio_filename = f"audio{suffix}"
            
            session.save_artifact(
                audio_filename, 
                audio_data, 
                'binary',
                metadata={
                    'original_filename': original_filename,
                    'content_type': file.content_type,
                    'file_size': len(audio_data)
                }
            )
            
            # Get audio path for processing
            audio_path = session.session_dir / "artifacts" / audio_filename
            
            session.update_status('transcribing', 'Transcribing audio with Whisper')
            
            # Transcribe audio
            try:
                from faster_whisper import WhisperModel
                model_name = os.environ.get("FAST_WHISPER_MODEL", "small")
                device = os.environ.get("WHISPER_DEVICE", "cpu")
                
                model = WhisperModel(model_name, device=device)
                segments, info = model.transcribe(str(audio_path), beam_size=1)
                
                # Save detailed transcription info
                detailed_segments = []
                transcript_parts = []
                
                for seg in segments:
                    segment_info = {
                        'start': seg.start,
                        'end': seg.end,
                        'text': seg.text,
                        'no_speech_prob': getattr(seg, 'no_speech_prob', None),
                        'avg_logprob': getattr(seg, 'avg_logprob', None)
                    }
                    detailed_segments.append(segment_info)
                    transcript_parts.append(seg.text)
                
                transcript = " ".join(transcript_parts).strip()
                
                if not transcript:
                    raise HTTPException(
                        status_code=500,
                        detail="Audio transcription failed: Whisper produced empty transcript. "
                               "The audio file may be too quiet, corrupted, or contain no speech."
                    )
                
                # Save transcription artifacts
                session.save_artifact('transcript', transcript, 'text')
                session.save_intermediate('whisper', 'detailed_segments', detailed_segments, 'json')
                session.save_intermediate('whisper', 'model_info', {
                    'model_name': model_name,
                    'device': device,
                    'language': info.language,
                    'language_probability': info.language_probability,
                    'duration': info.duration
                }, 'json')
                
            except ImportError as e:
                session.log_error(f"faster-whisper not installed: {e}", 'transcription')
                raise HTTPException(
                    status_code=500, 
                    detail=f"Audio transcription failed: faster-whisper package not installed. Install with: pip install faster-whisper. Error: {e}"
                )
            except Exception as e:
                session.log_error(f"Transcription error: {e}", 'transcription')
                raise HTTPException(
                    status_code=500,
                    detail=f"Audio transcription failed: Error during transcription process. Error: {e}"
                )
            
            session.update_status('categorizing', 'Running categorization pipeline')
            
            # Run categorization pipeline
            try:
                cmd = ["uv", "run", "python", str(RUN_PY)]
                if CATEGORIES_JSON.is_file():
                    cmd += ["--categories", str(CATEGORIES_JSON)]
                
                proc = subprocess.run(
                    cmd,
                    input=transcript,
                    text=True,
                    capture_output=True,
                    cwd=str(PIPELINE_DIR),
                    check=False,
                    timeout=60
                )
                
                # Save pipeline execution details
                session.save_intermediate('pipeline', 'execution_info', {
                    'command': cmd,
                    'return_code': proc.returncode,
                    'execution_time': datetime.now().isoformat()
                }, 'json')
                
                if proc.stderr:
                    session.save_intermediate('pipeline', 'stderr', proc.stderr, 'text')
                if proc.stdout:
                    session.save_intermediate('pipeline', 'stdout', proc.stdout, 'text')
                
                if proc.returncode != 0:
                    error_msg = proc.stderr or proc.stdout or "Unknown error"
                    session.log_error(f"Pipeline failed: {error_msg}", 'categorization')
                    raise HTTPException(
                        status_code=500,
                        detail=f"Categorization failed: Pipeline error (exit code {proc.returncode}). "
                               f"Error details: {error_msg[:500]}{'...' if len(error_msg) > 500 else ''}"
                    )
                
                if not proc.stdout or not proc.stdout.strip():
                    session.log_error("Pipeline produced no output", 'categorization')
                    raise HTTPException(
                        status_code=500,
                        detail="Categorization failed: Pipeline produced no output. The AI model may have failed to process the transcript."
                    )
                
                output_text = proc.stdout
                
            except subprocess.TimeoutExpired:
                session.log_error("Pipeline timeout", 'categorization')
                raise HTTPException(
                    status_code=500, 
                    detail="Categorization failed: Pipeline timed out after 60 seconds. "
                           "The transcript may be too long or the AI model is not responding."
                )
            except Exception as e:
                session.log_error(f"Pipeline execution error: {e}", 'categorization')
                raise HTTPException(
                    status_code=500, 
                    detail=f"Categorization failed: Could not start pipeline process. Error: {e}"
                )
            
            session.update_status('finalizing', 'Processing results and saving final artifacts')
            
            # Parse and save categorization results
            try:
                categorization_result = json.loads(output_text)
                session.save_artifact('categorization', categorization_result, 'json')
                
                # Also save raw LLM output for debugging
                session.save_intermediate('llm', 'raw_response', output_text, 'text')
                
            except json.JSONDecodeError as e:
                session.log_error(f"Invalid JSON from pipeline: {e}", 'parsing')
                # Save as text if JSON parsing fails
                session.save_artifact('categorization_raw', output_text, 'text')
                categorization_result = output_text
            
            session.update_status('completed', 'Audio processing completed successfully')
            
            # Prepare response with session information
            response_data = {
                "result": categorization_result,
                "metadata": {
                    "session_id": session.session_id,
                    "timestamp": session.get_metadata()['created'],
                    "audio_file": audio_filename,
                    "transcript": transcript,
                    "artifacts": session.list_artifacts(),
                    "processing_steps": len(session.get_metadata().get('processing_steps', [])),
                    "session_summary": session.get_summary()
                }
            }
            
            # Also maintain backwards compatibility with old format
            old_format_metadata = {
                "timestamp": session.session_id.split('_')[0] + '_' + session.session_id.split('_')[1],
                "audio_file": f"{session.session_id}_{audio_filename}",
                "transcript": transcript,
                "processing_result": output_text if isinstance(categorization_result, str) else json.dumps(categorization_result)
            }
            
            # Save old format metadata for backwards compatibility
            old_metadata_path = RECORDINGS_DIR / f"{old_format_metadata['timestamp']}_metadata.json"
            try:
                old_metadata_path.write_text(json.dumps(old_format_metadata, indent=2))
            except Exception as e:
                print(f"Warning: Could not save backwards compatibility metadata: {e}")
            
            return JSONResponse(response_data)
            
        except HTTPException:
            # Re-raise HTTP exceptions (these have proper error messages)
            raise
        except Exception as e:
            # Log unexpected errors and convert to HTTP exception
            session.log_error(f"Unexpected error: {e}", 'unknown')
            raise HTTPException(
                status_code=500,
                detail=f"Audio processing failed: An unexpected error occurred. Session ID: {session.session_id}. Error: {e}"
            )
