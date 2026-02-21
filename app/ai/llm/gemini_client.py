import os
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.constants import GEMINI_MODEL

class GeminiClient:
    def __init__(self, model_name: str = GEMINI_MODEL):
        api_key = os.getenv("GOOGLE_API_KEY") # We should use GOOGLE_API_KEY or typical env
        self.llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)

    def get_llm(self):
        return self.llm

gemini_client = GeminiClient()
