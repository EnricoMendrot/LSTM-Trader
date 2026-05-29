from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_session
from models.models import User
from dependencies import get_password_hash

auth = APIRouter(prefix="/auth", tags=["auth"])

@auth.post("/create")
async def create_user(email: str, password: str, name: str, session=Depends(get_session)):

    user = session.query(User).filter(User.email == email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    else:
        password_hash = get_password_hash(password)
        new_user = User(email=email, password_hash=password_hash, name=name)
        session.add(new_user)
        session.commit()
        return {"message": "User created successfully"}
    
    