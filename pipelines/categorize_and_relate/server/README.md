# Audio -> Whisper -> Categorize & Relate (FastAPI)

This server accepts audio from the browser, transcribes it using faster-whisper, then pipes the transcript to the existing pipelines/categorize_and_relate/run.py and returns the JSON result.

Prerequisites
- Python 3.9+
- ffmpeg available on PATH (for audio decoding)
- Ollama running locally and the model used in run.py pulled (default gemma3:4b)

Setup
1. Create venv and install deps:
   python -m venv .venv
   .venv/Scripts/activate  # Windows PowerShell
   pip install -r requirements.txt

2. Run server:
   uvicorn server.main:app --reload --port 8000

Environment
- FAST_WHISPER_MODEL: set to base|small|medium for accuracy/speed tradeoff (default: small)
- WHISPER_DEVICE: cpu or cuda (if you have GPU)

Endpoints
- GET /health -> { status: "ok" }
- POST /process-audio -> multipart/form-data with field "file"; returns JSON or text
