from contextlib import asynccontextmanager
import joblib
import os

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.test import MODEL_PATH
from fastapi import FastAPI

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3" 
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
from tensorflow.keras.models import load_model

@asynccontextmanager
async def load_models(app: FastAPI):
    """
    Carrega os modelos de Machine Learning e os objetos auxiliares
    necessários para realizar inferências na aplicação.

    Esta função é executada durante o ciclo de vida (lifespan) da aplicação,
    realizando o carregamento dos modelos treinados e dos scalers a partir
    do diretório configurado em `MODEL_PATH`. Após o carregamento, todos os
    objetos são armazenados em `app.state.models`, permitindo que sejam
    compartilhados entre as requisições sem a necessidade de recarregá-los.

    Modelos carregados:
        - LSTM (.keras)
        - XGBoost (.pkl)
        - Configuração do Ensemble (.pkl)
        - Scalers utilizados no pré-processamento (.pkl)

    Args:
        app (FastAPI):
            Instância da aplicação FastAPI responsável por armazenar os
            modelos durante todo o tempo de execução.

    Yields:
        None:
            Mantém os recursos carregados disponíveis durante o ciclo de
            vida da aplicação.
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
