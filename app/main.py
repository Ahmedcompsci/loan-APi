"""
Loan Processing API
===================
A RESTful microservice for loan application lifecycle management.

Architecture:
    Router layer   — HTTP routing and request validation (Pydantic)
    Service layer  — business logic (auth, loan rules)
    Repository     — data access via SQLAlchemy ORM

Auth flow:
    POST /auth/register → hash password → store user
    POST /auth/login    → verify password → return JWT
    All /loans/* routes → verify JWT → extract user_id → scope data

Design decisions:
    - Router/service/repository separation keeps layers independently testable
    - Pydantic validates all inputs before they touch business logic
    - bcrypt hashing: computationally expensive by design (brute-force resistant)
    - JWT: stateless auth, no server-side session storage needed
    - SQLite for dev portability; set DATABASE_URL env var for MySQL/PostgreSQL

Run locally:
    pip install -r requirements.txt
    uvicorn app.main:app --reload

Docker:
    docker build -t loan-api .
    docker run -p 8000:8000 loan-api
"""

from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth, loans

# ── Create all tables on startup ──────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Loan Processing API",
    description="RESTful microservice for loan application lifecycle management.",
    version="1.0.0",
)

# ── Mount routers ─────────────────────────────────────────────────────────────
app.include_router(auth.router,  prefix="/auth",  tags=["Authentication"])
app.include_router(loans.router, prefix="/loans", tags=["Loans"])


@app.get("/")
def root():
    return {"service": "Loan Processing API", "status": "running"}
