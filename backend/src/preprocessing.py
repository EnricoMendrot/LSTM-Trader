import pandas as pd
import numpy as np
from dependencies import get_session
from models.models import PriceHistory
from fastapi import Depends
from sqlalchemy.orm import Session

def agg(df: pd.DataFrame) -> pd.DataFrame:
    """
    Função de agregar os dados diariamente, utilizando as seguintes regras:
    - Open: o primeiro valor do dia
    - High: o valor máximo do dia
    - Low: o valor mínimo do dia
    - Close: o último valor do dia
    - Volume: a soma do volume do dia
    """

    df = (
    df.groupby(["ticker", "Date"]).agg({
          "Open": "first",
          "High": "max",
          "Low": "min",
          "Close": "last",
          "Volume": "sum"
      })
      .reset_index()
    )
    return df

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona características ao DataFrame.
    """
    # RSI
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss

    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    sma20 = df["Close"].rolling(20).mean()
    std20 = df["Close"].rolling(20).std()
    df["BB_upper"] = sma20 + 2 * std20
    df["BB_lower"] = sma20 - 2 * std20
    df["BB_position"] = (df["Close"] - df["BB_lower"]) / (df["BB_upper"] - df["BB_lower"])

    # Para colocar % - Diminui Ruído
    df["return_1"] = df["Close"].pct_change(1)
    df["return_5"] = df["Close"].pct_change(5)
    df["return_10"] = df["Close"].pct_change(10)

    # média dos preços, mas dando MAIS peso aos candles recentes.
    df["EMA_9"] = df["Close"].ewm(span=9, adjust=False).mean()
    df["EMA_21"] = df["Close"].ewm(span=21, adjust=False).mean()
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["trend"] = (df["EMA_9"] > df["EMA_21"]).astype(int)

    df["volatility"] = df["Close"].pct_change().rolling(20).std()

    df["bull_market"] = (
        df["EMA_21"] > df["EMA_50"]
    ).astype(int)

    # Target (1 = subiu, 0 = caiu)
    df["target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)

    return df

def run_preprocessing(session: Session = Depends(get_session)) -> pd.DataFrame:
    """
    Executa o processo de pré-processamento dos dados.
    """
    df = pd.read_sql_table(PriceHistory.__tablename__, session.bind)
    df = agg(df)
    df = (
    df.sort_values(["ticker", "Date"])
      .groupby("ticker", group_keys=False)
      .apply(add_features)
    )
    df =df.dropna().drop_duplicates()

    return df