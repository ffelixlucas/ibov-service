import os
import httpx
from dotenv import load_dotenv
from app.config import Config

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("BASE_URL")
referer = os.getenv("REFERER", "http://localhost")




def gerar_analise_openai(prompt):
    try:
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": referer,
                "X-Title": "RadarFinanceiroFutureTrade"
            },
            json={
                "model": "mistralai/mistral-7b-instruct:free",  # ⬅️ importante manter o :free
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            },
            timeout=30.0
        )
        if response.status_code != 200:
            raise Exception(response.text)

        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Erro na OpenRouter: {str(e)}"
