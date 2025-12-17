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


class ProgressUpdate(BaseModel):
    progress: float  # 0.0 to 100.0
    step: Optional[int] = None
    total_steps: Optional[int] = None
    status: str = "generating"

    @field_validator("progress")
    @classmethod
    def validate_progress(cls, v):
        if v < 0.0 or v > 100.0:
            raise ValueError("progress must be between 0.0 and 100.0")
        return v


class TranscriptionStatus(BaseModel):
    status: Optional[str] = None  # "pending" | "completed" | null
    text: Optional[str] = None
    updated_date: Optional[str] = None


class ImageGenerationStatus(BaseModel):
    total: int
    pending: int
    generating: int
    completed: int
    failed: int
    progress: float  # percentage of completed images (0-100)
    generations: List[Dict]


class ProcessingStatusResponse(BaseModel):
    recording_id: int
    transcription: TranscriptionStatus
    image_generation: ImageGenerationStatus
    overall_status: str  # "pending" | "transcribing" | "generating_prompts" | "generating_images" | "completed" | "failed"
    created_date: str
    updated_date: str


class QueueInfo(BaseModel):
    size: int
    max_size: int
    is_active: bool


class ThreadStatus(BaseModel):
    recording_thread_alive: bool
    image_thread_alive: bool


class ProcessingMetrics(BaseModel):
    total_processed: int
    avg_time_seconds: float


class QueueStatusSummary(BaseModel):
    total_queued: int
    has_active_work: bool


class QueueStatusResponse(BaseModel):
    service_status: str
    is_active: bool
    queues: Dict[str, QueueInfo]
    threads: ThreadStatus
    metrics: Dict[str, ProcessingMetrics]
    summary: QueueStatusSummary