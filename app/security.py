"""
security.py — Password Hashing and JWT Authentication
======================================================
bcrypt hashing:
    - Work factor makes brute-force attacks computationally expensive
    - passlib handles salt generation automatically
    - Never store or log plain-text passwords

JWT (JSON Web Token):
    - Stateless: server doesn't store sessions
    - Contains: {"sub": user_id, "exp": expiry_timestamp}
    - Signed with SECRET_KEY — set this via environment variable in production
    - HS256 algorithm: HMAC-SHA256

Security note:
    Set SECRET_KEY to a long random string in production:
        openssl rand -hex 32
"""

import os
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
import app.models as models

# ── Config ────────────────────────────────────────────────────────────────────

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
ALGORITHM  = "HS256"
TOKEN_EXPIRE_MINUTES = 60

# bcrypt context — handles hashing and verification
pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the bcrypt hash."""
    return pwd_context.verify(plain, hashed)


# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_access_token(data: dict) -> str:
    """
    Create a signed JWT containing `data` with an expiry timestamp.
    The token is returned to the client and sent in subsequent requests.
    """
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db:    Session = Depends(get_db),
) -> models.User:
    """
    FastAPI dependency: validates a JWT from the Authorization header
    and returns the corresponding User ORM object.

    Raises 401 if the token is missing, expired, or tampered with.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_error
    except JWTError:
        raise credentials_error

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if not user:
        raise credentials_error
    return user
