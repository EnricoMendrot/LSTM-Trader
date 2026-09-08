from fastapi import APIRouter, Depends, HTTPException, Request
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dependencies import get_session
from models.models import Prediction, Stock
from services.predict_service import predict_model
from schemas.predict import PredictResponse

predict = APIRouter(prefix="/predict", tags=["predict"])

@predict.post("/{id_stock}", response_model=PredictResponse)
async def create_prediction(request: Request, id_stock: int, session=Depends(get_session)) -> PredictResponse:
    """
    Função responsável por retornar um json com os dados da previsão.

    Fluxo do processo:
        1. Verificação dos dados
        2. Carregamento dos modelos
        3. Fazer a previsão dos modelos
        4. Retorna as previsões 

    Args:
        id_stock(int):
            Identificador do ativo que será utilizado para a previsão.
        
        request:
            Request para buscar os modelos carregados

        session:
            Sessão ativa utilizada para acesso aos dados.
    
    Returns:
        dicionário contendo as informações das predições:

            - "id_stock": id da ação,
            - "prob_xgb": probabilidade do modelo XGBoost,
            - "prob_lstm": probabilidade do modelo LSTM,
            - "direction": se ele prevê alta ou baixa,
            - "final_forecast": probabilidade final (confiança),
            - "confidence_score": confiança entre os modelos,
            - "target_date": dia que os modelos preveem
    """

    stock = session.query(Stock).filter(Stock.id_stock == id_stock).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")


    models = request.app.state.models
    result = await predict_model(id_stock, models, session)

    print(Prediction.__table__.columns.keys())
    
    prediction = Prediction(
        id_stock=id_stock,
        version_model="v1.0",
        prob_lstm=result["prob_lstm"],
        prob_xgboost=result["prob_xgb"],
        prob_ensemble=result["final_forecast"],
        final_forecast=result["final_forecast"],
        confidence_score=result["confidence_score"],
        target_date=result["target_date"]
    )

    session.add(prediction)
    session.commit()
    session.refresh(prediction)

    return PredictResponse(id_stock=id_stock, **result)
