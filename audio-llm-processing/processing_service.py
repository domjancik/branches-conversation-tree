from queue import Queue, PriorityQueue
import threading
import math
from typing import Optional, Tuple
import whisper
import librosa
from data_client import (
    update_transcription,
    update_prompts,
    create_image_generations_batch,
    update_image_generation,
    ImageGenerationUpdate,
    ImageGenerationCreate,
)
from image_prompt_generation import get_image_prompts
from image_generation import generate_image, ImageGenerationResult
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
import time
from collections import defaultdict

load_dotenv()

logger = logging.getLogger(__name__)

# STYLES = ["Mk Lite Brite Art"]
STYLES = ["Mk Gyotaku", "Mk Luminogram"]

prompt_suffix = os.getenv("PROMPT_SUFFIX")
image_generations_path = os.getenv("IMAGE_GENERATIONS_PATH")
audio_recordings_path = os.getenv("AUDIO_RECORDINGS_PATH")
ollama_model = os.getenv("OLLAMA_MODEL")

# Configuration
MAX_QUEUE_SIZE = 1000  # Maximum number of items in each queue
MAX_RETRIES = 3  # Maximum number of retries for failed image generations
RETRY_DELAY = 5  # Delay in seconds between retries


def get_image_file_name(file_base_name: str, image_generation_id: str, index: int, style: str):
    iso_date = datetime.now().isoformat()
    file_name = f"{file_base_name}_{index}_{image_generation_id}_{style}_{iso_date}.png"
    file_name = file_name.replace(":", "-").replace(" ", "-")
    return file_name


