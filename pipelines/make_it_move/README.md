# Make It Move Pipeline

A Python pipeline that transforms static images into videos by:
1. Analyzing the image with Ollama's Qwen multimodal model
2. Generating a movement/animation prompt 
3. Creating a video using FramePack via Gradio

## Prerequisites

Before using this pipeline, ensure you have:

1. **Ollama** running locally with Qwen multimodal model
   - Install Ollama: https://ollama.ai/
   - Pull Qwen model: `ollama pull qwen2-vl`
   - Verify it's running: `ollama list`

2. **FramePack** running via Pinokio with Gradio interface
   - Should be accessible at `http://127.0.0.1:7860` (default)
   - Verify by opening the URL in your browser

## Installation

1. Navigate to the pipelines directory:
   ```bash
   cd C:\Users\magne\dev\branches-conversation-tree\pipelines
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Command Line Interface

Run the pipeline from command line:

```bash
python make_it_move_pipeline.py "path/to/your/image.jpg"
```

#### Options:
- `--output-dir`: Output directory for generated videos (default: `./output`)
- `--ollama-host`: Ollama server URL (default: `http://localhost:11434`)
- `--framepack-url`: FramePack Gradio URL (default: `http://127.0.0.1:7860`)
- `--qwen-model`: Qwen model name (default: `qwen2-vl`)

#### Examples:
```bash
# Basic usage
python make_it_move_pipeline.py "C:\Users\magne\Pictures\photo.jpg"

# Custom output directory
python make_it_move_pipeline.py "photo.jpg" --output-dir "C:\Videos\Generated"

# Custom Ollama host
python make_it_move_pipeline.py "photo.jpg" --ollama-host "http://192.168.1.100:11434"
```

### Python API

Use the pipeline programmatically:

```python
from make_it_move_pipeline import MakeItMovePipeline

# Initialize pipeline
pipeline = MakeItMovePipeline(
    ollama_host="http://localhost:11434",
    framepack_gradio_url="http://127.0.0.1:7860",
    qwen_model="qwen2-vl"
)

# Generate video from image
video_path = pipeline.run_pipeline(
    image_path="path/to/image.jpg",
    output_dir="./output"
)

if video_path:
    print(f"Video generated: {video_path}")
```

### Example Usage Script

Run the example script (update the image path first):

```bash
python example_usage.py
```

## Pipeline Steps

1. **Image Analysis**: Qwen analyzes the input image and identifies:
   - Objects/subjects that could move
   - Natural movements they might make
   - Environmental effects (wind, water, lighting)
   - Suitable camera movements

2. **Prompt Generation**: Creates a detailed movement prompt optimized for video generation

3. **Video Generation**: Sends the image and prompt to FramePack via Gradio API

4. **Output**: Returns the path to the generated video file

## Configuration

### Qwen Model

The pipeline uses `qwen2-vl` by default. If you have a different Qwen model:

```bash
python make_it_move_pipeline.py "image.jpg" --qwen-model "your-qwen-model-name"
```

### FramePack Parameters

The pipeline uses these default parameters for video generation:
- Frames: 16
- Resolution: 1024x576
- Inference steps: 25
- Guidance scale: 7.5

To modify these, edit the `generate_video_via_gradio` method in `make_it_move_pipeline.py`.

## Troubleshooting

### Common Issues:

1. **Ollama Connection Error**
   - Ensure Ollama is running: `ollama list`
   - Check if Qwen model is available: `ollama list | grep qwen`
   - Verify Ollama host URL

2. **FramePack Connection Error**  
   - Ensure FramePack/Gradio is running
   - Check the Gradio URL in your browser
   - Verify the API endpoints are accessible

3. **Image Upload Fails**
   - Check image file exists and is readable
   - Ensure image format is supported (JPG, PNG, etc.)
   - Try with a different image

4. **Video Generation Timeout**
   - Video generation can take several minutes
   - Check FramePack logs for errors
   - Try with lower resolution or fewer frames

### Debug Mode

Add debug prints to troubleshoot API calls:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## File Structure

```
pipelines/
├── make_it_move_pipeline.py    # Main pipeline class
├── example_usage.py           # Example usage script  
├── requirements.txt           # Python dependencies
├── README.md                 # This file
└── output/                   # Generated videos (created automatically)
```

## License

This pipeline is provided as-is for educational and development purposes.

