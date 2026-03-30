# config.py
import os
from dotenv import load_dotenv

load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")

MODEL_NAME = "command-a-03-2025"
TEMPERATURE = 0
MAX_RETRIES = 2
