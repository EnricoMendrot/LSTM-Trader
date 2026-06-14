from sqlalchemy.orm import sessionmaker
from backend.models.models import engine

def get_session():
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()