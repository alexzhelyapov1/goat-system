from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config

# Create a new engine instance for the FastAPI app
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

# Create a new sessionmaker instance for the FastAPI app
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
