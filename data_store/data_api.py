import os
import requests
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from data_model import db, AudioRecording, RecordingImageGeneration
from playhouse.shortcuts import model_to_dict
import logging
from data_api_models import (
    AudioRecordingCreate,
    TranscriptionUpdate,
    PromptsUpdate,
    ImageGenerationCreate,
    ImageGenerationUpdate,
    BatchImageGenerationCreate,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup/shutdown events"""
    if db.is_closed():
        db.connect()
    yield
    if not db.is_closed():
        db.close()


app = FastAPI(lifespan=lifespan)


AUDIO_PROCESSOR_URL = os.getenv("AUDIO_PROCESSOR_URL", "http://localhost:8001")


async def init_audio_processing(recording_id: int, audio_file_path: str):
    """Initiates audio processing by making request to processing service"""
    try:
        response = requests.post(
            f"{AUDIO_PROCESSOR_URL}/process-audio/",
            json={"recording_id": str(recording_id), "source_file": audio_file_path},
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to initiate audio processing: {str(e)}"
        )


@app.post("/recordings/")
async def create_recording(recording: AudioRecordingCreate):
    """Create a new audio recording entry in the database"""
    try:
        with db.atomic():
            db_recording = AudioRecording(
                audio_file_path=recording.audio_file_path,
                parent_audio_recording=recording.parent_audio_recording_id,
                parent_time=recording.parent_time,
            )
            db_recording.save()

            await init_audio_processing(db_recording.id, db_recording.audio_file_path)

            return {
                "id": db_recording.id,
                "audio_file_path": db_recording.audio_file_path,
                "created_date": db_recording.created_date.isoformat(),
                "updated_date": db_recording.updated_date.isoformat(),
                "parent_audio_recording": db_recording.parent_audio_recording_id,
                "parent_time": db_recording.parent_time,
            }
    except Exception as e:
        logger.error(f"Error creating recording: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/recordings/{id}/transcription")
async def update_transcription(id: int, update: TranscriptionUpdate):
    """Update the transcription for a recording"""
    try:
        with db.atomic():
            recording = AudioRecording.get_by_id(id)
            recording.transcription = update.transcription
            recording.save()
            return {"message": "Transcription updated successfully"}
    except AudioRecording.DoesNotExist:
        raise HTTPException(status_code=404, detail="Recording not found")
    except Exception as e:
        logger.error(f"Error updating transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/recordings/{id}/prompts")
async def update_prompts(id: int, update: PromptsUpdate):
    """Update the prompts for a recording"""
    try:
        with db.atomic():
            recording = AudioRecording.get_by_id(id)
            recording.prompts = update.prompts
            recording.save()
            return {"message": "Prompts updated successfully"}
    except AudioRecording.DoesNotExist:
        raise HTTPException(status_code=404, detail="Recording not found")
    except Exception as e:
        logger.error(f"Error updating prompts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recordings/{recording_id}/image-generations/")
async def create_image_generation(
    recording_id: int, image_generation: ImageGenerationCreate
):
    """Create a new image generation entry for an audio recording"""
    try:
        # Verify the audio recording exists
        try:
            AudioRecording.get_by_id(recording_id)
        except AudioRecording.DoesNotExist:
            raise HTTPException(status_code=404, detail="Audio recording not found")

        with db.atomic():
            db_image_generation = RecordingImageGeneration(
                audio_recording_id=recording_id,
                prompt=image_generation.prompt,
                image_file_path=image_generation.image_file_path,
                seed=image_generation.seed,
                request_payload=image_generation.request_payload,
                status=image_generation.status,
            )
            db_image_generation.save()

            return {
                "id": db_image_generation.id,
                "audio_recording_id": db_image_generation.audio_recording_id,
                "image_file_path": db_image_generation.image_file_path,
                "seed": db_image_generation.seed,
                "request_payload": db_image_generation.request_payload,
                "status": db_image_generation.status,
                "created_date": db_image_generation.created_date.isoformat(),
                "updated_date": db_image_generation.updated_date.isoformat(),
            }
    except Exception as e:
        logger.error(f"Error creating image generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/recordings/{recording_id}/image-generations/{generation_id}")
async def update_image_generation(
    recording_id: int, generation_id: int, update: ImageGenerationUpdate
):
    """Update an existing image generation entry"""
    try:
        # Verify the audio recording exists
        try:
            AudioRecording.get_by_id(recording_id)
        except AudioRecording.DoesNotExist:
            raise HTTPException(status_code=404, detail="Audio recording not found")

        # Get the image generation
        try:
            image_generation = RecordingImageGeneration.get(
                (RecordingImageGeneration.id == generation_id)
                & (RecordingImageGeneration.audio_recording_id == recording_id)
            )
        except RecordingImageGeneration.DoesNotExist:
            raise HTTPException(status_code=404, detail="Image generation not found")

        # Update only provided fields
        with db.atomic():
            update_dict = update.model_dump(exclude_unset=True)
            if update_dict:
                for field, value in update_dict.items():
                    setattr(image_generation, field, value)
                image_generation.save()

            return {
                "id": image_generation.id,
                "audio_recording_id": image_generation.audio_recording_id,
                "image_file_path": image_generation.image_file_path,
                "seed": image_generation.seed,
                "request_payload": image_generation.request_payload,
                "status": image_generation.status,
                "created_date": image_generation.created_date.isoformat(),
                "updated_date": image_generation.updated_date.isoformat(),
            }
    except Exception as e:
        logger.error(f"Error updating image generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recordings/{recording_id}/tree")
async def get_recording_tree(recording_id: int):
    """Get the tree of recordings for a given recording"""
    try:
        recording = AudioRecording.get_by_id(recording_id)
        return [
            model_to_dict(recording, recurse=False)
            for recording in recording.get_tree()
        ]
    except AudioRecording.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Recording {recording_id} not found")
    except Exception as e:
        logger.error(f"Error getting recording tree: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recordings/{recording_id}/image-generations/batch")
async def create_image_generations_batch(recording_id: int, batch: BatchImageGenerationCreate):
    """Create multiple image generation entries for an audio recording in a single transaction"""
    try:
        # Verify the audio recording exists
        try:
            AudioRecording.get_by_id(recording_id)
        except AudioRecording.DoesNotExist:
            raise HTTPException(status_code=404, detail="Audio recording not found")

        created_generations = []
        with db.atomic():
            for gen in batch.generations:
                db_image_generation = RecordingImageGeneration(
                    audio_recording_id=recording_id,
                    prompt=gen.prompt,
                    image_file_path=gen.image_file_path,
                    seed=gen.seed,
                    request_payload=gen.request_payload,
                    status=gen.status,
                )
                db_image_generation.save()
                created_generations.append({
                    "id": db_image_generation.id,
                    "audio_recording_id": recording_id,
                    "status": db_image_generation.status,
                    "created_date": db_image_generation.created_date.isoformat(),
                    "updated_date": db_image_generation.updated_date.isoformat(),
                })

            return created_generations
    except Exception as e:
        logger.error(f"Error creating batch image generations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
