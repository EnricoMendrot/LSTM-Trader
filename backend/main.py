import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.model_loader import load_models
from fastapi import FastAPI
from routes.auth import auth
from routes.dashboard import dashboard
from routes.predict import predict as predict_router

app = FastAPI(lifespan=load_models)


app.include_router(auth)
app.include_router(dashboard)
app.include_router(predict_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}