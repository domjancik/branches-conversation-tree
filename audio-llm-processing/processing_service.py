from queue import Queue
import threading
from typing import Optional
import whisper
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

load_dotenv()

logger = logging.getLogger(__name__)

# STYLES = ["Mk Lite Brite Art"]
STYLES = ["Mk Gyotaku", "Mk Luminogram"]

prompt_suffix = os.getenv("PROMPT_SUFFIX")
image_generations_path = os.getenv("IMAGE_GENERATIONS_PATH")
audio_recordings_path = os.getenv("AUDIO_RECORDINGS_PATH")
ollama_model = os.getenv("OLLAMA_MODEL")


def get_image_file_name(file_base_name: str, image_generation_id: str, index: int, style: str):
    iso_date = datetime.now().isoformat()
    file_name = f"{file_base_name}_{index}_{image_generation_id}_{style}_{iso_date}.png"
    file_name = file_name.replace(":", "-").replace(" ", "-")
    return file_name


class AudioProcessingService:
    def __init__(self):
        logger.info("Initializing AudioProcessingService")
        self.processing_queue = Queue()
        self.whisper_model: Optional[whisper.Whisper] = None
        self.is_running = False
        self.processing_thread: Optional[threading.Thread] = None

    def start(self):
        if self.is_running:
            return

        logger.info("Starting AudioProcessingService")

        self.is_running = True
        self.whisper_model = whisper.load_model("medium")
        self.processing_thread = threading.Thread(target=self._process_queue)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def stop(self):
        logger.info("Stopping AudioProcessingService")
        self.is_running = False
        if self.processing_thread:
            self.processing_queue.put(None)  # Sentinel to stop the thread
            self.processing_thread.join()
        self.whisper_model = None

    def add_processing_request(self, recording_id: str, source_file: str):
        self.processing_queue.put((recording_id, source_file))

    def _process_queue(self):
        while self.is_running:
            try:
                item = self.processing_queue.get()
                if item is None:  # Sentinel value to stop the thread
                    logger.info("Received stop signal, stopping processing thread")
                    break

                recording_id, source_file = item
                logger.info(
                    f"Processing audio file {source_file} for recording {recording_id}"
                )
                try:
                    self._process_audio(recording_id, source_file)
                    logger.info(f"Successfully processed recording {recording_id}")
                except Exception as e:
                    logger.error(
                        f"Error processing {recording_id}: {str(e)}", exc_info=True
                    )
                finally:
                    self.processing_queue.task_done()
            except Exception as e:
                logger.error(f"Queue processing error: {str(e)}", exc_info=True)

    def _create_pending_image_generations(self, recording_id: str, prompts: list[str]):
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

    def _generate_and_store_images(self, recording_id, prompts: list[str]):
        image_generation_id_prompt_pairs = self._create_pending_image_generations(recording_id, prompts)

        for index, (image_generation_id, prompt) in enumerate(image_generation_id_prompt_pairs):
            logger.info(
                f"Generating image {index}/{len(prompts)} for {recording_id}, image generation id: {image_generation_id}"
            )

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
            except Exception as e:
                logger.error(
                    f"Error generating image {index}/{len(prompts)} for {recording_id}, image generation id: {image_generation_id}: {str(e)}",
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

    def _process_audio(self, recording_id: str, source_file: str):
        logger.info(f"Starting transcription for {recording_id} from {source_file}")
        source_file_path = os.path.join(audio_recordings_path, source_file)
        transcription = self._transcribe_audio(source_file_path)
        logger.info(f"Transcription complete for {recording_id}, updating database")
        update_transcription(recording_id, transcription)

        logger.info(f"Generating image prompts for {recording_id}")
        prompts = get_image_prompts(transcription, ollama_model)
        logger.info(f"Updating prompts for {recording_id}")
        update_prompts(recording_id, prompts)
        logger.info(f"Processing complete for {recording_id}")

        logger.info(f"Generating images for {recording_id}")
        self._generate_and_store_images(recording_id, prompts)
        logger.info(f"Images generated for {recording_id}")

    def _transcribe_audio(self, source_file: str) -> str:
        result = self.whisper_model.transcribe(
            source_file, language="en", task="translate"
        )
        return result["text"]
