# config.py

import os

COHERE_API_KEY = os.getenv("COHERE_API_KEY")

MODEL_NAME = "command-r-plus"
TEMPERATURE = 0
MAX_RETRIES = 2