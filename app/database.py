"""
database.py — SQLAlchemy Engine and Session Factory
====================================================
Reads DATABASE_URL from environment for easy environment swapping:
    - SQLite  (default, dev/test)
    - MySQL   (production: mysql+pymysql://user:pass@host/db)
    - PostgreSQL (production: postgresql://user:pass@host/db)
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./loans.db")

engine = create_engine(
    DATABASE_URL,
    # SQLite needs this flag for multi-threaded FastAPI usage
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# SessionLocal: one DB session per request (closed in dependency)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base: all ORM models inherit from this
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a DB session per request.
    Ensures the session is always closed, even on exceptions.

    Usage in routers:
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
