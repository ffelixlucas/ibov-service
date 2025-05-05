# Crie um novo arquivo test_api.py
from app.ai_service import gerar_analise_openai

test_prompt = "Responda apenas com 'Conexão OK' se estiver funcionando"
print(gerar_analise_openai(test_prompt))