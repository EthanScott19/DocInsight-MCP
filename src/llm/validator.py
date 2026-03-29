# validator.py

from tools import TOOLS


def validate_tool_call(tool_call: dict):
    if "tool" not in tool_call:
        raise ValueError("Missing tool field")

    if "arguments" not in tool_call:
        raise ValueError("Missing arguments")

    if not isinstance(tool_call["arguments"], dict):
        raise ValueError("Arguments must be a dictionary")

    tool_names = [t["name"] for t in TOOLS]

    if tool_call["tool"] not in tool_names:
        raise ValueError(f"Invalid tool: {tool_call['tool']}")

    schema = next(t for t in TOOLS if t["name"] == tool_call["tool"])

    for arg in tool_call["arguments"]:
        if arg not in schema["parameters"]:
            raise ValueError(f"Invalid argument: {arg}")