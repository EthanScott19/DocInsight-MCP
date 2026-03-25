#llm code, using Cohere Command A
import cohere
import os

class LLMClient:
    def __init__(self):
        
      #Must set client key before hand, showing in requirements doc
      
      self.client = cohere.Client(os.getenv("COHERE_API_KEY"))

    def generate(self, prompt):
        response = self.client.generate(
            model="command-a",
            prompt=prompt,
            max_tokens=200,
            temperature=0
        )
        return response.generations[0].text.strip()
