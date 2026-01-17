import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

def normalize_db_url(url: str) -> str:
    # Manche Provider liefern postgres:// statt postgresql://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    # SQLAlchemy Treiber fuer psycopg
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    # Lokal Default fuer docker-compose
    DATABASE_URL = "postgresql+psycopg://tbc:tbc@localhost:5432/tbc_recruit"
else:
    DATABASE_URL = normalize_db_url(DATABASE_URL)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
