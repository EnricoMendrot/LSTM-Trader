from fastapi import FastAPI
from routes.auth import auth
from routes.dashboard import dashboard

app = FastAPI()

app.include_router(auth)
app.include_router(dashboard)

@app.get("/")
async def root():
    return {"message": "Hello World"}