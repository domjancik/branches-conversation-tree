from peewee import *
from playhouse.sqlite_ext import *
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

db = SqliteDatabase(os.getenv("DB_PATH"))

class BaseModel(Model):
    class Meta:
        database = db

class AudioRecording(BaseModel):
    class Meta:
        table_name = "audio_recordings"
    audio_file_path = TextField()
    created_date = DateTimeField(default=datetime.datetime.now)
    updated_date = DateTimeField(default=datetime.datetime.now)
    transcription = TextField(null=True)
    prompts = JSONField(null=True)
    parent_audio_recording = ForeignKeyField('self', backref='child_audio_recordings', null=True)
    parent_time = FloatField(null=True)
    duration = FloatField(null=True)

    def save(self, *args, **kwargs):
        self.updated_date = datetime.datetime.now()
        return super().save(*args, **kwargs)


class RecordingImageGeneration(BaseModel):
    class Meta:
        table_name = "recording_image_generations"
    audio_recording_id = ForeignKeyField(AudioRecording, backref='image_generations')
    created_date = DateTimeField(default=datetime.datetime.now)
    updated_date = DateTimeField(default=datetime.datetime.now)
    image_file_path = TextField(null=True)
    seed = IntegerField(null=True)
    prompt = TextField()
    reason = TextField(null=True)
    duration = FloatField(null=True)
    request_payload = JSONField(null=True)
    status = TextField(default="pending", choices=[("pending", "pending"), ("generating", "generating"), ("completed", "completed"), ("failed", "failed")])

    def save(self, *args, **kwargs):
        self.updated_date = datetime.datetime.now()
        return super().save(*args, **kwargs)
