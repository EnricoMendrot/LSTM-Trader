from schemas.user import UserSchema
from schemas.login import LoginSchema
from models.models import User
from dependencies import get_session, verify_token
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

auth = APIRouter(prefix="/auth", tags=["auth"])

# ======== Funções auxiliares para autenticação ======== #

def generate_token(user: User, token_duration=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    data_expire = datetime.now(timezone.utc) + token_duration
    dic_info = {
        "sub": str(user.id_user),
        "exp": data_expire
    }
    jwt_encode = jwt.encode(dic_info, SECRET_KEY, algorithm=ALGORITHM)
    return jwt_encode

def verify_user(email, password, session):
    user = session.query(User).filter(User.email == email).first()
    if not user:
        return False
    elif not verify_password(password, user.password_hash):
        return False
    return user 

def _truncate(password: str) -> str:
    return password.encode("utf-8")[:72].decode("utf-8", errors="ignore")

def get_password_hash(password: str) -> str:
    truncated = password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(truncated, bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    truncated = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(truncated, hashed_password.encode("utf-8"))

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
    Endpoint para autenticar um usuário já existente e gerar um token JWT.
    """
    user = verify_user(login_schema.email, login_schema.password, session)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    else:
        access_token = generate_token(user)
        refresh_token = generate_token(user, token_duration = timedelta(days = 7) )
        return {"access_token": access_token, 
                "refresh_token": refresh_token, 
                "token_type": "Bearer"}
    

@auth.post("/login-form")
async def login_form(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    """
    Endpoint serve para efetuar o login de um usuário pelo botão de Authorize.
    """
    user = verify_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    else:
        access_token = generate_token(user)
        refresh_token = generate_token(user, token_duration = timedelta(days = 7) )
        return {"access_token": access_token, 
                "token_type": "Bearer"}
            
@auth.get("/refresh")
async def use_refresh_token(user: User = Depends(verify_token)): 
    access_token = generate_token(user)

    return {
        "access_token": access_token, 
        "token_type": "Bearer"
    }