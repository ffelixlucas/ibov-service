import os
from dotenv import load_dotenv
from openai import OpenAI
from app.config import Config

# Carrega as variáveis de ambiente do .env
load_dotenv()


api_key = os.getenv("OPENROUTER_API_KEY")
base_url = os.getenv("OPENROUTER_BASE_URL")
referer = os.getenv("OPENROUTER_REFERER", "http://localhost")

# Verifica se a API Key está disponível
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY não foi encontrada. Verifique seu .env")

# Cria o client do OpenAI/OpenRouter
client = OpenAI(
    base_url=base_url,
    api_key=api_key
    print(f"🔐 API_KEY em uso: {api_key}")

)

def gerar_analise_openrouter(prompt):
    try:
        completion = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",
            messages=[{"role": "user", "content": prompt}],
            extra_headers={
                "HTTP-Referer": referer,
                "X-Title": "RadarFinanceiroFutureTrade"
            }
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Erro na OpenRouter: {e}"
