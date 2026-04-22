from typing import Any, Dict
import sqlite3

from mcp_schema import get_tool_names, get_tool_schema, get_required_arguments
from db import (
    get_all_applications,
    count_all_applications,
    get_application_by_id,
    get_applications_by_degree,
    count_applications_by_degree,
    get_applications_by_admission_note,
    count_applications_by_admission_note,
    filter_applications,
    get_missing_items_for_application,
    get_documents_for_application,
    count_filtered_applications,
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
    required_args = set(get_required_arguments(tool_name))
    provided_args = set(arguments.keys())

    invalid_args = provided_args - allowed_args
    if invalid_args:
        raise ValueError(
            f"Invalid arguments for {tool_name}: {', '.join(sorted(invalid_args))}"
        )

    missing_args = required_args - provided_args
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

    if tool_name == "count_all_applications":
        return {"count": count_all_applications(conn)}

    if tool_name == "get_application_by_id":
        return get_application_by_id(conn, args["app_id"])

    if tool_name == "get_applications_by_degree":
        return get_applications_by_degree(conn, args["degree_code"])

    if tool_name == "count_applications_by_degree":
        return {
            "degree_code": args["degree_code"],
            "count": count_applications_by_degree(conn, args["degree_code"])
        }

    if tool_name == "get_applications_by_admission_note":
        return get_applications_by_admission_note(conn, args["admission_note"])

    if tool_name == "count_applications_by_admission_note":
        return {
            "admission_note": args["admission_note"],
            "count": count_applications_by_admission_note(conn, args["admission_note"])
        }

    if tool_name == "filter_applications":
        return filter_applications(
            conn,
            degree_code=args.get("degree_code"),
            admission_note=args.get("admission_note"),
            min_gpa=args.get("min_gpa"),
            max_gpa=args.get("max_gpa"),
            student_type=args.get("student_type"),
            term=args.get("term"),
        )

    if tool_name == "get_missing_items_for_application":
        return get_missing_items_for_application(conn, args["app_id"])

    if tool_name == "get_documents_for_application":
        return get_documents_for_application(conn, args["app_id"])
    if tool_name == "count_filtered_applications":
        return {
            "count": count_filtered_applications(
                conn,
                degree_code=args.get("degree_code"),
                admission_note=args.get("admission_note"),
                min_gpa=args.get("min_gpa"),
                max_gpa=args.get("max_gpa"),
                student_type=args.get("student_type"),
                term=args.get("term"),
            )
        }

    raise ValueError(f"Unhandled tool: {tool_name}")