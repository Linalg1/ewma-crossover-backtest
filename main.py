"""
EWMA Crossover Backtest — QQQ(Nasdaq 100 ETF)

Strategie de suivi de tendance :
  - EWMA rapide (span=20) vs EWMA lente (span=50)
  - Long quand la rapide est au-dessus de la lente, sinon cash
  - Le signal est decale d'un jour (.shift(1)) pour eviter le lookahead bias :
    on ne peut agir sur un signal qu'a partir du lendemain de son apparition.

"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('dark_background')

# parametres
TICKER = "QQQ"
PERIOD = "5y"          # historique telecharge
FAST_SPAN = 20
SLOW_SPAN = 50

# telechargement des donnees
data = yf.download(TICKER, period=PERIOD, auto_adjust=True)
df = data[["Close"]].copy()
print(df)
df.columns = ["Close"]  
df = df.dropna()

# calcul des EWMA et du signal
df["ewma_fast"] = df["Close"].ewm(span=FAST_SPAN, adjust=False).mean()
df["ewma_slow"] = df["Close"].ewm(span=SLOW_SPAN, adjust=False).mean()

# signal brut : 1 = tendance up, 0 = tendance down
df["signal"] = (df["ewma_fast"] > df["ewma_slow"]).astype(int)


df["position"] = df["signal"].shift(1).fillna(0)

# rendements et courbes de performance
df["ret"] = df["Close"].pct_change().fillna(0)
df["strategy_ret"] = df["position"] * df["ret"]

df["equity_strategy"] = (1 + df["strategy_ret"]).cumprod()
df["equity_buyhold"] = (1 + df["ret"]).cumprod()

# metriques de performance
def sharpe_ratio(returns, freq=252):
    """Sharpe annualise, taux sans risque suppose nul."""
    if returns.std() == 0:
        return 0.0
    return (returns.mean() / returns.std()) * np.sqrt(freq)

def max_drawdown(equity_curve):
    """Pire baisse depuis un plus haut historique, en %."""
    running_max = equity_curve.cummax()
    drawdown = equity_curve / running_max - 1
    return drawdown.min()

strategy_total_return = df["equity_strategy"].iloc[-1] - 1
buyhold_total_return = df["equity_buyhold"].iloc[-1] - 1

strategy_sharpe = sharpe_ratio(df["strategy_ret"])
buyhold_sharpe = sharpe_ratio(df["ret"])

strategy_dd = max_drawdown(df["equity_strategy"])
buyhold_dd = max_drawdown(df["equity_buyhold"])

print(f"--- {TICKER} | EWMA({FAST_SPAN}/{SLOW_SPAN}) Crossover ---")
print(f"Periode          : {df.index[0].date()} -> {df.index[-1].date()}")
print(f"Rendement strat. : {strategy_total_return:.2%}   | Buy&Hold : {buyhold_total_return:.2%}")
print(f"Sharpe strat.    : {strategy_sharpe:.2f}         | Buy&Hold : {buyhold_sharpe:.2f}")
print(f"Max drawdown str.: {strategy_dd:.2%}   | Buy&Hold : {buyhold_dd:.2%}")

# graphs
fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# Prix + EWMA + signaux de croisement
axes[0].plot(df.index, df["Close"], label="Prix", color="lightgray", linewidth=1)
axes[0].plot(df.index, df["ewma_fast"], label=f"EWMA rapide ({FAST_SPAN})", color="orange")
axes[0].plot(df.index, df["ewma_slow"], label=f"EWMA lente ({SLOW_SPAN})", color="steelblue")

crossovers = df["signal"].diff()
buy_points = df[crossovers == 1]
sell_points = df[crossovers == -1]
axes[0].scatter(buy_points.index, buy_points["Close"], marker="^", color="green", label="Achat", zorder=5)
axes[0].scatter(sell_points.index, sell_points["Close"], marker="v", color="red", label="Vente", zorder=5)

axes[0].set_title(f"{TICKER} — EWMA Crossover ({FAST_SPAN}/{SLOW_SPAN})")
axes[0].legend()
axes[0].grid(alpha=0.3)

# Courbes de performance
axes[1].plot(df.index, df["equity_strategy"], label="Strategie EWMA", color="orange")
axes[1].plot(df.index, df["equity_buyhold"], label="Buy & Hold", color="steelblue")
axes[1].set_title("Performance cumulee (base 1.0)")
axes[1].legend()
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("ewma_crossover_qqq.png", dpi=150)
plt.show()


# 2022 seul
df_2022 = df.loc["2022-01-01":"2022-12-31"].copy()

# Recalculer les equity curves à partir de 1.0 sur cette sous-période uniquement
df_2022["equity_strategy"] = (1 + df_2022["strategy_ret"]).cumprod()
df_2022["equity_buyhold"] = (1 + df_2022["ret"]).cumprod()

print("2022 seul :")
print(f"Strategie : {(df_2022['equity_strategy'].iloc[-1]-1):.2%}")
print(f"Buy&Hold  : {(df_2022['equity_buyhold'].iloc[-1]-1):.2%}")