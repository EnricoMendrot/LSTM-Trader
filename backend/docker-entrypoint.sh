#!/bin/sh
set -e

MODELS_DIR=/app/model/models

# Os modelos não são versionados. Na primeira subida, treina a partir do banco
# e guarda no volume `models`; nas próximas, só carrega.
if [ ! -f "$MODELS_DIR/lstm_model.keras" ] || [ ! -f "$MODELS_DIR/xgboost_model.pkl" ] \
   || [ ! -f "$MODELS_DIR/ensemble_config.pkl" ] || [ ! -f "$MODELS_DIR/scalers.pkl" ]; then
    echo ">> Modelos não encontrados em $MODELS_DIR. Treinando (leva alguns minutos)..."
    python -m src.preprocessing
    python src/train.py
    echo ">> Treino concluído."
fi

exec uvicorn main:app --host 0.0.0.0 --port 8000
