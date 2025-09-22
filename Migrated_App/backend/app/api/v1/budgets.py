"""
Budgets API Router
REST endpoints for budget management
"""
from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.general_ledger.budget_service import BudgetService

router = APIRouter(prefix="/budgets", tags=["Budgets"])


# Pydantic models
class BudgetCreate(BaseModel):
    budget_name: str
    fiscal_year: int
    budget_type: str = "ANNUAL"
    description: Optional[str] = None


class BudgetLineCreate(BaseModel):
    account_code: str
    annual_amount: Decimal
    spread_method: str = Field("EVEN", regex="^(EVEN|CUSTOM)$")
    period_amounts: Optional[List[Decimal]] = None
    notes: Optional[str] = None


class BudgetCopyRequest(BaseModel):
    new_budget_name: str
    new_fiscal_year: int
    adjustment_percent: Optional[Decimal] = None


class BudgetResponse(BaseModel):
    id: int
    budget_name: str
    fiscal_year: int
    budget_type: str
    description: Optional[str]
    is_active: bool
    is_approved: bool
    total_amount: Decimal
    approved_date: Optional[date]
    approved_by: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", response_model=BudgetResponse)
def create_budget(
    budget_data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create new budget"""
    service = BudgetService(db)
    budget = service.create_budget(
        **budget_data.dict(),
        user_id=current_user_id
    )
    return budget


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: int,
    db: Session = Depends(get_db)
):
    """Get budget by ID"""
    from app.models.general_ledger import BudgetHeader
    budget = db.query(BudgetHeader).filter(BudgetHeader.id == budget_id).first()
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    return budget


@router.post("/{budget_id}/lines")
def add_budget_line(
    budget_id: int,
    line_data: BudgetLineCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Add budget line"""
    service = BudgetService(db)
    line = service.add_budget_line(
        budget_id=budget_id,
        **line_data.dict(),
        user_id=current_user_id
    )
    return {"message": "Budget line added", "line_id": line.id}


@router.post("/{budget_id}/approve")
def approve_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Approve budget for use"""
    service = BudgetService(db)
    budget = service.approve_budget(budget_id, current_user_id)
    return {"message": "Budget approved", "budget_name": budget.budget_name}


@router.post("/{budget_id}/copy")
def copy_budget(
    budget_id: int,
    copy_data: BudgetCopyRequest,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Copy budget to new year"""
    service = BudgetService(db)
    new_budget = service.copy_budget(
        source_budget_id=budget_id,
        new_budget_name=copy_data.new_budget_name,
        new_fiscal_year=copy_data.new_fiscal_year,
        adjustment_percent=copy_data.adjustment_percent,
        user_id=current_user_id
    )
    return {"message": "Budget copied", "new_budget_id": new_budget.id}


@router.get("/{budget_id}/lines")
def get_budget_lines(
    budget_id: int,
    db: Session = Depends(get_db)
):
    """Get budget lines"""
    from app.models.general_ledger import BudgetLine
    lines = db.query(BudgetLine).filter(BudgetLine.budget_id == budget_id).all()
    return {"lines": lines}


@router.get("/{budget_id}/variance")
def get_budget_variance(
    budget_id: int,
    period_id: Optional[int] = Query(None),
    variance_threshold: Optional[Decimal] = Query(None),
    db: Session = Depends(get_db)
):
    """Get budget variance report"""
    service = BudgetService(db)
    report = service.get_budget_variance_report(
        budget_id=budget_id,
        period_id=period_id,
        variance_threshold=variance_threshold
    )
    return report


@router.get("/")
def search_budgets(
    fiscal_year: Optional[int] = Query(None),
    budget_type: Optional[str] = Query(None),
    is_approved: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Search budgets"""
    from app.models.general_ledger import BudgetHeader
    from sqlalchemy import and_
    
    query = db.query(BudgetHeader)
    
    filters = []
    if fiscal_year:
        filters.append(BudgetHeader.fiscal_year == fiscal_year)
    if budget_type:
        filters.append(BudgetHeader.budget_type == budget_type)
    if is_approved is not None:
        filters.append(BudgetHeader.is_approved == is_approved)
    if is_active is not None:
        filters.append(BudgetHeader.is_active == is_active)
    
    if filters:
        query = query.filter(and_(*filters))
    
    budgets = query.order_by(BudgetHeader.fiscal_year.desc(), BudgetHeader.budget_name).all()
    return {"budgets": budgets}


@router.delete("/{budget_id}/lines/{line_id}")
def delete_budget_line(
    budget_id: int,
    line_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Delete budget line"""
    from app.models.general_ledger import BudgetLine, BudgetHeader
    
    # Check budget exists and is not approved
    budget = db.query(BudgetHeader).filter(BudgetHeader.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    if budget.is_approved:
        raise HTTPException(status_code=400, detail="Cannot modify approved budget")
    
    # Delete line
    line = db.query(BudgetLine).filter(
        BudgetLine.id == line_id,
        BudgetLine.budget_id == budget_id
    ).first()
    
    if not line:
        raise HTTPException(status_code=404, detail="Budget line not found")
    
    # Update budget total
    budget.total_amount -= line.annual_budget
    db.delete(line)
    db.commit()
    
    return {"message": "Budget line deleted"}