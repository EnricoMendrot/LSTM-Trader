import sys
import os
import numpy as np
from fastapi import Depends
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.preprocessing import run_preprocessing
from src.test import prepare_data, MODEL_PATH
from dependencies import get_session_context

async def predict(id_stock: str, models: dict, session):
    lstm = models['lstm']
    xgb = models['xgb']
    ensemble = models['ensemble']
    scalers = models['scalers']

    df = run_preprocessing(session, id_stock= id_stock)

    X_seq, y_seq, X_xgb = prepare_data(df, scalers).values()
    
    lstm_pred = lstm.predict(X_seq[-1:])
    xgb_pred = xgb.predict_proba(X_xgb[-1:])

    final_forecast = (
          (ensemble['peso_lstm'] * lstm_pred.flatten()) +
          (ensemble['peso_xgb'] * xgb_pred[:, 1])
     )

    confidence_score = 1 - abs(lstm_pred.flatten() - xgb_pred[:, 1])

    return dict(
        prob_xgb=float(xgb_pred[0, 1]),      
        prob_lstm=float(lstm_pred[0, 0]),     
        final_forecast=float(final_forecast[0]),
        confidence_score=float(confidence_score[0]),
    )

if __name__ == "__main__":
    from tensorflow.keras.models import load_model
    import joblib
    import os
    import asyncio

    lstm = load_model(os.path.join(MODEL_PATH, 'lstm_model.keras'))
    xgb = joblib.load(os.path.join(MODEL_PATH, 'xgboost_model.pkl'))
    ensemble = joblib.load(os.path.join(MODEL_PATH, 'ensemble_config.pkl'))
    scalers = joblib.load(os.path.join(MODEL_PATH, 'scalers.pkl'))

    models = {"lstm": lstm, "xgb": xgb, "ensemble": ensemble, "scalers": scalers}

    with get_session_context() as session:
        result = asyncio.run(predict(1, models, session))  # ✅ retorna o dict de verdade

    print(result)