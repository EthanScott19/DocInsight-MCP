import json
from .config import MAX_RETRIES
from .prompt import build_prompt
from .llm_client import call_llm
from .parser import extract_json
from .validator import validate_tool_call


def generate_tool_call(user_input: str) -> dict:
    prompt = build_prompt(user_input)

    for attempt in range(MAX_RETRIES):
        response_text = call_llm(prompt)

        try:
            json_text = extract_json(response_text)
            tool_call = json.loads(json_text)

            validate_tool_call(tool_call)
            return tool_call

        except Exception:
            if attempt == MAX_RETRIES - 1:
                raise ValueError(f"LLM failed after retries:\n{response_text}")

    raise ValueError("Unexpected error while generating tool call.")
