import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import datetime as dt

# -------------------------------
# Configurações
# -------------------------------
tickers = {
    "PTT": "PTT.BK",        # Energia
    "Bangkok Bank": "BBL.BK",   # Financeiro
    "SCC": "SCC.BK",        # Materiais
    "AOT": "AOT.BK",        # Aeroportos
    "CP ALL": "CPALL.BK"    # Varejo
}

start = dt.datetime(2020, 1, 1)
end = dt.datetime(2025, 1, 1)

# -------------------------------
# Função para calcular retorno total com dividendos
# -------------------------------
def total_return_with_dividends(ticker, name):
    stock = yf.Ticker(ticker)

    # Preços ajustados
    prices = stock.history(start=start, end=end, auto_adjust=True)["Close"]

    # Dividendos (corrigindo timezone)
    dividends = stock.dividends.copy()
    dividends.index = dividends.index.tz_localize(None)
    dividends = dividends.loc[start:end]

    # Retorno total = preço + dividendos reinvestidos
    total_return = (
        prices.pct_change().fillna(0)
        + dividends.reindex(prices.index, fill_value=0) / prices.shift(1).fillna(method="bfill")
    ).add(1).cumprod()

    return total_return, prices

# -------------------------------
# Coleta e cálculo
# -------------------------------
results = {}
for name, ticker in tickers.items():
    tr, prices = total_return_with_dividends(ticker, name)
    results[name] = {
        "TotalReturn": tr,
        "Prices": prices
    }

# DataFrame consolidado
df_returns = pd.DataFrame({name: res["TotalReturn"] for name, res in results.items()})

# Cálculo de métricas
metrics = {}
for name, data in results.items():
    prices = data["Prices"]
    tr = data["TotalReturn"]

    cagr = (tr.iloc[-1] / tr.iloc[0]) ** (1 / ((end - start).days / 365)) - 1
    volatility = prices.pct_change().std() * (252 ** 0.5)
    sharpe = cagr / volatility if volatility > 0 else 0

    metrics[name] = {
        "Final Return": round((tr.iloc[-1] - 1) * 100, 2),
        "CAGR": round(cagr * 100, 2),
        "Volatility": round(volatility * 100, 2),
        "Sharpe": round(sharpe, 2),
    }

df_metrics = pd.DataFrame(metrics).T

# -------------------------------
# Gráfico de evolução
# -------------------------------
plt.figure(figsize=(10, 6))
for name in df_returns.columns:
    df_returns[name].plot(label=name)
plt.legend()
plt.title("Retorno Total com Dividendos – Bolsa da Tailândia")
plt.ylabel("Crescimento acumulado (base = 1)")
plt.savefig("retornos_tailandia.png", dpi=300)

# -------------------------------
# Função para gerar relatórios
# -------------------------------
def gerar_relatorio(nome_arquivo, titulo, conclusao, df_metrics):
    doc = SimpleDocTemplate(nome_arquivo, pagesize=A4)
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph(titulo, styles["Title"]))
    elementos.append(Spacer(1, 12))

    # Tabela
    dados = [["Empresa", "Return (%)", "CAGR (%)", "Volatility (%)", "Sharpe"]]
    for idx, row in df_metrics.iterrows():
        dados.append([idx, row["Final Return"], row["CAGR"], row["Volatility"], row["Sharpe"]])

    tabela = Table(dados, hAlign="LEFT")
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.gray),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elementos.append(tabela)
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph(conclusao, styles["Normal"]))
    elementos.append(Spacer(1, 12))

    doc.build(elementos)

# -------------------------------
# Relatório em Português
# -------------------------------
conclusao_pt = """
A análise indica que uma carteira balanceada entre energia, financeiro e infraestrutura tailandesa 
tem potencial de estabilidade com crescimento moderado. 
Empresas como <b>PTT</b> e <b>AOT</b> mostraram solidez no período, com bom balanço entre retorno e risco.
"""
gerar_relatorio("Relatorio_Executivo_Tailandia_PT.pdf", "Relatório Executivo – Bolsa da Tailândia", conclusao_pt, df_metrics)

# -------------------------------
# Relatório em Inglês
# -------------------------------
conclusao_en = """
The analysis indicates that a balanced portfolio between energy, financials, and infrastructure in Thailand 
offers potential for stability with moderate growth. 
Companies such as <b>PTT</b> and <b>AOT</b> showed resilience during the period, with a good balance between return and risk.
"""
gerar_relatorio("Executive_Report_Thailand_EN.pdf", "Executive Report – Thai Stock Market", conclusao_en, df_metrics)

print("✅ Relatórios gerados com sucesso!")

