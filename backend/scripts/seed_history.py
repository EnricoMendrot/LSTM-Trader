import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pandas as pd
import yfinance as yf
from backend.dependencies import get_session
from backend.models.models import Stock
from backend.models.models import PriceHistory

TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]


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

    df["rsi"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    sma20 = df["Close"].rolling(20).mean()
    std20 = df["Close"].rolling(20).std()
    df["bb_upper"] = sma20 + 2 * std20
    df["bb_lower"] = sma20 - 2 * std20
    df["bb_position"] = (df["Close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

    # Para colocar % - Diminui Ruído
    df["return_1"] = df["Close"].pct_change(1)
    df["return_5"] = df["Close"].pct_change(5)
    df["return_10"] = df["Close"].pct_change(10)

    # média dos preços, mas dando MAIS peso aos candles recentes.
    df["ema_9"] = df["Close"].ewm(span=9, adjust=False).mean()
    df["ema_21"] = df["Close"].ewm(span=21, adjust=False).mean()
    df["ema_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["trend"] = (df["ema_9"] > df["ema_21"]).astype(int)

    df["volatility"] = df["Close"].pct_change().rolling(20).std()

    df['ema_9_rel']  = df['Close'] / df['ema_9'] - 1
    df['ema_21_rel'] = df['Close'] / df['ema_21'] - 1
    df['ema_50_rel'] = df['Close'] / df['ema_50'] - 1

    df['Open_rel']  = df['Open']  / df['Close'] - 1
    df['High_rel']  = df['High']  / df['Close'] - 1
    df['Low_rel']   = df['Low']   / df['Close'] - 1
    
    df["bull_market"] = (
        df["ema_21"] > df["ema_50"]
    ).astype(int)

    # Target (1 = subiu, 0 = caiu)
    df["target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)

    return df

def seed_stocks(db):
    for ticker in TICKERS:
        existing = db.query(Stock).filter(Stock.ticker == ticker).first()
        if existing:
            continue
        
        info = yf.Ticker(ticker).info
        stock = Stock(
            ticker       = ticker,
            company_name = info.get("longName", ticker),
            sector       = info.get("sector", "Unknown"),
            exchange     = info.get("exchange", "Unknown"),
        )
        db.add(stock)
    
    db.commit()
    print("Stocks inseridos.")

def seed_history(db):
    df_raw = yf.download(TICKERS, start="2010-01-01", group_by="ticker")
    spy = yf.download("SPY", start="2010-01-01")
    vix = yf.download("^VIX", start="2010-01-01")

    spy = spy.reset_index()
    vix = vix.reset_index()

    if isinstance(spy.columns, pd.MultiIndex):
        spy.columns = spy.columns.get_level_values(0)

    if isinstance(vix.columns, pd.MultiIndex):
        vix.columns = vix.columns.get_level_values(0)
    records = []

    for ticker in TICKERS:
        stock = db.query(Stock).filter(Stock.ticker == ticker).first()

        df = df_raw[ticker].copy()
        df.reset_index(inplace=True)

        df = df.merge(spy[["Date", "Close"]], on="Date", how="left", suffixes=("", "_spy"))
        df = df.merge(vix[["Date", "Close"]], on="Date", how="left", suffixes=("", "_vix"))

        df.rename(columns={
            "Close_spy": "spy_close",
            "Close_vix": "vix_close"
        }, inplace=True)

        df["spy_return"] = df["spy_close"].pct_change()
        df["vix_change"] = df["vix_close"].pct_change()
        df["bull_market"] = (df["spy_close"] > df["spy_close"].rolling(50).mean()).astype(int)

        df = add_features(df)


        for row in df.itertuples(index=False):

            records.append(PriceHistory(
                id_stock    = stock.id_stock,
                recorded_at = row.Date.to_pydatetime(),

                open_price  = float(row.Open),
                price_high  = float(row.High),
                price_low   = float(row.Low),
                close       = float(row.Close),
                volume      = float(row.Volume),

                return_1    = getattr(row, "return_1", None),
                return_5    = getattr(row, "return_5", None),
                return_10   = getattr(row, "return_10", None),

                ema_9       = getattr(row, "ema_9", None),
                ema_21      = getattr(row, "ema_21", None),
                ema_50      = getattr(row, "ema_50", None),

                rsi         = getattr(row, "rsi", None),
                macd        = getattr(row, "macd", None),
                macd_signal = getattr(row, "macd_signal", None),

                bb_upper    = getattr(row, "bb_upper", None),
                bb_lower    = getattr(row, "bb_lower", None),
                bb_position = getattr(row, "bb_position", None),

                trend       = int(getattr(row, "trend", 0)),
                volatility = getattr(row, "volatility", None),
                spy_return = getattr(row, "spy_return", None),
                vix_change = getattr(row, "vix_change", None),
                bull_market = int(getattr(row, "bull_market", 0)),
            ))

    db.bulk_save_objects(records)
    db.commit()

    print(f"{len(records)} registros salvos.")

if __name__ == "__main__":
    db = next(get_session())
    try:
        print("1. Inserindo stocks...")
        seed_stocks(db)
        
        print("2. Baixando e salvando histórico...")
        seed_history(db)
    finally:
        db.close()