from schemas.user import UserSchema
from fastapi import APIRouter, Depends, HTTPException
from models.models import User
from sqlalchemy.orm import Session
from dependencies import get_session, get_password_hash


auth = APIRouter(prefix="/login", tags=["login"])

@auth.post("/create")
def create_user(usuario_schema: UserSchema, session: Session = Depends(get_session)):
    """
    Endpoint para criar/cadastrar um novo usuário.
    """
    user = session.query(User).filter(User.email == usuario_schema.email).first()

    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    else:
        password_hash = get_password_hash(usuario_schema.password)
        new_user = User(email=usuario_schema.email, password_hash=password_hash, name=usuario_schema.name)
        session.add(new_user)
        session.commit()
        return {"message": "User created successfully"}