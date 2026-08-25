from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from simpro_mock.config import settings

#create_engine opens a connection pool to the PostgreSQL db using the URL from settings
# SessionLocal is a session factory: each call to it creates a new db session
# for a single request.
engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine)

# Base is the declarative base class for all SQLAlchemy models. It provides
# the metadata and mapping functionality for the ORM.
class Base(DeclarativeBase):
    pass

# get_db() is a dependency function that provides a database session to the
# FastAPI route handlers. It creates a new session, yields it for use in the
# request, and ensures that the session is closed after the request is
# completed.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()