from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from models.models import engine
from passlib.context import CryptContext
import bcrypt
import os


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_session():
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

def _truncate(password: str) -> str:
    return password.encode("utf-8")[:72].decode("utf-8", errors="ignore")

def get_password_hash(password: str) -> str:
    truncated = password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(truncated, bcrypt.gensalt())
    return hashed.decode("utf-8")