# Pipeline Storage and Orchestration

This document explains what the current pipeline stores, where it stores it, what intermediate artifacts are missing, and proposes a complete artifact strategy and orchestration approach. It also evaluates chaining/orchestration frameworks and when Temporal would be beneficial.

## Current State (as implemented)

Components:
- Frontend: static web UI serving the recorder
- Backend: FastAPI (server/main.py)
- Pipeline: run.py (templating + Ollama call)

Storage currently performed by the backend (server/main.py):
- Saved audio file: recordings/<timestamp>_recording.<ext>
- Saved metadata JSON: recordings/<timestamp>_metadata.json containing:
  - timestamp
  - audio_file
  - transcript (string from faster-whisper)
  - processing_result (string: the exact stdout from run.py; may be JSON text)

What is NOT stored today:
- Transcription internals: whisper segments, language detection, timings
- Rendered prompt passed to the LLM
- Model/options used (model name, temperature, seed)
- Raw LLM response before any cleaning
- Cleaned and enhanced JSON as a separate, strongly-typed file
- Categories snapshot actually used (categories.json at runtime)
- Execution context (app version, SDK versions, env configuration)
- Any error objects with stack traces or structured error codes
- Correlation IDs linking artifacts for each request

Summary: we persist the audio and a single metadata JSON with transcript and final pipeline stdout, but not the intermediate artifacts that aid reproducibility, debugging, and analytics.

## Proposed Artifact Strategy

Adopt a per-request session directory under recordings/ that groups all artifacts:

recordings/
  <YYYYMMDD_HHMMSS>/
    audio/
      original.<ext>                      # exact uploaded audio
      working.wav                         # optional decoded PCM for processing
    transcription/
      transcript.txt                      # final text used downstream
      whisper_info.json                   # language, timings, scores
      whisper_segments.json               # segment-by-segment detail
      logs.txt                            # optional transcription logs
    llm/
      prompt_rendered.md                  # rendered prompt after templating
      response_raw.txt                    # raw response from the model
      response_clean.json                 # extracted/cleaned JSON (if parseable)
      response_enhanced.json              # post-processed with text range validation
      model_config.json                   # model, temperature, seed, options
    inputs/
      categories.json                     # snapshot of categories provided/used
      vars.json                           # snapshot of template variables
    context/
      execution.json                      # versions, env, host info, git commit
      request.json                        # inbound request metadata (content-type, size)
    outputs/
      result.json                         # canonical final JSON for use by UI
      metadata.json                       # high-level summary pointing to all artifacts
    errors/
      error.json                          # present on failure with structured details

Metadata.json should include:
- id: <timestamp or UUID>
- created_at, duration_ms
- pointers to each produced artifact
- status: success|failed
- hashes (optional) for audio and outputs

Retention policy:
- Default keep all for N days (e.g., 30)
- Optionally compress older sessions
- CLI/server flags: KEEP_DAYS, COMPRESS_OLD=true

## Changes required to implement

Minimal step-wise plan:
1) Assign a run_id per request (timestamp or ULID) and create recordings/<run_id>/
2) Save transcript to transcription/transcript.txt (in addition to metadata)
3) Extend run.py to optionally emit:
   - prompt_rendered.md
   - response_raw.txt
   - response_clean.json
   - response_enhanced.json
   - model_config.json
   Controlled via env PIPELINE_ARTIFACT_DIR or --artifacts <dir>
4) In server/main.py, pass PIPELINE_ARTIFACT_DIR to the subprocess environment, and after completion, write outputs/result.json and outputs/metadata.json
5) On errors, capture stderr/stdout into errors/error.json

Optional enhancements:
- Log structured timing for each step (transcribe_ms, llm_ms, total_ms)
- Hash artifact contents for dedup and integrity
- Include UI build/version in execution context

## Is every output stored (including intermediate steps)?

Today: No.
- Stored: audio file, a single metadata JSON that embeds transcript and the final pipeline stdout string.
- Missing: intermediate artifacts (rendered prompt, raw/clean/enhanced LLM outputs, whisper segment details, model options, structured error objects, execution context, etc.).

With the proposed strategy: Yes.
- All intermediate and final artifacts are captured and organized per run.
- Results become reproducible and auditable.

## Chaining and Orchestration Options

