from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, sessionmaker
from models.models import User, engine
from passlib.context import CryptContext
from jose import jwt, JWTError

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_session():
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def verify_token(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    try:
        dic_info = jwt.decode(token, SECRET_KEY, ALGORITHM)
        user_id = dic_info.get("sub")

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    usuario = session.query(User).filter(User.id_user == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="User not found")
    
    return usuario