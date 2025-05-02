import yfinance as yf
from collections import defaultdict
from locale import setlocale, format_string, LC_NUMERIC
setlocale(LC_NUMERIC, 'pt_BR.UTF-8')
import numpy as np
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calcular_rsi(dados, periodos=14):
    try:
        delta = dados['Close'].diff()
        if delta.dropna().empty or len(delta.dropna()) < periodos:
            logger.warning("Dados insuficientes para calcular RSI")
            return 0
        
        ganho = delta.where(delta > 0, 0)
        perda = -delta.where(delta < 0, 0)
        
        media_ganho = ganho.rolling(window=periodos).mean()
        media_perda = perda.rolling(window=periodos).mean()
        
        if media_perda.iloc[-1] == 0:
            logger.warning("Média de perda é zero, RSI indefinido")
            return 100 if media_ganho.iloc[-1] > 0 else 0
        
        rs = media_ganho / media_perda
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.empty else 0
    except Exception as e:
        logger.error(f"Erro ao calcular RSI: {str(e)}")
        return 0

def formatar_volume(numero):
    """Formata o volume para formato legível (ex: 1.5M, 150K)."""
    if numero >= 1_000_000:
        return f"{numero/1_000_000:.1f}M".replace(".", ",")
    elif numero >= 1_000:
        return f"{numero/1_000:.1f}K".replace(".", ",")
    else:
        return f"{numero:,.0f}".replace(",", ".")

def buscar_variacao_ibov():
    ticker_ibov = "^BVSP"
    dados_ibov = yf.Ticker(ticker_ibov)
    info_ibov = dados_ibov.history(period="1d", interval="1d")  # Dados diários para IBOV

    if info_ibov.empty:
        logger.warning("Dados do IBOV não encontrados")
        return {
            "indice": "IBOV",
            "valor_atual": format_string('%.2f', ultimo_valor, grouping=True),
            "variacao": f"{variacao:+.2f}%",
            "volatilidade": volatilidade_formatada,
            "acoes_maior_peso": acoes_maior_peso,
            "setor_em_alta": setor_em_alta,
            "setor_em_baixa": setor_em_baixa
        }

    ultimo_valor = info_ibov["Close"].iloc[-1]
    abertura = info_ibov["Open"].iloc[0]
    variacao = ((ultimo_valor - abertura) / abertura) * 100

    acoes = [
        {"ticker": "PETR4.SA", "nome": "Petrobras", "setor": "Energia", "peso_ibov": 8.2},
        {"ticker": "VALE3.SA", "nome": "Vale", "setor": "Mineração", "peso_ibov": 7.1},
        {"ticker": "ITUB4.SA", "nome": "Itaú", "setor": "Financeiro", "peso_ibov": 6.8},
        {"ticker": "BBDC4.SA", "nome": "Bradesco", "setor": "Financeiro", "peso_ibov": 3.5},
        {"ticker": "BBAS3.SA", "nome": "Banco do Brasil", "setor": "Financeiro", "peso_ibov": 2.9},
        {"ticker": "B3SA3.SA", "nome": "B3", "setor": "Financeiro", "peso_ibov": 2.7},
        {"ticker": "ABEV3.SA", "nome": "Ambev", "setor": "Consumo", "peso_ibov": 2.1},
    ]

    acoes_maior_peso = []
    for acao in acoes:
        try:
            logger.info(f"Processando ação {acao['ticker']}")
            ticker = yf.Ticker(acao["ticker"])
            dados_5min = ticker.history(period="1d", interval="5m")
            dados_historicos = ticker.history(period="5d", interval="1h")

            if dados_5min.empty:
                logger.warning(f"Dados intradiários vazios para {acao['ticker']}")
                suporte = resistencia = rsi = variacao_acao = 0
                preco = "R$ 0,00"
            else:
                logger.info(f"Dados intradiários disponíveis para {acao['ticker']}: {len(dados_5min)} pontos")
                suporte = dados_5min['Low'].min()
                resistencia = dados_5min['High'].max()
                rsi = calcular_rsi(dados_5min, periodos=5) if len(dados_5min) >= 5 else 0  # Reduzido para 5
                variacao_acao = ((dados_5min['Close'].iloc[-1] - dados_5min['Open'].iloc[0]) / dados_5min['Open'].iloc[0]) * 100
                preco = f"R$ {dados_5min['Close'].iloc[-1]:.2f}".replace(".", ",")

            volume_medio = dados_historicos["Volume"].mean() if not dados_historicos.empty else 0
            volume_atual = dados_5min["Volume"].sum() if not dados_5min.empty else 0

            volume_status = (
                f"{formatar_volume(volume_atual)} ({((volume_atual - volume_medio)/volume_medio)*100:+.0f}% vs média)"
                if volume_medio > 0 else f"{formatar_volume(volume_atual)} (sem média)"
            )

            acoes_maior_peso.append({
                "ticker": acao["ticker"].replace(".SA", ""),
                "nome": acao["nome"],
                "setor": acao["setor"],
                "preco": preco,
                "variacao": f"{variacao_acao:+.1f}%",
                "volume": volume_status,
                "peso_ibov": acao["peso_ibov"],
                "suporte": f"R$ {suporte:.2f}".replace(".", ",") if suporte else "R$ 0,00",
                "resistencia": f"R$ {resistencia:.2f}".replace(".", ",") if resistencia else "R$ 0,00",
                "rsi": f"{rsi:.1f}"
            })

        except Exception as e:
            logger.error(f"Erro ao processar {acao['ticker']}: {str(e)}")
            acoes_maior_peso.append({
                "ticker": acao["ticker"].replace(".SA", ""),
                "nome": acao["nome"],
                "setor": acao["setor"],
                "preco": "R$ 0,00",
                "variacao": "0.0%",
                "volume": "0 (sem média)",
                "peso_ibov": acao["peso_ibov"],
                "suporte": "R$ 0,00",
                "resistencia": "R$ 0,00",
                "rsi": "0.0"
            })

    # Agrupa variações por setor
    setor_variacoes = defaultdict(list)
    for acao in acoes_maior_peso:
        try:
            variacao = float(acao["variacao"].replace("%", "").replace("+", "").replace(",", "."))
            if "-" in acao["variacao"]:
                variacao = -abs(variacao)
            setor_variacoes[acao["setor"]].append(variacao)
        except:
            continue

    # Calcula média de cada setor
    setor_medias = {
        setor: sum(varios)/len(varios) for setor, varios in setor_variacoes.items() if varios
    }

    setor_em_alta = max(setor_medias, key=setor_medias.get, default="―")
    setor_em_baixa = min(setor_medias, key=setor_medias.get, default="―")

    # Cálculo da Volatilidade
    dados_ibov_intraday = dados_ibov.history(period="1d", interval="5m")  # Dados de 5 minutos
    retornos = dados_ibov_intraday["Close"].pct_change().dropna()
    volatilidade = np.std(retornos) * 100 if not retornos.empty else 0
    volatilidade_formatada = f"{volatilidade:.2f}%"

    return {
        "indice": "IBOV",
        "valor_atual": format_string('%.2f', ultimo_valor, grouping=True),  # 👈 ADICIONADO
        "variacao": f"{variacao:+.2f}%",
        "volatilidade": volatilidade_formatada,
        "acoes_maior_peso": acoes_maior_peso,
        "setor_em_alta": setor_em_alta,
        "setor_em_baixa": setor_em_baixa
    }

