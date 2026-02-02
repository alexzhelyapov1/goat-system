from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config

engine_args = {}
if 'sqlite' in Config.SQLALCHEMY_DATABASE_URI:
    engine_args['connect_args'] = {"check_same_thread": False}

engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    **engine_args
)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if 'sqlite' in Config.SQLALCHEMY_DATABASE_URI:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
