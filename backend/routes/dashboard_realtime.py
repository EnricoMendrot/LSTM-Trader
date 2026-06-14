from models.models import PriceHistory
from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_session
from sqlalchemy.orm import Session

dashboard = APIRouter(prefix = '/dashboard', tags=['dashboard'])

@dashboard.get("/history/{id_stock}")
async def get_stock_data(id_stock: int, session: Session = Depends(get_session)) -> dict:
    """
    Endpoint para buscar os dados de determinada ação, por exemplo, Apple (AAPL). O ticker é o símbolo da ação na bolsa de valores. O endpoint retorna um dicionário com os dados da ação solicitada.
    """

    ticker = session.query(PriceHistory).filter(PriceHistory.id_stock == id_stock).all()


    return {"ticker": [
            {"recorded_at": t.recorded_at,
             "close": t.close,
             "open_price": t.open_price,
             "price_high": t.price_high,
             "price_low": t.price_low,
             "volume": t.volume}
            for t in ticker
    ]}
      

