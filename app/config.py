import os

class Config:
    PORT = int(os.getenv("PORT", 8000))
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL")
    OPENROUTER_REFERER = os.getenv("OPENROUTER_REFERER", "http://localhost")
