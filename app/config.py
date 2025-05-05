import os

class Config:
    PORT = int(os.getenv("PORT", 8000))
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    BASE_URL = os.getenv("BASE_URL")
    REFERER = os.getenv("REFERER", "http://localhost")
