"""Database session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()


def create_session(url: str):
    """Create a SQLAlchemy session from a database URL."""
    engine = create_engine(url, echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


def init_db(url: str):
    """Create all tables."""
    engine = create_engine(url)
    Base.metadata.create_all(engine)
