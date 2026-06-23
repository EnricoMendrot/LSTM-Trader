from fastapi import FastAPI
from routes.dashboard import dashboard

app = FastAPI()

app.include_router(dashboard)

@app.get("/")
async def root():
    return {"message": "Hello World"}