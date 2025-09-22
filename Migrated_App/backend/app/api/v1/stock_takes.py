"""
Stock Takes API Router
REST endpoints for stock take management
"""
from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.stock_control.stock_take_service import StockTakeService

router = APIRouter(prefix="/stock-takes", tags=["Stock Takes"])


# Pydantic models
class StockTakeCreate(BaseModel):
    take_name: str
    location_code: Optional[str] = None
    category_filter: Optional[str] = None
    freeze_stock: bool = True
    notes: Optional[str] = None


class StockCountCreate(BaseModel):
    stock_id: int
    counted_quantity: Decimal
    notes: Optional[str] = None


class StockTakeResponse(BaseModel):
    id: int
    take_number: str
    take_name: str
    take_date: date
    take_status: str
    location_code: Optional[str]
    items_to_count: int
    items_counted: int
    items_with_variance: int
    total_variance_value: Decimal
    is_frozen: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=StockTakeResponse)
def create_stock_take(
    take_data: StockTakeCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create new stock take"""
    service = StockTakeService(db)
    stock_take = service.create_stock_take(
        **take_data.dict(),
        user_id=current_user_id
    )
    return stock_take


@router.get("/{take_id}", response_model=StockTakeResponse)
def get_stock_take(
    take_id: int,
    db: Session = Depends(get_db)
):
    """Get stock take by ID"""
    service = StockTakeService(db)
    stock_take = service.get_stock_take(take_id)
    if not stock_take:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock take not found"
        )
    return stock_take


@router.post("/{take_id}/generate-sheets")
def generate_count_sheets(
    take_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Generate count sheets for stock take"""
    service = StockTakeService(db)
    sheets = service.generate_count_sheets(take_id, current_user_id)
    return {"message": "Count sheets generated", "sheets": sheets}


@router.post("/{take_id}/counts")
def record_stock_count(
    take_id: int,
    count_data: StockCountCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Record stock count"""
    service = StockTakeService(db)
    count = service.record_stock_count(
        take_id=take_id,
        **count_data.dict(),
        user_id=current_user_id
    )
    return {"message": "Stock count recorded", "count_id": count.id}


@router.get("/{take_id}/counts")
def get_stock_counts(
    take_id: int,
    variance_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Get stock counts for take"""
    service = StockTakeService(db)
    counts = service.get_stock_counts(take_id, variance_only)
    return {"counts": counts}


@router.post("/{take_id}/post-adjustments")
def post_stock_adjustments(
    take_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Post stock take adjustments"""
    service = StockTakeService(db)
    result = service.post_stock_adjustments(take_id, current_user_id)
    return {"message": "Adjustments posted", "adjustments": result}


@router.post("/{take_id}/finalize")
def finalize_stock_take(
    take_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Finalize stock take"""
    service = StockTakeService(db)
    stock_take = service.finalize_stock_take(take_id, current_user_id)
    return {"message": "Stock take finalized", "take_number": stock_take.take_number}


@router.get("/")
def search_stock_takes(
    status: Optional[str] = Query(None),
    location_code: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search stock takes"""
    service = StockTakeService(db)
    result = service.search_stock_takes(
        status=status,
        location_code=location_code,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )
    return result


@router.get("/{take_id}/variance-report")
def get_variance_report(
    take_id: int,
    db: Session = Depends(get_db)
):
    """Get stock take variance report"""
    service = StockTakeService(db)
    report = service.generate_variance_report(take_id)
    return report


@router.get("/{take_id}/count-sheets")
def get_count_sheets(
    take_id: int,
    format: str = Query("PDF", regex="^(PDF|EXCEL)$"),
    db: Session = Depends(get_db)
):
    """Get count sheets for stock take"""
    service = StockTakeService(db)
    sheets = service.export_count_sheets(take_id, format)
    return {"download_url": sheets}