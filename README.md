# 📈 ibov-service

Microserviço em Python com Flask para fornecer dados e análises automatizadas do IBOVESPA e do Mini Índice (WIN$), com suporte a inteligência artificial via OpenRouter.

---

## 🚀 Funcionalidades

- 🔎 **/api/ibov** – Retorna dados do IBOV (Yahoo Finance)
- 📊 **/api/market/win** – Fornece dados do Mini Índice (WIN1!) com intervalo personalizável
- 🧠 **/api/market/analise** – Gera uma análise estratégica com IA baseada em dados reais de mercado

---

## 🧱 Estrutura

```
ibov-service/
│
├── main.py              # Inicializa o servidor Flask
├── routes.py            # Define as rotas da API
├── service.py           # Lógica de negócio (coleta de dados, análise etc)
├── requirements.txt     # Dependências do projeto
├── .env                 # Variáveis sensíveis (não subir no Git)
└── .gitignore           # Ignora venv, .env e arquivos desnecessários
```

## 📁 Integração

Este microserviço é integrado a um backend Node.js que atua como proxy entre o frontend da plataforma Future Trade e este serviço Python.
