# Error Handling Improvements

This document describes the comprehensive error message improvements made to the audio processing pipeline to provide better user feedback and debugging information.

## Issues Addressed

### Original Problem
- Error code 3221225794 was being returned from the web UI with no context
- Generic error messages that didn't help users understand what went wrong
- No guidance on how to fix common issues
- Poor error propagation from pipeline components

### Root Cause
The original issue was caused by the Ollama Python SDK in the uv environment not being able to connect to the Ollama service due to missing explicit host configuration.

## Improvements Made

### 1. Server-Side Error Messages (`server/main.py`)

#### Audio Transcription Errors
- **Before**: `"faster-whisper not available: {e}"`
- **After**: `"Audio transcription failed: faster-whisper package not installed. Install with: pip install faster-whisper. Error: {e}"`

#### Whisper Model Loading Errors
- **Before**: Generic exception handling
- **After**: Detailed error messages with suggestions:
  - Model loading failures with device/model name guidance
  - Empty transcript detection with possible causes
  - Transcription process errors with file information

#### Pipeline Execution Errors
- **Before**: `"Pipeline error (code {proc.returncode}): {proc.stderr or proc.stdout}"`
- **After**: Intelligent error parsing with specific guidance:
  - **Ollama Connection**: "Cannot connect to Ollama AI service. Please ensure Ollama is installed and running. Visit https://ollama.com"
  - **Model Not Found**: "AI model not found. Please run 'ollama pull gemma3:4b'"
  - **Missing Dependencies**: "Missing required Python packages. Please install with 'uv sync'"
  - **Configuration Issues**: "Pipeline configuration missing (prompt.md not found)"

#### File Upload Validation
- **Before**: Basic file handling
- **After**: Comprehensive validation:
  - Empty file detection
  - File size limits with helpful messages
  - Upload failure diagnostics

### 2. Pipeline Script Error Messages (`run.py`)

#### Ollama Connection and Model Management
- **Before**: `"ollama SDK call failed: {e}"`
- **After**: Detailed diagnostics:
  - Connection testing with specific instructions
  - Model availability checking with installation commands
  - Timeout detection with optimization suggestions

#### Input Validation
- **Before**: Generic error messages
- **After**: Specific validation with guidance:
  - Empty input detection
  - File not found errors with path information
  - JSON validation for categories with format guidance

#### Configuration Errors
- **Before**: `"prompt.md not found"`
- **After**: `"Configuration error: prompt.md not found at {path}. Please ensure the pipeline is properly set up with all required files."`

### 3. Error Classification and Response Codes

#### HTTP Status Codes
- **400**: Client errors (bad input, empty files, validation failures)
- **500**: Server errors (service unavailable, processing failures, configuration issues)

#### Exit Codes for CLI
- **0**: Success
- **1**: Runtime/processing errors
- **2**: Configuration/input errors

## Error Message Guidelines

### 1. Structure
All error messages now follow the pattern:
```
[Component] failed: [Specific issue]. [Actionable guidance]. [Technical details if helpful].
```

### 2. User-Friendly Language
- Avoid technical jargon where possible
- Provide clear next steps
- Include relevant commands or links
- Explain likely causes

### 3. Actionable Guidance
Every error message includes at least one of:
- Command to run to fix the issue
- Link to documentation or setup instructions
- Alternative approaches to try
- Configuration changes to make

## Examples of Improved Error Messages

### Before vs After

#### Connection Error
**Before**: `"ollama SDK call failed: Connection refused"`
**After**: `"Cannot connect to Ollama service. Please ensure Ollama is running with 'ollama serve'. Visit https://ollama.com for setup instructions."`

#### Empty Audio
**Before**: `"Empty transcript from whisper"`
**After**: `"Audio transcription failed: Whisper produced empty transcript. The audio file may be too quiet, corrupted, or contain no speech."`

#### Missing Model
**Before**: Generic Ollama error
**After**: `"AI model 'gemma3:4b' not found. Available models: gemma2:2b, llama2:7b. Install with: ollama pull gemma3:4b"`

## Testing the Improvements

### Positive Tests
```bash
# Normal operation
echo "Test message" | uv run python run.py

# With categories
echo "Test message" | uv run python run.py --categories categories.json
```

### Error Scenario Tests
```bash
# Empty input
echo "" | uv run python run.py
# Expected: "Input error: Empty input provided. Please provide some text to categorize."

# Missing file
uv run python run.py --input nonexistent.txt
# Expected: "Input error: Input path not found: nonexistent.txt"

# Invalid categories JSON
echo "test" | uv run python run.py --categories invalid.json
# Expected: "Categories error: Invalid JSON in categories file..."
```

## Benefits

1. **Better User Experience**: Users get clear, actionable feedback instead of cryptic error codes
2. **Faster Debugging**: Developers can quickly identify root causes
3. **Self-Service Support**: Users can often fix issues themselves with the provided guidance
4. **Reduced Support Load**: Fewer unclear error reports
5. **Better Development Workflow**: Clear feedback during development and testing

## Technical Implementation Details

### Error Propagation Chain
1. **Pipeline Script (`run.py`)** → Detailed error messages with exit codes
2. **Server (`main.py`)** → HTTP exceptions with specific error parsing
3. **Web UI** → User-friendly error display (handled by frontend)

### Error Parsing Logic
The server now intelligently parses pipeline output to detect common error patterns:
- Ollama service issues
- Model availability problems
- Configuration missing
- Dependency issues
- Input validation failures

### Timeout and Resource Management
- Added 60-second timeout to prevent hanging requests
- Cleanup of temporary files on errors
- Graceful handling of interrupted processes

## Future Improvements

1. **Structured Error Objects**: Return JSON error objects with error codes, messages, and suggested actions
2. **Error Telemetry**: Log error patterns to identify common issues
3. **Health Checks**: Proactive system health monitoring
4. **Recovery Suggestions**: Automatic retry logic for transient errors
5. **User Guidance Integration**: Link errors to documentation or troubleshooting guides
