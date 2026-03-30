from mcp_schema import TOOLS


def build_prompt(user_input: str) -> str:
    tool_descriptions = []

    for tool in TOOLS:
        params = ", ".join([f"{k}: {v}" for k, v in tool["parameters"].items()])
        if not params:
            params = "no arguments"

        tool_descriptions.append(
            f'- {tool["name"]}: {tool["description"]} | parameters: {params}'
        )

    formatted_tools = "\n".join(tool_descriptions)

    return f"""
You are an AI that converts a user question into exactly one structured tool call.

You MUST:
- Return only valid JSON
- Never generate SQL
- Never explain anything
- Use exactly one tool
- Use only the tools and parameters listed below
- Do not invent tools or arguments
- Omit arguments that are not needed

Output format:
{{
  "tool": "<tool_name>",
  "arguments": {{ ... }}
}}

Available tools:
{formatted_tools}

Examples:
User request: "Show all applications"
Output:
{{"tool": "get_all_applications", "arguments": {{}}}}

User request: "Find application 101"
Output:
{{"tool": "get_application_by_id", "arguments": {{"app_id": 101}}}}

User request: "Show CSC applications"
Output:
{{"tool": "get_applications_by_degree", "arguments": {{"degree_code": "CSC"}}}}

User request: "Show provisional admissions"
Output:
{{"tool": "get_applications_by_admission_note", "arguments": {{"admission_note": "Provisional Admission"}}}}

User request: "Show missing items for application 101"
Output:
{{"tool": "get_missing_items_for_application", "arguments": {{"app_id": 101}}}}

User request: "Show documents for application 101"
Output:
{{"tool": "get_documents_for_application", "arguments": {{"app_id": 101}}}}

User request: "{user_input}"
"""