def inferir_tendencia_win(variacao_ibov, acoes):
    impacto_total = 0.0
    rsi_medio = 0.0
    volume_acumulado = 0
    acoes_validas = 0

    for acao in acoes:
        try:
            variacao = float(acao["variacao"].replace('%', '').replace('+', '').replace(',', '.'))
            if "-" in acao["variacao"]:
                variacao *= -1
            
            impacto_total += variacao * acao["peso_ibov"] / 100
            rsi_medio += float(acao["rsi"])
            volume_str = acao["volume"].split(" ")[0].replace(",", "").replace(".", "")
            volume_acumulado += int(volume_str) if volume_str.isdigit() else 0
            acoes_validas += 1
        except Exception as e:
            logger.warning(f"Erro ao processar ação {acao['ticker']} em inferir_tendencia_win: {str(e)}")
            continue
    
    rsi_medio = rsi_medio / acoes_validas if acoes_validas > 0 else 0
    
    logger.info(f"Tendência calculada: impacto_total={impacto_total:.2f}, rsi_medio={rsi_medio:.2f}")
    
    if impacto_total > 0.5 and rsi_medio < 70:
        return "alta"
    elif impacto_total < -0.5 and rsi_medio > 30:
        return "baixa"
    else:
        return "lateral"

def obter_dados_win(interval="5m"):
    try:
        win = yf.Ticker("EWZ")
        dados = win.history(period="1d", interval=interval)
        
        if dados.empty:
            return {"tendencia": "não disponível", "volume": "não disponível"}
        
        volume_total = dados['Volume'].sum()
        if volume_total > 0:
            vwap = (dados['Close'] * dados['Volume']).sum() / volume_total
        else:
            vwap = 0
        
        return {
            "tendencia": "alta" if dados['Close'].iloc[-1] > vwap else "baixa",
            "vwap": f"R$ {vwap:.2f}".replace(".", ","),
            "volume": formatar_volume(dados['Volume'].iloc[-1])
        }
    except Exception as e:
        return {"tendencia": "erro", "volume": "erro", "detalhes": str(e)}