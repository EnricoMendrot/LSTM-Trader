import pandas as pd
from fastapi import Depends
from sqlalchemy.orm import Session
import os
import sys
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models.models import PriceHistory
from dependencies import get_session, get_session_context

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
    df.groupby(["id_stock", "recorded_at"]).agg({
        "open_price": "first",
        "price_high": "max",
        "price_low": "min",
        "close": "last",
        "volume": "sum",
        "spy_return": "last",
        "vix_change": "last"
    })
      .reset_index()
    )
    return df

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona características ao DataFrame.
    """

    # RSI
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss

    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    sma20 = df["close"].rolling(20).mean()
    std20 = df["close"].rolling(20).std()
    df["BB_upper"] = sma20 + 2 * std20
    df["BB_lower"] = sma20 - 2 * std20
    df["BB_position"] = (df["close"] - df["BB_lower"]) / (df["BB_upper"] - df["BB_lower"])

    # Para colocar % - Diminui Ruído
    df["return_1"] = df["close"].pct_change(1)
    df["return_5"] = df["close"].pct_change(5)
    df["return_10"] = df["close"].pct_change(10)

    # média dos preços, mas dando MAIS peso aos candles recentes.
    df["EMA_9"] = df["close"].ewm(span=9, adjust=False).mean()
    df["EMA_21"] = df["close"].ewm(span=21, adjust=False).mean()
    df["EMA_50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["trend"] = (df["EMA_9"] > df["EMA_21"]).astype(int)

    df["volatility"] = df["close"].pct_change().rolling(20).std()

    df['EMA_9_rel']  = df['close'] / df['EMA_9'] - 1
    df['EMA_21_rel'] = df['close'] / df['EMA_21'] - 1
    df['EMA_50_rel'] = df['close'] / df['EMA_50'] - 1
    df['BB_upper_rel'] = df['close'] / df['BB_upper'] - 1
    df['BB_lower_rel'] = df['close'] / df['BB_lower'] - 1
    df['Open_rel']  = df['open_price']  / df['close'] - 1
    df['High_rel']  = df['price_high']  / df['close'] - 1
    df['Low_rel']   = df['price_low']   / df['close'] - 1

    df['SPY_return_5'] = df.groupby('id_stock')['spy_return'].transform(lambda x: x.rolling(5).sum())
    
    df.drop(columns=['EMA_9', 'EMA_21', 'EMA_50', 'BB_upper', 'BB_lower'], inplace=True)
    df.drop(columns=['open_price', 'price_high', 'price_low'], inplace=True)
    df.drop(columns=[
        'BB_position',
        'EMA_9_rel',
        'EMA_21_rel',
        'EMA_50_rel',
        'trend',
        'return_10',
        'MACD_signal'
    ], inplace=True)

    future_return = (df["close"].shift(-5) - df["close"]) / df["close"]
    df["target"] = (future_return > 0.03).astype(int)

    return df

def run_preprocessing(session: Session = Depends(get_session)) -> pd.DataFrame:
    """
    Executa o processo de pré-processamento dos dados.
    """
    df = pd.read_sql_table(PriceHistory.__tablename__, session.bind)
    df = agg(df)
    
    df = df.sort_values(["id_stock", "recorded_at"])

    grupos_processados = []
    for id_stock, grupo in df.groupby("id_stock"):
        grupo = add_features(grupo)
        grupos_processados.append(grupo)

    df = pd.concat(grupos_processados)
    df = df.dropna().drop_duplicates()
        
    return df

if __name__ == "__main__":
    with get_session_context() as session:
        df = run_preprocessing(session)
        os.makedirs("data", exist_ok=True)
        print("Dados processados e salvos em data/processed_data.csv")
        print(df.head())
        df.to_csv(os.path.join("data", "processed_data.csv"), index=False)