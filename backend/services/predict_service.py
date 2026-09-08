import sys
import os
from pandas.tseries.offsets import BDay

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.preprocessing import run_preprocessing
from src.test import prepare_data, MODEL_PATH
from dependencies import get_session_context


async def predict_model(id_stock: str, models: dict, session):
    """
    Realiza a inferência para um ativo financeiro utilizando um modelo Ensemble
    composto por LSTM e XGBoost.

    Fluxo de execução:
        1. Recupera e pré-processa os dados históricos do ativo.
        2. Prepara os dados de entrada para cada modelo utilizando os scalers.
        3. Executa as previsões individuais da LSTM e do XGBoost.
        4. Combina as probabilidades por meio de uma média ponderada
           (Ensemble) para gerar a previsão final.
        5. Calcula um índice de confiança baseado na concordância entre
           as probabilidades produzidas pelos modelos.

    Args:
        id_stock (str):
            Identificador do ativo que será utilizado para a previsão.

        models (dict):
            Dicionário contendo os modelos treinados e os objetos auxiliares.
            Estrutura esperada:
                {
                    "lstm": Modelo LSTM,
                    "xgb": Modelo XGBoost,
                    "ensemble": {
                        "peso_lstm": float,
                        "peso_xgb": float
                    },
                    "scalers": dict
                }

        session:
            Sessão ativa utilizada para acesso aos dados.

    Returns:
        dict:
            Dicionário contendo:
                - prob_xgb (float): Probabilidade prevista pelo XGBoost.
                - prob_lstm (float): Probabilidade prevista pela LSTM.
                - final_forecast (float): Probabilidade final calculada pelo Ensemble.
                - confidence_score (float): Índice de concordância entre os modelos,
                  variando de 0 a 1, onde valores próximos de 1 indicam maior
                  consistência entre as previsões.
    """
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

    last_date = df['recorded_at'].max()
    target_date = (last_date + BDay(1)).date()

    confidence_score = 1 - abs(lstm_pred.flatten() - xgb_pred[:, 1])

    final_forecast=float(final_forecast[0])
    direction = "alta" if final_forecast > 0.5 else "baixa"

    return dict(
        prob_xgb=float(xgb_pred[0, 1]),      
        prob_lstm=float(lstm_pred[0, 0]),     
        prob_ensemble=final_forecast,
        final_forecast=final_forecast,
        direction = direction,
        confidence_score=float(confidence_score[0]),
        target_date = target_date
        
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
        result = asyncio.run(predict_model(1, models, session))  # ✅ retorna o dict de verdade

    print(result)