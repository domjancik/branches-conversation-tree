conda deactivate
python -m uvicorn data_api:app --host 0.0.0.0 --port 8000 --reload