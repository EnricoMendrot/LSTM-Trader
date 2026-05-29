from schemas.user import UserSchema
from schemas.login import LoginSchema
from fastapi import APIRouter, Depends, HTTPException
from models.models import User
from sqlalchemy.orm import Session
from dependencies import get_session, get_password_hash, verify_password


auth = APIRouter(prefix="/auth", tags=["auth"])

# ======== Funções auxiliares para autenticação ======== #
def gerenate_token(user: User.id_user) -> int:
    token = f"tgverfvirwjovo{user}"
    return token

def verify_user(email, password, session):
    user = session.query(User).filter(User.email == email).first()
    if not user:
        return False
    elif not verify_password(password, user.password_hash):
        return False
    return user


# ========= Endpoints de autenticação ========= #
@auth.post("/create")
async def create_user(usuario_schema: UserSchema, session: Session = Depends(get_session)):
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


@auth.post("/login")
async def login_user(login_schema: LoginSchema, session: Session = Depends(get_session)):
    """
    
    """
    user = verify_user(login_schema.email, login_schema.password, session)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    else:
        access_token = gerenate_token(user)
        return {"acess_token": access_token, "token_type": "Bearer"}