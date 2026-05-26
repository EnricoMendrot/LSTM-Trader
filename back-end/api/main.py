from fastapi import FastAPI
from routes.login import login
from routes.register import register

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}