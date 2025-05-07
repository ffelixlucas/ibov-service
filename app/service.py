import yfinance as yf
from collections import defaultdict
from locale import setlocale, format_string, LC_NUMERIC
import locale
try:
    locale.setlocale(locale.LC_NUMERIC, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_NUMERIC, 'C')  # fallback universal
import numpy as np
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from datetime import datetime, timedelta
CACHE_DADOS = {}
CACHE_TTL = timedelta(minutes=3)


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
    agora = datetime.now()

    # Verifica se o índice IBOV está no cache
    if ticker_ibov in CACHE_DADOS and agora - CACHE_DADOS[ticker_ibov]["timestamp"] < CACHE_TTL:
        logger.info("Usando cache para IBOV")
        dados_ibov = CACHE_DADOS[ticker_ibov]["ticker"]
    else:
        logger.info("Consultando yfinance para IBOV")
        dados_ibov = yf.Ticker(ticker_ibov)
        CACHE_DADOS[ticker_ibov] = {
            "ticker": dados_ibov,
            "timestamp": agora
        }

    try:
        info_ibov = dados_ibov.history(period="1d", interval="1d")
        logger.info(f"info_ibov retornado: {info_ibov}")
    except Exception as e:
        logger.error(f"Erro ao buscar histórico do IBOV: {str(e)}")
        return {
            "erro": "Falha ao consultar histórico do IBOV"
        }

    if info_ibov.empty:
        logger.warning("Dados do IBOV não encontrados")
        return {
            "erro": "Falha ao buscar dados do IBOV"
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
            ticker_symbol = acao["ticker"]
            agora = datetime.now()

            # Verifica se já temos cache e se ainda está válido
            if ticker_symbol in CACHE_DADOS and agora - CACHE_DADOS[ticker_symbol]["timestamp"] < CACHE_TTL:
                logger.info(f"Usando cache para {ticker_symbol}")
                dados_5min = CACHE_DADOS[ticker_symbol]["dados_5min"]
                dados_historicos = CACHE_DADOS[ticker_symbol]["dados_historicos"]
            else:
                logger.info(f"Consultando yfinance para {ticker_symbol}")
                ticker = yf.Ticker(ticker_symbol)
                dados_5min = ticker.history(period="1d", interval="5m")
                dados_historicos = ticker.history(period="5d", interval="1h")

                # Salva no cache
                CACHE_DADOS[ticker_symbol] = {
                    "dados_5min": dados_5min,
                    "dados_historicos": dados_historicos,
                    "timestamp": agora
                }

            if dados_5min.empty:
                logger.warning(f"Dados intradiários vazios para {acao['ticker']}")
                suporte = resistencia = rsi = variacao_acao = 0
                preco = "R$ 0,00"
            else:
                logger.info(f"Dados intradiários disponíveis para {acao['ticker']}: {len(dados_5min)} pontos")
                suporte = dados_5min['Low'].min()
                resistencia = dados_5min['High'].max()
                rsi = calcular_rsi(dados_5min, periodos=5) if len(dados_5min) >= 5 else 0
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
    
def buscar_indices_globais():
    tickers = {
        "IBOVESPA": {"ticker": "^BVSP", "nome": "Ibovespa"},
        "SP500": {"ticker": "^GSPC", "nome": "S&P 500"},
        "DOLAR": {"ticker": "USDBRL=X", "nome": "Dólar Comercial"},
        "NASDAQ": {"ticker": "^IXIC", "nome": "Nasdaq"},
        "EURO": {"ticker": "EURBRL=X", "nome": "Euro"},
        "NIKKEI": {"ticker": "^N225", "nome": "Nikkei 225"}
    }

    resultados = {}

    for chave, dados_ticker in tickers.items():
        simbolo = dados_ticker["ticker"]
        nome_legivel = dados_ticker["nome"]

        try:
            dados = yf.Ticker(simbolo).history(period="1d", interval="1d")
            if dados.empty:
                resultados[chave] = {"erro": "Sem dados disponíveis"}
                continue

            preco_final = dados["Close"].iloc[-1]
            preco_abertura = dados["Open"].iloc[0]
            variacao = ((preco_final - preco_abertura) / preco_abertura) * 100

            resultados[chave] = {
                "nome": nome_legivel,
                "ticker": simbolo,
                "valor_atual": round(preco_final, 2),
                "variacao": f"{variacao:+.2f}%"
            }

        except Exception as e:
            resultados[chave] = {"erro": str(e)}

    return resultados

