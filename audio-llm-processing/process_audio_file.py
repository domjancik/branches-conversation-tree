from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from processing_service import AudioProcessingService
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

processing_service = AudioProcessingService()

class ProcessingRequest(BaseModel):
    recording_id: str
    source_file: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup/shutdown events"""
    processing_service.start()
    yield
    processing_service.stop()

app = FastAPI(lifespan=lifespan)

@app.post("/process-audio/")
async def process_audio(request: ProcessingRequest):
    logger.info(f"Received processing request for recording_id: {request.recording_id}")
    processing_service.add_processing_request(
        request.recording_id,
        request.source_file
    )
    logger.info(f"Added recording {request.recording_id} to processing queue")
    return {"status": "processing", "recording_id": request.recording_id}


@app.get("/queue-status")
async def get_queue_status():
    """Get current processing queue status and metrics"""
    try:
        metrics = processing_service.get_metrics()
        service_status = "running" if processing_service.is_running else "stopped"
        
        # Get queue sizes
        recording_queue_size = metrics["recording_queue_size"]
        image_queue_size = metrics["image_queue_size"]
        
        # Check thread status (handle None case)
        recording_thread_alive = processing_service.recording_thread.is_alive() if processing_service.recording_thread else False
        image_thread_alive = processing_service.image_thread.is_alive() if processing_service.image_thread else False
        
        # Determine if queues are active (have items or thread is processing)
        recording_is_active = recording_queue_size > 0 or recording_thread_alive
        image_is_active = image_queue_size > 0 or image_thread_alive
        
        # Overall active status
        is_active = recording_is_active or image_is_active
        total_queued = recording_queue_size + image_queue_size
        
        return {
            "service_status": service_status,
            "is_active": is_active,
            "queues": {
                "recording": {
                    "size": recording_queue_size,
                    "max_size": 1000,
                    "is_active": recording_is_active
                },
                "image_generation": {
                    "size": image_queue_size,
                    "max_size": 1000,
                    "is_active": image_is_active
                }
            },
            "threads": {
                "recording_thread_alive": recording_thread_alive,
                "image_thread_alive": image_thread_alive
            },
            "metrics": {
                "recording_processing": {
                    "total_processed": metrics["recording_processing"]["count"],
                    "avg_time_seconds": metrics["recording_processing"]["avg_time"]
                },
                "image_generation": {
                    "total_processed": metrics["image_generation"]["count"],
                    "avg_time_seconds": metrics["image_generation"]["avg_time"]
                }
            },
            "summary": {
                "total_queued": total_queued,
                "has_active_work": is_active
            }
        }
    except Exception as e:
        logger.error(f"Error getting queue status: {str(e)}", exc_info=True)
        return {
            "service_status": "error",
            "is_active": False,
            "queues": {
                "recording": {"size": 0, "max_size": 1000, "is_active": False},
                "image_generation": {"size": 0, "max_size": 1000, "is_active": False}
            },
            "threads": {
                "recording_thread_alive": False,
                "image_thread_alive": False
            },
            "metrics": {
                "recording_processing": {"total_processed": 0, "avg_time_seconds": 0.0},
                "image_generation": {"total_processed": 0, "avg_time_seconds": 0.0}
            },
            "summary": {
                "total_queued": 0,
                "has_active_work": False
            },
            "error": str(e)
        }