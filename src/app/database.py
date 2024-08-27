from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://username:password@postgres-service:5432/iivashko"
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:password@host.docker.internal:5432/card_app"

engine = create_engine(url=SQLALCHEMY_DATABASE_URL, echo=True)
new_session = sessionmaker(engine, expire_on_commit=False)

def get_db():
    db = new_session()
    try:
        yield db
    finally:
        db.close()
