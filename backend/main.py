from fastapi import FastAPI
from backend.routes.predict import predict

app = FastAPI()

app.include_router(predict)

@app.get("/")
async def root():
    return {"message": "Hello World"}