Goals to consider:
- Durable execution across restarts
- Clear step boundaries (transcribe -> analyze -> post-process -> persist -> notify)
- Retries with backoff, idempotency, cancellation, and timeouts
- Human-in-the-loop (optional)
- Observability and replays

Frameworks:

1) LangChain / LlamaIndex (prompt chaining)
- Strengths: High-level LLM prompting patterns, chains, tools, RAG
- Weaknesses: Not an orchestrator; no durable timers or workflow semantics
- Fit: Good for prompt composition in-process; complement, not a replacement for orchestration

2) Prefect
- Strengths: Pythonic flows and tasks, orchestration UI, retries, caching, task mapping, result storage
- Weaknesses: Requires separate backend/agent for full power; less focus on ultra-long-running, durable timers
- Fit: Excellent lightweight orchestrator for this pipeline; great developer ergonomics, artifact handling, and observability

3) Dagster
- Strengths: Strong data-asset and ops modeling, rich UI, sensors/schedules, metadata integration
- Weaknesses: Heavier than Prefect for small pipelines
- Fit: Great if the project evolves into broader data platform with assets and lineage

4) Apache Airflow
- Strengths: Mature scheduling, DAGs, enterprise adoption
- Weaknesses: Batch orientation, heavier ops overhead, less ideal for event-driven, short-lived LLM calls
- Fit: Overkill here

5) Temporal (durable workflow orchestration)
- Strengths: "Code as workflows", built-in durability, timeouts, retries, heartbeats, signals/queries, versioning, long-running activities. Survives process restarts and network blips. Strong guarantees.
- Weaknesses: Operational overhead (server or Temporal Cloud), learning curve. Windows dev is fine; deploy needs service.
- Fit: Ideal if you want strong reliability, exactly-once semantics, cancellations, and workflows that may wait (e.g., human approval, backoffs) or spawn sub-workflows. Great for production-grade audio+LLM pipelines.

Recommendation:
- Near-term: Prefect for quick wins (simple flow: transcribe -> analyze -> post-process -> persist), plus artifact storage as proposed. Prefect’s result storage and task retries fit well, minimal infra.
- If/when the pipeline needs strong durability, SLAs, or interactivity: migrate to Temporal workflows. Temporal is ideal for: 
  - Guaranteed retries with backoff on Whisper/LLM calls
  - Idempotent activities (e.g., artifact writes) with deduplication
  - Signals for user actions (approve/correct transcript)
  - Long timers (scheduled follow-ups) and replays

## Temporal-based Workflow Sketch

Activities (idempotent):
- save_audio(in): returns artifact path
- transcribe(audio_path) -> transcript + segments
- analyze(transcript, config) -> raw_output
- postprocess(raw_output, transcript) -> clean/enhanced JSON
- persist(run_id, artifacts) -> write to outputs/ and metadata.json
- notify(run_id, status)

Workflow:
- On request: create run_id
- Call activities sequentially with retries and timeouts; record progress in workflow state
- On errors: surface structured error and partial artifacts; allow retry
- On completion: emit event/notification (WebSocket/Webhook)

## Implementation Plan (stepwise)

Phase 1 (low-risk, high-value):
- Introduce run_id and session directories
- Persist transcript, prompt_rendered, raw/clean/enhanced outputs, model options
- Update metadata.json to reference artifacts
- Add env PIPELINE_ARTIFACT_DIR propagation and CLI flag in run.py

Phase 2 (observability & robustness):
- Add timings, structured error objects, and request.json
- Create a CLI to list and inspect runs (summaries and artifacts)
- Add retention job (compress or delete older runs)

Phase 3 (orchestration):
- Prefect flow with tasks for each step and artifact storage
- Optional: Temporal PoC for durable orchestration

## Open Questions
- PII policy for transcripts and recordings (retention, encryption)
- Versioned prompts and models: pinning vs rolling updates
- Multi-model fallback (if model A unavailable)
- Where to host orchestrator (local vs cloud)

## Quick Checklist for Adoption
- [ ] Add run_id session directory creation
- [ ] Pass PIPELINE_ARTIFACT_DIR to run.py and write artifacts
- [ ] Write outputs/result.json and outputs/metadata.json canonically
- [ ] Add retention and pruning job
- [ ] (Optional) Prefect flow for the steps
- [ ] (Optional) Temporal PoC for durable orchestration

