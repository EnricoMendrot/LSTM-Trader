from fastapi import APIRouter, HTTPException

register = APIRouter(prefix="/register", tags=["register"])

@register.post("/")
async def register_user():
    return {"message": "User registered successfully"}

@register.get("/")
async def get_register():
    return {"message": "Bem-vindo à página de registro!"}