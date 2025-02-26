import ollama
import json
from typing import List

def get_image_prompts(text: str, ollama_model: str = "llama3.1:8b", max_retries: int = 3) -> List[str]:
    retries = 0
    while retries < max_retries:
        try:
            model = ollama.generate(
                model=ollama_model,
                prompt=f"Generate 10 image prompts for the following text: {text}. Respond in a JSON array format only, no other text.",
                stream=False
            )
            print(model.response)
            parsed_response = json.loads(model.response)
            return parsed_response
        except json.JSONDecodeError as e:
            retries += 1
            if retries == max_retries:
                raise Exception(f"Failed to parse JSON response after {max_retries} attempts. Last error: {str(e)}")
            print(f"Failed to parse JSON (attempt {retries}/{max_retries}). Retrying...")