from fastapi import FastAPI
from backend.routes.login import login
from backend.routes.register import register

app = FastAPI()

app.include_router(login)
app.include_router(register)

@app.get("/")
async def root():
    return {"message": "Hello World"}