TOOLS = [
    {
        "name": "query_students",
        "description": "Find students based on GPA or name",
        "parameters": {
            "min_gpa": "number",
            "max_gpa": "number",
            "student_name": "string"
        }
    },
    {
        "name": "query_courses",
        "description": "Find course records",
        "parameters": {
            "course_name": "string",
            "semester": "string",
            "grade_below": "string"
        }
    },
    {
        "name": "get_transcript",
        "description": "Get full transcript for a student",
        "parameters": {
            "student_id": "string"
        }
    }
]