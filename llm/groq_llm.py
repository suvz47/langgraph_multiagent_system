import os
import requests
from typing import List, Dict
from dotenv import load_dotenv
load_dotenv()

class GroqLLM:
    def __init__(self, model: str = "llama-3.1-8b-instant"):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = model
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def chat(self, messages: List[Dict[str, str]]) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": messages
        }
        response = requests.post(self.api_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"] 