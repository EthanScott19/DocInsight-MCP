# llm_client.py

import cohere
from .config import COHERE_API_KEY, MODEL_NAME, TEMPERATURE

co = cohere.Client(COHERE_API_KEY)


def call_llm(prompt: str) -> str:
    response = co.chat(
        model=MODEL_NAME,
        message=prompt,
        temperature=TEMPERATURE
    )

    return response.text.strip()
