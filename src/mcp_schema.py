from typing import Dict, List, Any


TOOLS: List[Dict[str, Any]] = [
    {
        "name": "get_all_applications",
        "description": "Return a list of all applications",
        "parameters": {}
    },
    {
        "name": "count_all_applications",
        "description": "Return the total number of applications",
        "parameters": {}
    },
    {
        "name": "get_application_by_id",
        "description": "Get full application details for a specific application ID",
        "parameters": {
            "app_id": "number"
        }
    },
    {
        "name": "get_applications_by_degree",
        "description": "Find applications by degree code",
        "parameters": {
            "degree_code": "string"
        }
    },
    {
        "name": "count_applications_by_degree",
        "description": "Count applications by degree code",
        "parameters": {
            "degree_code": "string"
        }
    },
    {
        "name": "get_applications_by_admission_note",
        "description": "Find applications by admission note",
        "parameters": {
            "admission_note": "string"
        }
    },
    {
        "name": "count_applications_by_admission_note",
        "description": "Count applications by admission note",
        "parameters": {
            "admission_note": "string"
        }
    },
    {
        "name": "filter_applications",
        "description": "Filter applications using one or more optional criteria",
        "parameters": {
            "degree_code": "string",
            "admission_note": "string",
            "min_gpa": "number",
            "max_gpa": "number",
            "student_type": "string",
            "term": "string"
        }
    },
    {
        "name": "get_missing_items_for_application",
        "description": "Get missing items for an application",
        "parameters": {
            "app_id": "number"
        }
    },
    {
        "name": "get_documents_for_application",
        "description": "Get documents for an application",
        "parameters": {
            "app_id": "number"
        }
    },
    {
        "name": "count_filtered_applications",
        "description": "Count applications using one or more optional criteria",
        "parameters": {
            "degree_code": "string",
            "admission_note": "string",
            "min_gpa": "number",
            "max_gpa": "number",
            "student_type": "string",
            "term": "string"
        }
    },
]


REQUIRED_ARGUMENTS: Dict[str, List[str]] = {
    "get_all_applications": [],
    "count_all_applications": [],
    "get_application_by_id": ["app_id"],
    "get_applications_by_degree": ["degree_code"],
    "count_applications_by_degree": ["degree_code"],
    "get_applications_by_admission_note": ["admission_note"],
    "count_applications_by_admission_note": ["admission_note"],
    "filter_applications": [],
    "get_missing_items_for_application": ["app_id"],
    "get_documents_for_application": ["app_id"],
    "count_filtered_applications": [],
}


def get_tool_names() -> List[str]:
    return [tool["name"] for tool in TOOLS]


def get_tool_schema(tool_name: str) -> Dict[str, Any]:
    for tool in TOOLS:
        if tool["name"] == tool_name:
            return tool
    raise ValueError(f"Unknown tool: {tool_name}")


def get_required_arguments(tool_name: str) -> List[str]:
    if tool_name not in REQUIRED_ARGUMENTS:
        raise ValueError(f"Unknown tool: {tool_name}")
    return REQUIRED_ARGUMENTS[tool_name]