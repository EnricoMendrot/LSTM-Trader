from backend.services.model_loader import load_models
from fastapi import FastAPI
from backend.routes.predict import predict as predict_router

app = FastAPI(lifespan=load_models)

app.include_router(predict_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}