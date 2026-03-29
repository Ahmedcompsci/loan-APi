# Loan Processing API

A RESTful microservice for loan application lifecycle management. Built with a router/service/repository architecture, JWT authentication, bcrypt password hashing, and Pydantic validation. Containerized with Docker and backed by SQLite (dev) or MySQL/PostgreSQL (prod).

## Architecture

```
Client Request
      ↓
FastAPI Router  (HTTP routing + Pydantic validation)
      ↓
Security Layer  (JWT verification → user identity)
      ↓
Business Logic  (ownership checks, status transitions)
      ↓
SQLAlchemy ORM  (repository pattern → SQL)
      ↓
SQLite / MySQL / PostgreSQL  (swap via DATABASE_URL)
```

## Quickstart

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000/docs
```

## Docker

```bash
docker build -t loan-api .
docker run -p 8000:8000 -e SECRET_KEY=your-secret loan-api

# With MySQL
docker run -p 8000:8000 \
  -e DATABASE_URL=mysql+pymysql://user:pass@host/db \
  -e SECRET_KEY=your-secret \
  loan-api
```

## Auth Flow

```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "ahmed", "email": "ahmed@example.com", "password": "securepass"}'

# 2. Login → get JWT
curl -X POST http://localhost:8000/auth/login \
  -d '{"username": "ahmed", "password": "securepass"}'
# → {"access_token": "eyJ...", "token_type": "bearer"}

# 3. Use JWT on all loan endpoints
curl http://localhost:8000/loans/ \
  -H "Authorization: Bearer eyJ..."
```

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | ❌ | Create account |
| POST | `/auth/login` | ❌ | Get JWT token |
| POST | `/loans/` | ✅ | Submit loan application |
| GET | `/loans/` | ✅ | List your loans |
| GET | `/loans/{id}` | ✅ | Get loan by ID |
| PATCH | `/loans/{id}` | ✅ | Update loan status |
| DELETE | `/loans/{id}` | ✅ | Delete loan |

## Project Structure

```
loan_api/
├── Dockerfile
├── requirements.txt
└── app/
    ├── main.py          # App entry point + router registration
    ├── database.py      # SQLAlchemy engine + session factory
    ├── models.py        # ORM models (User, Loan)
    ├── schemas.py       # Pydantic request/response schemas
    ├── security.py      # bcrypt hashing + JWT creation/verification
    └── routers/
        ├── auth.py      # POST /auth/register, /auth/login
        └── loans.py     # CRUD /loans/*
```

## Security Design
- **bcrypt** — computationally expensive hash; brute-force resistant
- **JWT** — stateless auth; no server-side session storage
- **Ownership scoping** — every loan query filters by `owner_id = current_user.id`
- **Uniform 401** — same error for "user not found" and "wrong password" (prevents username enumeration)

## Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./loans.db` | Database connection string |
| `SECRET_KEY` | `dev-secret-change-in-production` | JWT signing key — **change in prod** |

## Stack
Python 3.11 · FastAPI · SQLAlchemy · Pydantic v2 · passlib/bcrypt · python-jose · Docker
