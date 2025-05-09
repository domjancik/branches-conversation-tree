import ollama
import json
from typing import List

PROMPT_COUNT = 6

def get_image_prompts(text: str, ollama_model: str = "llama3.1:8b", prompt_count: int = PROMPT_COUNT, max_retries: int = 4) -> List[str]:
    retries = 0
    while retries < max_retries:
        try:
            model = ollama.generate(
                model=ollama_model,
                prompt=f"Generate {prompt_count} image prompts for the following text: {text}. Respond in a JSON string array format only, no other text.",
                stream=False
            )
            print(model.response)
            parsed_response = json.loads(model.response)

            # Validate the response format
            if not isinstance(parsed_response, list) or not all(isinstance(item, str) for item in parsed_response):
                raise ValueError("Invalid response format. Expected a list of strings.")

            return parsed_response
        except (ValueError, json.JSONDecodeError) as e:
            retries += 1
            if retries == max_retries:
                raise Exception(f"Failed to parse JSON response after {max_retries} attempts. Last error: {str(e)}")
            print(f"Failed to parse JSON (attempt {retries}/{max_retries}). Retrying...")