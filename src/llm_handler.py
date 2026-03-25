from query_generator import QueryGenerator
from query_validator import QueryValidator

class LLMHandler:
    def __init__(self, schema):
        self.generator = QueryGenerator(schema)

    def process_query(self, user_query):
        sql = self.generator.generate_sql(user_query)

        if not QueryValidator.is_safe(sql):
            return {"error": "Unsafe query detected."}

        if not QueryValidator.is_select(sql):
            return {"error": "Only SELECT queries allowed."}

        return {"sql": sql}
