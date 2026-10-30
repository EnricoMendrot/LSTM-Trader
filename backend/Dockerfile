FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLBACKEND=Agg \
    TF_CPP_MIN_LOG_LEVEL=2

# libgomp1: runtime OpenMP exigido pelo XGBoost
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# MODEL_PATH (src/test.py) aponta para backend/../model/models → /app/model/models
WORKDIR /app/backend

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh \
    && mkdir -p /app/model/models

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
