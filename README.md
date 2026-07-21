# ibov-service

Microserviço em Python com Flask para fornecer dados e análises automatizadas do IBOVESPA e do Mini Índice (WIN$), com suporte a inteligência artificial via OpenRouter.

## Funcionalidades

- `GET /api/ibov`: retorna dados do IBOV via Yahoo Finance
- `GET /api/market/win`: fornece dados do Mini Índice com intervalo configurável
- `POST /api/market/analise`: gera análise estratégica com IA baseada em dados de mercado

## Stack

- Python
- Flask
- yfinance
- pandas
- OpenAI SDK/OpenRouter
- python-dotenv

## Estrutura

```text
.
├── app/              # Rotas e regra de negocio
├── requirements.txt  # Dependencias Python
└── README.md
```

## Como rodar localmente

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

> Configure as variáveis de ambiente localmente. Não versionar `.env`, tokens ou chaves.

## Integração

Este microserviço é integrado a um backend Node.js que atua como proxy entre o frontend da plataforma Future Trade e este serviço Python.

## Status

Microserviço em evolução para consulta e análise automatizada de mercado.
