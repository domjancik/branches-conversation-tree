from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict


class AudioRecordingCreate(BaseModel):
    audio_file_path: str
    parent_audio_recording_id: Optional[int] = None
    parent_time: Optional[float] = None

    @field_validator("audio_file_path")
    @classmethod
    def validate_audio_file_path(cls, v):
        if not v.strip():
            raise ValueError("audio_file_path cannot be empty")
        return v


class TranscriptionUpdate(BaseModel):
    transcription: str


class PromptsUpdate(BaseModel):
    prompts: List[str]


class ImageGenerationCreate(BaseModel):
    audio_recording_id: int
    image_file_path: Optional[str] = None
    seed: Optional[int] = None
    request_payload: Optional[Dict] = None
    prompt: str
    status: str = "pending"
    reason: Optional[str] = None

    @field_validator("image_file_path")
    @classmethod
    def validate_image_file_path(cls, v):
        if v is not None and not v.strip():
            raise ValueError("image_file_path cannot be empty")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ["pending", "generating", "completed", "failed"]
        if v not in valid_statuses:
            raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
        return v


class ImageGenerationUpdate(BaseModel):
    image_file_path: Optional[str] = None
    seed: Optional[int] = None
    request_payload: Optional[Dict] = None
    prompt: Optional[str] = None
    status: Optional[str] = None
    reason: Optional[str] = None
    duration: Optional[float] = None

    @field_validator("image_file_path")
    @classmethod
    def validate_image_file_path(cls, v):
        if v is not None and not v.strip():
            raise ValueError("image_file_path cannot be empty if provided")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["pending", "generating", "completed", "failed"]
            if v not in valid_statuses:
                raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
        return v


class BatchImageGenerationCreate(BaseModel):
    generations: List[ImageGenerationCreate]

    @field_validator("generations")
    @classmethod
    def validate_generations(cls, v):
        if not v:
            raise ValueError("generations list cannot be empty")
        return v