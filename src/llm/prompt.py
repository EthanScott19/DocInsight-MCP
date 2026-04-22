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
You convert a user question into EXACTLY ONE valid JSON tool call.

STRICT RULES:
- Return ONLY raw JSON
- Do NOT use markdown fences
- Do NOT explain
- Do NOT apologize
- Do NOT mention unavailable tools
- Do NOT output any text before or after the JSON
- Use exactly one tool
- Use only the listed tools and parameters
- Never invent tools or arguments

Admission note mappings:
- "accepted", "fully accepted", "accepted unprovisionally", "unconditional admission", "unprovisionally accepted" -> "Full Admission"
- "conditionally accepted", "conditional admission", "provisional", "provisionally accepted" -> "Provisional Admission"
- "denied", "rejected", "not admitted" -> "Denied Admission"

Degree mappings:
- "computer science", "cs", "csc" -> "CSC"
- "biology", "bio" -> "BIO"
- "mathematics", "math", "mth" -> "MTH"

Count intent:
- If the user asks "how many", "count", "number of", or "total" and the question includes filters such as GPA, degree, term, student type, or admission note, use count_filtered_applications.

Filtering:
- Use filter_applications when the user combines multiple filters, such as degree + admission note, degree + GPA, or term + student type.
- Use filter_applications when the user asks for applications above or below a GPA threshold.
- filter_applications may include any subset of these optional arguments:
  degree_code, admission_note, min_gpa, max_gpa, student_type, term

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

User request: "How many applicants are there?"
Output:
{{"tool": "count_all_applications", "arguments": {{}}}}

User request: "How many BIO applicants are there?"
Output:
{{"tool": "count_applications_by_degree", "arguments": {{"degree_code": "BIO"}}}}

User request: "How many students were denied admission?"
Output:
{{"tool": "count_applications_by_admission_note", "arguments": {{"admission_note": "Denied Admission"}}}}

User request: "Show all full admissions"
Output:
{{"tool": "get_applications_by_admission_note", "arguments": {{"admission_note": "Full Admission"}}}}

User request: "Show CSC applicants above 3.5 GPA"
Output:
{{"tool": "filter_applications", "arguments": {{"degree_code": "CSC", "min_gpa": 3.5}}}}

User request: "Show provisional BIO applications for Fall 2025"
Output:
{{"tool": "filter_applications", "arguments": {{"degree_code": "BIO", "admission_note": "Provisional Admission", "term": "Fall 2025"}}}}

User request: "Show documents for application 101"
Output:
{{"tool": "get_documents_for_application", "arguments": {{"app_id": 101}}}}

User request: "Show missing items for application 101"
Output:
{{"tool": "get_missing_items_for_application", "arguments": {{"app_id": 101}}}}

User request: "How many applicants had at least a 3.2 GPA?"
Output:
{{"tool": "count_filtered_applications", "arguments": {{"min_gpa": 3.2}}}}

User request: "How many BIO applicants had at least a 3.5 GPA?"
Output:
{{"tool": "count_filtered_applications", "arguments": {{"degree_code": "BIO", "min_gpa": 3.5}}}}

User request: "How many provisional CSC applications are there for Fall 2025?"
Output:
{{"tool": "count_filtered_applications", "arguments": {{"degree_code": "CSC", "admission_note": "Provisional Admission", "term": "Fall 2025"}}}}
User request: "{user_input}"
"""