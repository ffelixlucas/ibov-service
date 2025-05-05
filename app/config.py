import os

class Config:
    PORT = int(os.getenv("PORT", 8000))
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL")
    HTTP_REFERER = os.getenv("HTTP_REFERER", "http://localhost:8000")