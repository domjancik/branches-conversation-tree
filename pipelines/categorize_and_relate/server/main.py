import io
import json
import os
import tempfile
import subprocess
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"faster-whisper not available: {e}")

    # Model size: small or base for speed; make configurable via env FAST_WHISPER_MODEL
    model_name = os.environ.get("FAST_WHISPER_MODEL", "small")
    model = WhisperModel(model_name, device=os.environ.get("WHISPER_DEVICE", "cpu"))

    segments, info = model.transcribe(str(audio_path), beam_size=1)
    # Concatenate segments
    parts = []
    for seg in segments:
        parts.append(seg.text)
    return " ".join(parts).strip()


def run_categorize_and_relate(transcript: str) -> str:
    """Run run.py by piping transcript to stdin. Returns stdout string (expected JSON)."""
    if not RUN_PY.is_file():
        raise HTTPException(status_code=500, detail=f"run.py not found at {RUN_PY}")

    cmd = [
        "python",
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
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed invoking pipeline: {e}")

    if proc.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Pipeline error (code {proc.returncode}): {proc.stderr or proc.stdout}")

    return proc.stdout


@app.post("/process-audio")
async def process_audio(file: UploadFile = File(...)):
    # Generate timestamp-based filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = Path(file.filename or "upload").suffix or ".webm"
    audio_filename = f"{timestamp}_recording{suffix}"
    audio_path = RECORDINGS_DIR / audio_filename
    
    try:
        # Save uploaded audio persistently
        data = await file.read()
        audio_path.write_bytes(data)
        
        transcript = transcribe_with_whisper(audio_path)
        if not transcript:
            raise HTTPException(status_code=500, detail="Empty transcript from whisper")

        output_text = run_categorize_and_relate(transcript)

        # Save metadata alongside audio
        metadata = {
            "timestamp": timestamp,
            "audio_file": audio_filename,
            "transcript": transcript,
            "processing_result": output_text
        }
        metadata_path = RECORDINGS_DIR / f"{timestamp}_metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2))

        # Try to parse JSON, else return as text
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
        except Exception:
            # Not strict JSON; return as text with metadata
            return JSONResponse({
                "result": output_text,
                "metadata": {
                    "audio_file": audio_filename,
                    "transcript": transcript,
                    "timestamp": timestamp
                }
            })
    except Exception as e:
        # Clean up on error
        if audio_path.exists():
            try:
                audio_path.unlink()
            except Exception:
                pass
        raise e
