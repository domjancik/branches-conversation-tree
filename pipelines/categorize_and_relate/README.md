# Categorize & Relate Pipeline

This pipeline templates prompt.md and invokes Ollama to categorize input text, create category relationships, and surface open topics.

Defaults
- Model: gemma3:4b
- Temperature: 0
- Seed: 42

Files
- prompt.md – the base prompt template
- run.ps1 – PowerShell runner
- run.py – Python runner
- sample_input.txt – example input text
- categories.json – optional pre-existing categories
- vars.json – optional templating variables

Placeholders supported in prompt.md
- {{RAW_TEXT}} – replaced with the input text (or legacy <PASTE RAW TEXT HERE>)
- {{CATEGORIES_JSON}} – injected raw JSON from --categories/-CategoriesPath
- {{CATEGORIES_BULLETS}} – a human-readable summary of categories

If no categories placeholders are present but categories are provided, the scripts append a "Known categories" JSON section before the Input block.

Requires
- Ollama installed and running locally
- gemma3:4b model pulled: `ollama pull gemma3:4b`
- PowerShell 7+ or Python 3.8+
- Python Ollama SDK: `pip install ollama` or `pip install -r requirements.txt`

Quick start (PowerShell)
- Preview prompt rendering:
  `Get-Content .\sample_input.txt | .\run.ps1 -DryRun`

- Run with input only:
  `./run.ps1 -InputPath .\sample_input.txt`

- Run with categories and save output:
  `./run.ps1 -InputPath .\sample_input.txt -CategoriesPath .\categories.json -OutputPath .\result.json`

- Provide templating variables:
  `./run.ps1 -InputPath .\sample_input.txt -Var "PROJECT=Demo" -Var "AUTHOR=Alice"`

Quick start (Python)
- Install SDK (once):
  `pip install -r requirements.txt`

- Preview prompt rendering (no API call):
  `type .\sample_input.txt | python .\run.py --dry-run`

- Run with input only:
  `python .\run.py --input .\sample_input.txt`

- Run with categories and save output:
  `python .\run.py --input .\sample_input.txt --categories .\categories.json --output .\result.json`

- Provide templating variables:
  `python .\run.py --input .\sample_input.txt --var PROJECT=Demo --var AUTHOR=Alice`

Advanced
- Change model or settings:
  - PS: `./run.ps1 -InputPath .\sample_input.txt -Model "gemma3:4b" -Temperature 0 -Seed 42`
  - Py: `python .\run.py --input .\sample_input.txt --model gemma3:4b --temperature 0 --seed 42`

Text Range Features
- Each segment includes `text_ranges` array with character positions for visual highlighting
- Python script validates and enhances text ranges with fuzzy matching
- Supports trimming audio recordings and visual annotation of transcripts
- Provides `actual_text` and `corrected_*` fields for range validation

Notes
- The Python runner uses the Ollama SDK. It will try to extract clean JSON from the model output by:
  1) Parsing a ```json fenced block if present, else
  2) Parsing the first {...} JSON object found.
  If neither works, it writes the raw output.
- Text ranges are validated and corrected when possible for accuracy
- Both scripts return non-zero exit codes and print error output if `ollama generate` fails.
- Stdout contains the model response unless `-OutputPath/--output` is provided.

## Run the UI (Audio -> Whisper -> Categorize & Relate)

The UI is a static page in `web/` that records microphone audio and POSTs it to the FastAPI server in `server/`.

1. Start the API (from inside `pipelines/categorize_and_relate/server`):
   - With uv:
     `uv run -m uvicorn main:app --reload --port 8000`
   - Or with venv:
     `python -m venv .venv && .venv/Scripts/activate && pip install -r requirements.txt && uvicorn main:app --reload --port 8000`

   Optional env vars:
   - `FAST_WHISPER_MODEL` = tiny|base|small|medium (default: small)
   - `WHISPER_DEVICE` = cpu|cuda (default: cpu)

2. Serve the UI:
   `cd web && python -m http.server 3001` then open http://localhost:3001

3. Use the UI:
   Click "Start Recording" then "Stop" to send audio to `http://localhost:8000/process-audio` and display JSON results.
