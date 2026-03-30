from mcp_schema import get_tool_names, get_tool_schema


def validate_tool_call(tool_call: dict) -> None:
    if "tool" not in tool_call:
        raise ValueError("Missing tool field")

    if "arguments" not in tool_call:
        raise ValueError("Missing arguments")

    if not isinstance(tool_call["arguments"], dict):
        raise ValueError("Arguments must be a dictionary")

    tool_name = tool_call["tool"]

    if tool_name not in get_tool_names():
        raise ValueError(f"Invalid tool: {tool_name}")

    schema = get_tool_schema(tool_name)
    allowed_args = set(schema["parameters"].keys())
    provided_args = set(tool_call["arguments"].keys())

    invalid_args = provided_args - allowed_args
    if invalid_args:
        raise ValueError(
            f"Invalid argument(s) for {tool_name}: {', '.join(sorted(invalid_args))}"
        )

    missing_args = allowed_args - provided_args
    if missing_args:
        raise ValueError(
            f"Missing required argument(s) for {tool_name}: {', '.join(sorted(missing_args))}"
        )
