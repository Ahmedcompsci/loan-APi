"""
models.py — SQLAlchemy ORM Models
===================================
Defines the database schema as Python classes.
SQLAlchemy maps these to SQL tables automatically.

Tables:
    users — registered API users (one-to-many with loans)
    loans — loan applications (many-to-one with users)
"""

import enum
from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class LoanStatus(str, enum.Enum):
    """Enum for loan application lifecycle states."""
    PENDING  = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(50),  unique=True, nullable=False, index=True)
    email           = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    # One user → many loans
    loans = relationship("Loan", back_populates="owner")


class Loan(Base):
    __tablename__ = "loans"

    id         = Column(Integer, primary_key=True, index=True)
    owner_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount     = Column(Float,   nullable=False)
    purpose    = Column(String(200), nullable=False)
    status     = Column(Enum(LoanStatus), default=LoanStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Many loans → one user
    owner = relationship("User", back_populates="loans")
