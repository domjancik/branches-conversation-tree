import requests
import json
import os
from dataclasses import dataclass
import time
import logging
from dotenv import load_dotenv
import base64

load_dotenv()

logger = logging.getLogger(__name__)

host = os.getenv("IMAGE_GENERATION_API_URL")


@dataclass
class ImageGenerationResult:
    url: str
    seed: int
    request_payload: dict
    duration: float
    image_data: bytes


def text2img(params: dict) -> dict:
    """
    text to image
    """
    result = requests.post(
        url=f"{host}/v1/generation/text-to-image",
        data=json.dumps(params),
        headers={"Content-Type": "application/json"},
    )
    return result.json()


def generate_image(prompt: str, styles: list[str], negative_prompt: str = None):
    print(f"Generating image for prompt: {prompt}")
    time_start = time.time()
    params = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "aspect_ratios_selection": "1024*1024",
        "performance_selection": "Extreme Speed",
        "style_selections": styles,
        "advanced_params": {
            "overwrite_step": 4,
            "overwrite_switch": 1,
        }
    }
    result = text2img(params)
    logger.info(json.dumps(result, indent=4))
    image_url = result[0]["url"]
    if image_url.startswith('data:'):
        # Handle data URL
        # Remove the data URL prefix and get the base64 data
        image_data = base64.b64decode(image_url.split(',')[1])
    else:
        # Handle regular URL
        image_data = requests.get(image_url).content
    duration = time.time() - time_start
    logger.info(f"Time taken: {duration} seconds")

    return ImageGenerationResult(
        url=image_url,
        seed=result[0]["seed"],
        request_payload=params,
        duration=duration,
        image_data=image_data,
    )
