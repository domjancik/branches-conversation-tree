import os
import requests
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
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
    ProgressUpdate,
    ProcessingStatusResponse,
    TranscriptionStatus,
    ImageGenerationStatus,
)
from typing import Optional

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
                "progress": 100.0 if db_image_generation.status == "completed" else (50.0 if db_image_generation.status == "generating" else 0.0),
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
                "progress": 100.0 if image_generation.status == "completed" else (50.0 if image_generation.status == "generating" else 0.0),
                "created_date": image_generation.created_date.isoformat(),
                "updated_date": image_generation.updated_date.isoformat(),
            }
    except Exception as e:
        logger.error(f"Error updating image generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recordings/{recording_id}/tree")
async def get_recording_tree(
    recording_id: int,
    only_parents: bool = Query(False, description="Only return parent recordings"),
    max_depth: Optional[int] = Query(None, description="Maximum depth of the tree to return"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to return")
):
    """Get the tree of recordings for a given recording"""
    try:
        recording = AudioRecording.get_by_id(recording_id)
        tree = recording.get_tree()
        
        # Filter to only parents if requested
        if only_parents:
            tree = [r for r in tree if r.id != recording_id]
        
        # Convert to dict and filter fields if specified
        result = [model_to_dict(r, recurse=False) for r in tree]
        if fields:
            field_list = [f.strip() for f in fields.split(",")]
            result = [{k: v for k, v in r.items() if k in field_list} for r in result]
            
        return result
    except AudioRecording.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Recording {recording_id} not found")
    except Exception as e:
        logger.error(f"Error getting recording tree: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recordings/{recording_id}/parent-context")
async def get_parent_context(
    recording_id: int,
    max_depth: Optional[int] = Query(None, description="Maximum depth of parent context to return")
):
    """Get the context from parent recordings for a given recording"""
    try:
        recording = AudioRecording.get_by_id(recording_id)
        tree = recording.get_tree()
        
        # Filter to only parents and sort by created_date
        parents = [r for r in tree if r.id != recording_id]
        parents.sort(key=lambda x: x.created_date)
        
        # Get transcriptions from parent recordings
        context = []
        for parent in parents:
            if parent.transcription:
                context.append({
                    "id": parent.id,
                    "created_date": parent.created_date.isoformat(),
                    "transcription": parent.transcription
                })
        
        return {
            "recording_id": recording_id,
            "parent_context": context
        }
    except AudioRecording.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Recording {recording_id} not found")
    except Exception as e:
        logger.error(f"Error getting parent context: {str(e)}")
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


@app.get("/recordings/{recording_id}/processing-status", response_model=ProcessingStatusResponse)
async def get_processing_status(recording_id: int):
    """Get current processing status for a recording (transcription and image generation)"""
    try:
        recording = AudioRecording.get_by_id(recording_id)
        
        # Get transcription status
        transcription_status = TranscriptionStatus(
            status="completed" if recording.transcription else "pending",
            text=recording.transcription,
            updated_date=recording.updated_date.isoformat() if recording.transcription else None
        )
        
        # Get all image generations for this recording
        image_generations = list(RecordingImageGeneration.select().where(
            RecordingImageGeneration.audio_recording_id == recording_id
        ).order_by(RecordingImageGeneration.created_date))
        
        # Calculate image generation statistics
        total = len(image_generations)
        pending = sum(1 for gen in image_generations if gen.status == "pending")
        generating = sum(1 for gen in image_generations if gen.status == "generating")
        completed = sum(1 for gen in image_generations if gen.status == "completed")
        failed = sum(1 for gen in image_generations if gen.status == "failed")
        
        # Calculate overall progress (percentage of completed images)
        progress = (completed / total * 100.0) if total > 0 else 0.0
        
        # Build generations list
        generations_list = []
        for gen in image_generations:
            # Compute progress from status: 0% pending, 50% generating, 100% completed, 0% failed
            if gen.status == "completed":
                computed_progress = 100.0
            elif gen.status == "generating":
                computed_progress = 50.0  # Indeterminate progress
            elif gen.status == "failed":
                computed_progress = 0.0
            else:  # pending
                computed_progress = 0.0
            
            gen_dict = {
                "id": gen.id,
                "prompt": gen.prompt,
                "status": gen.status,
                "progress": computed_progress,
                "image_file_path": gen.image_file_path,
                "duration": gen.duration,
                "seed": gen.seed,
                "created_date": gen.created_date.isoformat(),
                "updated_date": gen.updated_date.isoformat(),
            }
            generations_list.append(gen_dict)
        
        image_generation_status = ImageGenerationStatus(
            total=total,
            pending=pending,
            generating=generating,
            completed=completed,
            failed=failed,
            progress=progress,
            generations=generations_list
        )
        
        # Determine overall status
        if recording.transcription is None:
            overall_status = "transcribing"
        elif recording.prompts is None:
            overall_status = "generating_prompts"
        elif total == 0:
            overall_status = "generating_prompts"
        elif generating > 0 or pending > 0:
            overall_status = "generating_images"
        elif failed > 0 and completed == 0:
            overall_status = "failed"
        elif completed == total and total > 0:
            overall_status = "completed"
        else:
            overall_status = "pending"
        
        return ProcessingStatusResponse(
            recording_id=recording_id,
            transcription=transcription_status,
            image_generation=image_generation_status,
            overall_status=overall_status,
            created_date=recording.created_date.isoformat(),
            updated_date=recording.updated_date.isoformat()
        )
    except AudioRecording.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Recording {recording_id} not found")
    except Exception as e:
        logger.error(f"Error getting processing status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/image-generations/{generation_id}/progress")
async def update_generation_progress(generation_id: int, progress_data: ProgressUpdate):
    """Webhook endpoint for streamdiffusion API to report progress (updates status based on progress)"""
    try:
        image_generation = RecordingImageGeneration.get_by_id(generation_id)
        
        with db.atomic():
            # Update status based on progress: if progress is 100%, mark as completed
            # Otherwise, ensure status is "generating" if not already completed/failed
            if progress_data.progress >= 100.0:
                image_generation.status = "completed"
            elif progress_data.status and image_generation.status not in ["completed", "failed"]:
                image_generation.status = progress_data.status
            image_generation.save()
        
        return {
            "message": "Progress updated successfully",
            "generation_id": generation_id,
            "progress": progress_data.progress,
            "status": image_generation.status
        }
    except RecordingImageGeneration.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Image generation {generation_id} not found")
    except Exception as e:
        logger.error(f"Error updating generation progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
