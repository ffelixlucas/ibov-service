from flask import Blueprint, jsonify, request
from app.service import buscar_variacao_ibov, obter_dados_win, buscar_indices_globais
from app.ai_service import gerar_analise_openai
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

market_bp = Blueprint("market", __name__)

@market_bp.route("/api/market/indices", methods=["GET"])
def rota_indices():
    try:
        dados = buscar_indices_globais()
        return jsonify(dados)
    except Exception as e:
        logger.error(f"Erro em /indices: {str(e)}")
        return jsonify({"erro": "Falha ao buscar índices globais"}), 500


@market_bp.route("/api/market/ibov", methods=["GET"])
def rota_ibov():
    try:
        dados = buscar_variacao_ibov()
        if not dados or not dados.get("acoes_maior_peso"):
            logger.warning("Dados do IBOV incompletos ou vazios")
            return jsonify({"erro": "Sem dados válidos do IBOV"}), 404
        return jsonify(dados)
    except Exception as e:
        logger.error(f"Erro na rota /ibov: {str(e)}")
        return jsonify({"erro": "Falha ao buscar dados do IBOV"}), 500

@market_bp.route("/api/market/win", methods=["GET"])
def rota_win():
    try:
        intervalo = request.args.get("interval", "15m")
        intervalos_validos = ["1m", "5m", "15m", "30m", "1h"]
        if intervalo not in intervalos_validos:
            return jsonify({"erro": f"Intervalo inválido. Use: {', '.join(intervalos_validos)}"}), 400
        
        dados = obter_dados_win(intervalo)
        if dados.get("tendencia") in ["erro", "não disponível"]:
            logger.warning(f"Dados do WIN indisponíveis para intervalo {intervalo}")
            return jsonify({"erro": "Sem dados válidos do WIN"}), 404
        
        return jsonify(dados)
    except Exception as e:
        logger.error(f"Erro na rota /win: {str(e)}")
        return jsonify({"erro": "Falha ao buscar dados do WIN"}), 500

@market_bp.route("/api/market/analise", methods=["POST"])
def gerar_analise():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Nenhum dado fornecido"}), 400
        
        campos_obrigatorios = ["variacao", "valor_atual", "volatilidade", "acoes_maior_peso", "setor_em_alta", "setor_em_baixa"]
        if not all(campo in dados for campo in campos_obrigatorios):
            logger.warning(f"Campos obrigatórios faltando: {campos_obrigatorios}")
            return jsonify({"erro": "Dados incompletos. Campos obrigatórios faltando."}), 400

        volatilidade = dados.get("volatilidade", "não disponível")
        ibov = dados.get("variacao", "0,00%")
        valor = dados.get("valor_atual", "0")
        acoes = dados.get("acoes_maior_peso", [])
        setor_alta = dados.get("setor_em_alta", "―")
        setor_baixa = dados.get("setor_em_baixa", "―")

        win_data = obter_dados_win("15m")
        tendencia = win_data.get("tendencia", "indefinida")
        volume_win = win_data.get("volume", "volume não disponível")
        if tendencia == "não disponível":
            tendencia = "sem tendência clara"

        impulsoras = '\n'.join([
            f'  → {a["ticker"]} ({a["setor"]}): {a["variacao"]} | Peso: {a.get("peso_ibov", 0)}% | Volume: {a["volume"]}'
            for a in acoes
            if '+' in a["variacao"] and float(a["variacao"].replace('%', '').replace(',', '.')) > 0.1
        ]) or 'Nenhuma ação com variação positiva significativa'

        penalizadoras = '\n'.join([
            f'  → {a["ticker"]} ({a["setor"]}): {a["variacao"]} | Peso: {a.get("peso_ibov", 0)}% | Volume: {a["volume"]}'
            for a in acoes
            if '-' in a["variacao"] and float(a["variacao"].replace('%', '').replace(',', '.')) < -0.1
        ]) or 'Nenhuma ação com variação negativa significativa'

        prompt = f"""
Você é um analista técnico da Future Trade. Analise o mercado usando esta estrutura:

**Comportamento do IBOV**
- Variação: {ibov} | Valor Atual: R$ {valor}
- Volatilidade: {volatilidade} (classifique como: baixa se <0.5%, moderada se 0.5-1.5%, alta se >1.5%)
- Relação com WIN$: Tendência {tendencia} | Volume: {volume_win}

**Ações e Setores** (Peso IBOV em destaque)
- Principais impulsoras (variação positiva significativa, >0.1%):
{impulsoras}
- Principais penalizadoras (variação negativa, <-0.1%):
{penalizadoras}

**Contexto Técnico**
- Força do setor {setor_alta} vs fraqueza do setor {setor_baixa}.
- Observações sobre volume: Mencione divergências de volume (ex.: volume acima ou abaixo da média) for ações relevantes.

Use termos técnicos como: rompimento de suporte/resistência, fluxo institucional, divergência de volume.

Exemplo de estilo desejado:
'O IBOV opera em baixa de -0,10%, com volatilidade baixa (0,10%). Nenhuma ação apresenta variação positiva significativa. As principais penalizadoras incluem PETR4 (Energia): -0,4% | Peso: 8,2% | Volume: 5,0M (+29% vs média) e VALE3 (Mineração): -0,2% | Peso: 7,1% | Volume: 1,3M (-20% vs média). O setor Consumo mostra resiliência relativa, enquanto Energia apresenta fraqueza. Observa-se divergência de volume em PETR4, com volume acima da média, indicando maior fluxo institucional.'

Contexto adicional:
- O miniíndice WIN$ replica o IBOV. Ações com maior peso têm mais impacto:
  - PETR4 (8,2%), VALE3 (7,1%), ITUB4 (6,8%)
- Use níveis técnicos de 15 minutos para as observações.
- Mencione volume se disponível ({volume_win}).
- Certifique-se de que a variação do IBOV ({ibov}) seja refletida corretamente (positiva ou negativa).
- Evite recomendar ações com variação próxima de 0% como impulsoras.
- Não inclua recomendações de compra ou venda, apenas descreva o comportamento do mercado.
"""

        analise = gerar_analise_openai(prompt.strip())
        return jsonify({"analise": analise})
    except Exception as e:
        logger.error(f"Erro ao gerar análise: {str(e)}")
        return jsonify({"erro": "Falha ao gerar análise"}), 500