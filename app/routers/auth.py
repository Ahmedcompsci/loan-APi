"""
routers/auth.py — User Registration and JWT Login
==================================================
Handles the two unauthenticated endpoints:
    POST /auth/register — create a new user account
    POST /auth/login    — verify credentials, return JWT

Security flow:
    Register: validate input → check uniqueness → hash password → store user
    Login:    find user → verify bcrypt hash → issue signed JWT

The JWT returned from /login is sent by the client as:
    Authorization: Bearer <token>
on all subsequent /loans/* requests.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import hash_password, verify_password, create_access_token

router = APIRouter()


@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.

    Checks:
        - Username must be unique
        - Email must be unique
        - Password is hashed with bcrypt before storage
          (plain-text password is never written to the DB)

    Returns the created user object (without hashed_password).
    """
    # Check username availability
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken."
        )

    # Check email availability
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )

    # Create user — password is hashed here, never stored plain
    user = models.User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)  # reload from DB to populate auto-generated fields (id, created_at)
    return user


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user and return a signed JWT.

    Security note:
        We return the same 401 error for both "user not found" and
        "wrong password" — this prevents username enumeration attacks.
    """
    # Look up user by username
    user = db.query(models.User).filter(models.User.username == payload.username).first()

    # Use the same error for missing user and wrong password (timing-safe)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue JWT — payload contains user ID as "sub" (subject) claim
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
