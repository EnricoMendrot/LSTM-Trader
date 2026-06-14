from fastapi import FastAPI
from routes.dasboard_realtime import dashboard

app = FastAPI()

app.include_router(dashboard)

@app.get("/")
async def root():
    return {"message": "Hello World"}