from fastapi import FastAPI
from routes.auth import auth
from routes.register import register

app = FastAPI()

app.include_router(auth)
app.include_router(register)

@app.get("/")
async def root():
    return {"message": "Hello World"}