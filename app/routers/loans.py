"""
routers/loans.py — Loan Application CRUD Endpoints
====================================================
All routes require a valid JWT (via get_current_user dependency).
Data is scoped to the authenticated user — users can only see and
modify their own loan records.

Endpoints:
    POST   /loans/          — submit a new loan application
    GET    /loans/          — list all loans for current user
    GET    /loans/{id}      — get a single loan by ID
    PATCH  /loans/{id}      — update loan status (pending/approved/rejected)
    DELETE /loans/{id}      — delete a loan application

Ownership enforcement:
    Every query filters by owner_id = current_user.id
    This prevents horizontal privilege escalation
    (user A accessing user B's loans by guessing IDs).
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import get_current_user

router = APIRouter()


def _get_loan_or_404(loan_id: int, user_id: int, db: Session) -> models.Loan:
    """
    Helper: fetch a loan by ID scoped to the current user.
    Returns 404 if not found OR if it belongs to a different user.
    (We don't distinguish — prevents ID enumeration.)
    """
    loan = db.query(models.Loan).filter(
        models.Loan.id       == loan_id,
        models.Loan.owner_id == user_id,
    ).first()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan {loan_id} not found."
        )
    return loan


@router.post("/", response_model=schemas.LoanOut, status_code=201)
def create_loan(
    payload:      schemas.LoanCreate,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    """
    Submit a new loan application.
    Status defaults to 'pending' (set in the ORM model).
    Ownership is set to the authenticated user's ID.
    """
    loan = models.Loan(
        owner_id=current_user.id,
        amount=payload.amount,
        purpose=payload.purpose,
        # status defaults to LoanStatus.PENDING via ORM default
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


@router.get("/", response_model=List[schemas.LoanOut])
def list_loans(
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Return all loan applications belonging to the current user.
    Ordered by most recently created first.
    """
    return (
        db.query(models.Loan)
        .filter(models.Loan.owner_id == current_user.id)
        .order_by(models.Loan.created_at.desc())
        .all()
    )


@router.get("/{loan_id}", response_model=schemas.LoanOut)
def get_loan(
    loan_id:      int,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return a single loan by ID. Returns 404 if not found or not owned by current user."""
    return _get_loan_or_404(loan_id, current_user.id, db)


@router.patch("/{loan_id}", response_model=schemas.LoanOut)
def update_loan_status(
    loan_id:      int,
    payload:      schemas.LoanUpdate,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Update the status of a loan application.
    Valid transitions: pending → approved | rejected

    In a production system, status transitions would be controlled
    by role-based access (e.g. only admins can approve/reject).
    For this version, the owner can update their own loan status.
    """
    loan = _get_loan_or_404(loan_id, current_user.id, db)
    loan.status = payload.status
    db.commit()
    db.refresh(loan)
    return loan


@router.delete("/{loan_id}", status_code=204)
def delete_loan(
    loan_id:      int,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Delete a loan application permanently.
    Returns 204 No Content on success (standard REST convention).
    """
    loan = _get_loan_or_404(loan_id, current_user.id, db)
    db.delete(loan)
    db.commit()
    # 204 returns no body — FastAPI handles this automatically
