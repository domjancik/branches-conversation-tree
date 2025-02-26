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