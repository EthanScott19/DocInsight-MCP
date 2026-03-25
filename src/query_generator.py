from llm_client import LLMClient

class QueryGenerator:
    def __init__(self, schema):
        self.llm = LLMClient()
        self.schema = schema

    def build_prompt(self, user_query):
        return f"""
You are an AI that converts natural language into SQL queries.

DATABASE SCHEMA:
{self.schema}

RULES:
- Only return SQL
- No explanations
- Only SELECT statements
- Use only provided tables/columns

USER QUERY:
{user_query}

SQL:
"""

    def generate_sql(self, user_query):
        prompt = self.build_prompt(user_query)
        return self.llm.generate(prompt)
