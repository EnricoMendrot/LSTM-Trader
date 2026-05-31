from fastapi import FastAPI
from routes.auth import auth


app = FastAPI()

app.include_router(auth)

@app.get("/")
async def root():
    return {"message": "Hello World"}