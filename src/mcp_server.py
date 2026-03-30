from typing import Any, Dict
import sqlite3

from mcp_schema import get_tool_names, get_tool_schema
from db import (
    get_all_applications,
    get_application_by_id,
    get_applications_by_degree,
    get_applications_by_admission_note,
    get_missing_items_for_application,
    get_documents_for_application,
)


def validate_tool_call(tool_call: Dict[str, Any]) -> None:
    if "tool" not in tool_call:
        raise ValueError("Missing tool field.")

    if "arguments" not in tool_call:
        raise ValueError("Missing arguments field.")

    tool_name = tool_call["tool"]
    arguments = tool_call["arguments"]

    if tool_name not in get_tool_names():
        raise ValueError(f"Invalid tool: {tool_name}")

    if not isinstance(arguments, dict):
        raise ValueError("Arguments must be a dictionary.")

    schema = get_tool_schema(tool_name)
    allowed_args = set(schema["parameters"].keys())
    provided_args = set(arguments.keys())

    invalid_args = provided_args - allowed_args
    if invalid_args:
        raise ValueError(
            f"Invalid arguments for {tool_name}: {', '.join(sorted(invalid_args))}"
        )

    missing_args = allowed_args - provided_args
    if missing_args:
        raise ValueError(
            f"Missing required arguments for {tool_name}: {', '.join(sorted(missing_args))}"
        )


def execute_query(conn: sqlite3.Connection, tool_call: Dict[str, Any]):
    validate_tool_call(tool_call)

    tool_name = tool_call["tool"]
    args = tool_call["arguments"]

    if tool_name == "get_all_applications":
        return get_all_applications(conn)

    if tool_name == "get_application_by_id":
        return get_application_by_id(conn, args["app_id"])

    if tool_name == "get_applications_by_degree":
        return get_applications_by_degree(conn, args["degree_code"])

    if tool_name == "get_applications_by_admission_note":
        return get_applications_by_admission_note(conn, args["admission_note"])

    if tool_name == "get_missing_items_for_application":
        return get_missing_items_for_application(conn, args["app_id"])

    if tool_name == "get_documents_for_application":
        return get_documents_for_application(conn, args["app_id"])

    raise ValueError(f"Unhandled tool: {tool_name}")