class AudioProcessingService:
    def __init__(self):
        logger.info("Initializing AudioProcessingService")
        self.new_recording_queue = Queue(maxsize=MAX_QUEUE_SIZE)  # Queue for new recording requests
        self.image_generation_queue = PriorityQueue(maxsize=MAX_QUEUE_SIZE)  # Queue for image generation tasks
        self.whisper_model: Optional[whisper.Whisper] = None
        self.is_running = False
        self.recording_thread: Optional[threading.Thread] = None
        self.image_thread: Optional[threading.Thread] = None
        self.metrics = defaultdict(lambda: {"count": 0, "total_time": 0})  # Track processing metrics

    def start(self):
        if self.is_running:
            return

        logger.info("Starting AudioProcessingService")

        self.is_running = True
        self.whisper_model = whisper.load_model("medium")
        
        # Start separate threads for recording processing and image generation
        self.recording_thread = threading.Thread(target=self._process_recordings)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        self.image_thread = threading.Thread(target=self._process_image_generations)
        self.image_thread.daemon = True
        self.image_thread.start()

    def stop(self):
        logger.info("Stopping AudioProcessingService")
        self.is_running = False
        if self.recording_thread:
            self.new_recording_queue.put(None)  # Sentinel to stop the thread
            self.recording_thread.join()
        if self.image_thread:
            self.image_generation_queue.put((float('inf'), None))  # Sentinel to stop the thread
            self.image_thread.join()
        self.whisper_model = None

    def add_processing_request(self, recording_id: str, source_file: str):
        try:
            # Add to new recording queue for immediate processing
            self.new_recording_queue.put((recording_id, source_file), block=False)
            logger.info(f"Added recording {recording_id} to processing queue")
        except Queue.Full:
            logger.error(f"Recording queue is full, could not add recording {recording_id}")
            raise

    def _process_recordings(self):
        while self.is_running:
            try:
                item = self.new_recording_queue.get()
                if item is None:  # Sentinel value to stop the thread
                    logger.info("Received stop signal, stopping recording processing thread")
                    break

                recording_id, source_file = item
                start_time = time.time()
                logger.info(
                    f"Processing new recording {recording_id} from {source_file}"
                )
                try:
                    self._process_audio(recording_id, source_file)
                    logger.info(f"Successfully processed recording {recording_id}")
                except Exception as e:
                    logger.error(
                        f"Error processing {recording_id}: {str(e)}", exc_info=True
                    )
                finally:
                    self.new_recording_queue.task_done()
                    # Update metrics
                    duration = time.time() - start_time
                    self.metrics["recording_processing"]["count"] += 1
                    self.metrics["recording_processing"]["total_time"] += duration
            except Exception as e:
                logger.error(f"Recording queue processing error: {str(e)}", exc_info=True)

    def _process_image_generations(self):
        while self.is_running:
            try:
                priority, item = self.image_generation_queue.get()
                if item is None:  # Sentinel value to stop the thread
                    logger.info("Received stop signal, stopping image generation thread")
                    break

                recording_id, prompt, image_generation_id = item
                start_time = time.time()
                logger.info(
                    f"Generating image for recording {recording_id}, prompt index {priority}"
                )
                try:
                    self._generate_and_store_image(recording_id, prompt, image_generation_id, priority)
                    logger.info(f"Successfully generated image for {recording_id}, prompt index {priority}")
                except Exception as e:
                    logger.error(
                        f"Error generating image for {recording_id}, prompt index {priority}: {str(e)}",
                        exc_info=True,
                    )
                finally:
                    self.image_generation_queue.task_done()
                    # Update metrics
                    duration = time.time() - start_time
                    self.metrics["image_generation"]["count"] += 1
                    self.metrics["image_generation"]["total_time"] += duration
            except Exception as e:
                logger.error(f"Image generation queue processing error: {str(e)}", exc_info=True)

    def _create_pending_image_generations(self, recording_id: str, prompts: list[str]) -> list[Tuple[str, str]]:
        image_generations = [
            ImageGenerationCreate(
                audio_recording_id=recording_id,
                prompt=prompt,
            )
            for prompt in prompts
        ]
        image_generation_ids = create_image_generations_batch(recording_id, image_generations)
        return list(zip(image_generation_ids, prompts))

    def _store_image(
        self,
        recording_id: str,
        image_generation_id: str,
        index: int,
        image_result: ImageGenerationResult,
    ):
        style = image_result.request_payload["style_selections"][0]
        file_name = get_image_file_name(str(recording_id), image_generation_id, index, style)

        file_path = os.path.join(image_generations_path, file_name)
        with open(file_path, "wb") as f:
            f.write(image_result.image_data)

        return file_name

    def _generate_and_store_image(self, recording_id: str, prompt: str, image_generation_id: str, index: int):
        retries = 0
        while retries < MAX_RETRIES:
            try:
                image_result = generate_image(prompt + prompt_suffix, STYLES)
                file_name = self._store_image(recording_id, image_generation_id, index, image_result)

                update_image_generation(
                    recording_id,
                    image_generation_id,
                    ImageGenerationUpdate(
                        image_file_path=file_name,
                        seed=image_result.seed,
                        request_payload=image_result.request_payload,
                        status="completed",
                        duration=image_result.duration,
                    ),
                )
                break  # Success, exit retry loop
                
            except Exception as e:
                retries += 1
                if retries == MAX_RETRIES:
                    logger.error(
                        f"Error generating image for {recording_id}, prompt index {index} after {MAX_RETRIES} retries: {str(e)}",
                        exc_info=True,
                    )
                    update_image_generation(
                        recording_id,
                        image_generation_id,
                        ImageGenerationUpdate(
                            status="failed",
                            reason=str(e),
                        ),
                    )
                else:
                    logger.warning(
                        f"Retry {retries}/{MAX_RETRIES} for image {index} for {recording_id}: {str(e)}"
                    )
                    time.sleep(RETRY_DELAY)

    def _get_audio_duration(self, file_path: str) -> float:
        """Get the duration of an audio file in seconds."""
        try:
            duration = librosa.get_duration(path=file_path)
            return duration
        except Exception as e:
            logger.error(f"Error getting audio duration for {file_path}: {str(e)}", exc_info=True)
            return 0.0

    def _process_audio(self, recording_id: str, source_file: str):
        logger.info(f"Starting transcription for {recording_id} from {source_file}")
        source_file_path = os.path.join(audio_recordings_path, source_file)
        
        # Get audio duration before processing
        duration = self._get_audio_duration(source_file_path)
        logger.info(f"Audio duration for {recording_id}: {duration:.2f} seconds")
        
        transcription = self._transcribe_audio(source_file_path)
        logger.info(f"Transcription complete for {recording_id}, updating database. Transcription: {transcription}")
        update_transcription(recording_id, transcription)

        # Generate image prompts
        prompt_count = math.ceil(duration / 5)
        logger.info(f"Generating {prompt_count} image prompts for {recording_id}")
        prompts = get_image_prompts(transcription, ollama_model, prompt_count)
        logger.info(f"Updating prompts for {recording_id}")
        update_prompts(recording_id, prompts)
        logger.info(f"Processing complete for {recording_id}")

        # Create pending image generations and queue each prompt individually
        image_generation_id_prompt_pairs = self._create_pending_image_generations(recording_id, prompts)
        for index, (image_generation_id, prompt) in enumerate(image_generation_id_prompt_pairs):
            # Queue each prompt with its index as priority
            self.image_generation_queue.put((index, (recording_id, prompt, image_generation_id)))

    def _transcribe_audio(self, source_file: str) -> str:
        result = self.whisper_model.transcribe(
            source_file, language="en", task="translate"
        )
        return result["text"]

    def get_metrics(self):
        """Get current processing metrics"""
        return {
            "recording_queue_size": self.new_recording_queue.qsize(),
            "image_queue_size": self.image_generation_queue.qsize(),
            "recording_processing": {
                "count": self.metrics["recording_processing"]["count"],
                "avg_time": self.metrics["recording_processing"]["total_time"] / max(1, self.metrics["recording_processing"]["count"])
            },
            "image_generation": {
                "count": self.metrics["image_generation"]["count"],
                "avg_time": self.metrics["image_generation"]["total_time"] / max(1, self.metrics["image_generation"]["count"])
            }
        }
