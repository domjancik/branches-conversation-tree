import requests
import json
import os
from pydantic import BaseModel
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DATA_STORE_API_URL")


def update_transcription(recording_id: str, transcription: str):
    request_payload = {"transcription": transcription}
    response = requests.put(
        url=f"{host}/recordings/{recording_id}/transcription",
        data=json.dumps(request_payload),
    )
    print(response.json())


def update_prompts(recording_id: str, prompts: list[str]):
    request_payload = {"prompts": prompts}
    response = requests.put(
        url=f"{host}/recordings/{recording_id}/prompts",
        data=json.dumps(request_payload),
    )
    print(json.dumps(response.json(), indent=4))


class ImageGenerationCreate(BaseModel):
    audio_recording_id: int
    prompt: str
    image_file_path: Optional[str] = None
    seed: Optional[int] = None
    request_payload: Optional[Dict] = None
    status: str = "pending"
    duration: Optional[float] = None


def create_image_generation(recording_id: str, image_generation: ImageGenerationCreate):
    response = requests.post(
        url=f"{host}/recordings/{recording_id}/image-generations/",
        data=image_generation.model_dump_json(),
    )
    print(response.json())
    return response.json()["id"]


def create_image_generations_batch(
    recording_id: str, image_generations: list[ImageGenerationCreate]
):
    request_payload = {"generations": [gen.model_dump() for gen in image_generations]}
    response = requests.post(
        url=f"{host}/recordings/{recording_id}/image-generations/batch",
        json=request_payload,
    )
    print("Created image generations response:")
    print(response.json())
    return [gen["id"] for gen in response.json()]


class ImageGenerationUpdate(BaseModel):
    image_file_path: Optional[str] = None
    seed: Optional[int] = None
    request_payload: Optional[Dict] = None
    status: Optional[str] = None
    reason: Optional[str] = None
    duration: Optional[float] = None


def update_image_generation(
    recording_id: str, generation_id: str, image_generation: ImageGenerationUpdate
):
    response = requests.put(
        url=f"{host}/recordings/{recording_id}/image-generations/{generation_id}",
        data=image_generation.model_dump_json(),
    )
    print(response.json())
