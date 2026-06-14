import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import yfinance as yf
from backend.dependencies import get_session
from backend.models.models import Stock
from backend.models.models import PriceHistory

TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]

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
    
    records = []
    for ticker in TICKERS:
        stock = db.query(Stock).filter(Stock.ticker == ticker).first()
        
        df = df_raw[ticker].copy()
        df.reset_index(inplace=True)
        
        for _, row in df.iterrows():
            records.append(PriceHistory(
                id_stock    = stock.id_stock,
                recorded_at = row["Date"].to_pydatetime(),
                close       = float(row["Close"]),
                open_price  = float(row["Open"]),
                price_high  = float(row["High"]),
                price_low   = float(row["Low"]),
                volume      = float(row["Volume"]),
            ))
    
    db.bulk_save_objects(records)
    db.commit()
    print(f"{len(records)} registros de histórico salvos.")

if __name__ == "__main__":
    db = next(get_session())
    try:
        print("1. Inserindo stocks...")
        seed_stocks(db)
        
        print("2. Baixando e salvando histórico...")
        seed_history(db)
    finally:
        db.close()