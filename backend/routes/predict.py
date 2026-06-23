from models.models import Prediction, PriceHistory, Stock
from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_session

predict = APIRouter(prefix="/predict", tags=["predict"])

@predict.post("/{stock_id}")
async def create_prediction(stock_id: int, prediction: Prediction, session=Depends(get_session)):
    stock = session.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    
    pass