from models.models import PriceHistory, Stock
from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_session
from sqlalchemy.orm import Session

dashboard = APIRouter(prefix = '/dashboard', tags=['dashboard'])

@dashboard.get("/history/{ticker}")
async def get_stock_data(ticker: str, session: Session = Depends(get_session)) -> dict:
    """
    Endpoint para buscar os dados de determinada ação, por exemplo, Apple (AAPL). O ticker é o símbolo da ação na bolsa de valores. O endpoint retorna um dicionário com os dados da ação solicitada.
    """
    ticker = session.query(Stock).filter(Stock.ticker == ticker).first()

    if not ticker:
        raise HTTPException(status_code=404, detail="Stock not found")

    price_history = session.query(PriceHistory).filter(PriceHistory.id_stock == ticker.id_stock).all()

    return {'Ticker': ticker.ticker,
            'Company Name': ticker.company_name,
            "History": [
            {"recorded_at": t.recorded_at,
             "close": t.close,
             "open_price": t.open_price,
             "price_high": t.price_high,
             "price_low": t.price_low,
             "volume": t.volume}
            for t in price_history
    ]}