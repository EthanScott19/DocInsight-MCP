# parser.py

def extract_json(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}") + 1
    return text[start:end]