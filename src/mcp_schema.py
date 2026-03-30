from typing import Dict, List, Any


TOOLS: List[Dict[str, Any]] = [
    {
        "name": "get_all_applications",
        "description": "Return a list of all applications",
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
        "name": "get_applications_by_admission_note",
        "description": "Find applications by admission note",
        "parameters": {
            "admission_note": "string"
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
    }
]


def get_tool_names() -> List[str]:
    return [tool["name"] for tool in TOOLS]


def get_tool_schema(tool_name: str) -> Dict[str, Any]:
    for tool in TOOLS:
        if tool["name"] == tool_name:
            return tool
    raise ValueError(f"Unknown tool: {tool_name}")
