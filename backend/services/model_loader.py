from contextlib import asynccontextmanager
import joblib
import os
from backend.src.test import MODEL_PATH
from fastapi import FastAPI

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3" 
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
from tensorflow.keras.models import load_model

@asynccontextmanager
async def load_models(app: FastAPI):
    """
    Função responsável por carregar o modelo de IA.
    """
    lstm = load_model(os.path.join(MODEL_PATH, 'lstm_model.keras')) 
    xgb = joblib.load(os.path.join(MODEL_PATH, 'xgboost_model.pkl'))
    ensemble = joblib.load(os.path.join(MODEL_PATH, 'ensemble_config.pkl'))
    scalers = joblib.load(os.path.join(MODEL_PATH, 'scalers.pkl'))

    app.state.models = {
        'lstm': lstm,
        'xgb': xgb,
        'ensemble': ensemble,
        'scalers': scalers
    }

    print("Models and scalers loaded successfully.")
    
    yield 

    # Shutdown: modelos e scalers serão coletados pelo GC ao final do processo
    del lstm, xgb, ensemble, scalers

app = FastAPI(lifespan=load_models)
