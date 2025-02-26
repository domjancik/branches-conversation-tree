from data_model import db, AudioRecording, RecordingImageGeneration

db.connect()
db.drop_tables([AudioRecording, RecordingImageGeneration])
db.create_tables([AudioRecording, RecordingImageGeneration])