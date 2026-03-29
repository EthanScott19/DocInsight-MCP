TOOLS = [
    {
        "name": "query_applicants",
        "description": "Find applicants based on GPA, name, or status",
        "parameters": {
            "min_gpa": "number",
            "max_gpa": "number",
            "applicant_name": "string",
            "admissions_status": "string"
        }
    },
    {
        "name": "get_application_details",
        "description": "Get full application details for a user",
        "parameters": {
            "user_id": "number"
        }
    },
    {
        "name": "check_missing_items",
        "description": "Find applications with missing required items",
        "parameters": {
            "app_id": "number"
        }
    },
    {
        "name": "query_documents",
        "description": "Check document submission status",
        "parameters": {
            "app_id": "number",
            "status": "string"
        }
    }
]