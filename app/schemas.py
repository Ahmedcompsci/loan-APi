"""
schemas.py — Pydantic Request/Response Schemas
===============================================
Pydantic validates all incoming request data before it reaches
business logic. Invalid data returns a 422 with field-level errors.

Separation from ORM models (models.py) is intentional:
    - ORM models define DB structure
    - Schemas define API contracts
    - Avoids accidentally exposing DB internals (e.g. hashed_password)
"""

from pydantic import BaseModel, EmailStr, Field
from app.models import LoanStatus


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email:    EmailStr
    password: str = Field(..., min_length=8, description="Min 8 characters")


class UserOut(BaseModel):
    """Safe user response — never exposes hashed_password."""
    id:       int
    username: str
    email:    str
    class Config:
        from_attributes = True  # allows ORM model → Pydantic conversion


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"


# ── Loans ─────────────────────────────────────────────────────────────────────

class LoanCreate(BaseModel):
    amount:  float = Field(..., gt=0, description="Loan amount in USD, must be positive")
    purpose: str   = Field(..., min_length=5, max_length=200)


class LoanUpdate(BaseModel):
    status: LoanStatus


class LoanOut(BaseModel):
    id:       int
    owner_id: int
    amount:   float
    purpose:  str
    status:   LoanStatus
    class Config:
        from_attributes = True
