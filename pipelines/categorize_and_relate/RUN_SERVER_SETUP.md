# Audio → Whisper → Categorize & Relate — Setup Notes

Status: Paused (Python 3.11 not installed yet)

Context
- Backend: FastAPI at pipelines/categorize_and_relate/server/main.py
- Web UI: pipelines/categorize_and_relate/web (MediaRecorder → POST → JSON)
- Pipeline: pipelines/categorize_and_relate/run.py (Ollama SDK)

Blocker
- faster-whisper pulled PyAV which failed to build on Python 3.13.
- Solution picked: use Python 3.11 venv for this server.

Prerequisites
- ffmpeg available on PATH
- Ollama running locally with model pulled (default: gemma3:4b)

Next Steps (Option A: Python 3.11 venv)
1) Install Python 3.11 (one time):
   winget install -e --id Python.Python.3.11

2) Create and activate venv (in this directory):
   py -3.11 -m venv .venv311
   . .venv311\Scripts\Activate.ps1

3) Install backend deps:
   pip install -r server\requirements.txt

4) Run backend:
   uvicorn pipelines.categorize_and_relate.server.main:app --reload --port 8000

5) Serve UI (in a separate terminal):
   python -m http.server 5173 --directory web
   # Open http://localhost:5173/index.html

Optional Environment
- FAST_WHISPER_MODEL=small|base|medium (default: small)
- WHISPER_DEVICE=cpu|cuda

Troubleshooting
- If whisper transcription is slow: try FAST_WHISPER_MODEL=base and/or use GPU with WHISPER_DEVICE=cuda (if available).
- If /process-audio returns a pipeline error: ensure Ollama is running and gemma3:4b is pulled, or adjust run.py model via flags.

Tracking
- MCP Task: Resolve server run issue (install Python 3.11, venv setup, start servers)
- Local tracking: ./.rels (id: resolve-python311-env)

