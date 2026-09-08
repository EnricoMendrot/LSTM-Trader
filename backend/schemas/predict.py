from pydantic import BaseModel
from datetime import date

class PredictResponse(BaseModel):
    id_stock: int
    prob_xgb: float
    prob_lstm: float
    direction: str
    final_forecast: float
    confidence_score: float
    target_date: date

    class Config:
        from_attributes = True