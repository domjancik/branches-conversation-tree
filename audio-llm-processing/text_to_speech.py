import whisper
import json


def transcribe_audio(source_file: str) -> str:
    model = whisper.load_model("medium")  # Can use "tiny", "small", "medium", or "large"
    result = model.transcribe(source_file, language="en", task="translate")  # Auto-detects Hebrew & English
    print(json.dumps(result, indent=4))
    return result["text"]