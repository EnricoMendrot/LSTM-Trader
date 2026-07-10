from sqlalchemy.orm import sessionmaker
from models.models import engine
from contextlib import contextmanager

def get_session():
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

@contextmanager
def get_session_context():
    '''
    Serve para o FastAPI Dependency Injection, permitindo que a sessão do banco de dados seja injetada em rotas ou funções que precisam dela
    '''
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()