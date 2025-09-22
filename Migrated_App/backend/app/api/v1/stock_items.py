"""
Stock Items API Router
REST endpoints for stock item management
"""
from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.stock_service import StockService

router = APIRouter(prefix="/stock-items", tags=["Stock Items"])


# Pydantic models
class StockItemCreate(BaseModel):
    stock_code: str
    description: str
    category_code: Optional[str] = None
    unit_of_measure: str = "EACH"
    location: Optional[str] = None
    sell_price: Optional[Decimal] = None
    unit_cost: Optional[Decimal] = None
    vat_code: str = "S"
    supplier_code: Optional[str] = None
    reorder_point: Optional[Decimal] = None
    economic_order_qty: Optional[Decimal] = None


class StockItemUpdate(BaseModel):
    description: Optional[str] = None
    category_code: Optional[str] = None
    unit_of_measure: Optional[str] = None
    location: Optional[str] = None
    bin_location: Optional[str] = None
    sell_price: Optional[Decimal] = None
    vat_code: Optional[str] = None
    reorder_point: Optional[Decimal] = None
    reorder_quantity: Optional[Decimal] = None
    economic_order_qty: Optional[Decimal] = None
    minimum_stock: Optional[Decimal] = None
    maximum_stock: Optional[Decimal] = None
    lead_time_days: Optional[int] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class StockItemResponse(BaseModel):
    id: int
    stock_code: str
    description: str
    category_code: Optional[str]
    unit_of_measure: str
    location: Optional[str]
    quantity_on_hand: Decimal
    sell_price: Optional[Decimal]
    unit_cost: Optional[Decimal]
    vat_code: str
    reorder_point: Optional[Decimal]
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=StockItemResponse)
def create_stock_item(
    item_data: StockItemCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create new stock item"""
    service = StockService(db)
    item = service.create_stock_item(
        **item_data.dict(),
        user_id=current_user_id
    )
    return item


@router.get("/{item_id}", response_model=StockItemResponse)
def get_stock_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Get stock item by ID"""
    service = StockService(db)
    item = service.get_stock_item(stock_id=item_id)
    return item


@router.get("/by-code/{stock_code}", response_model=StockItemResponse)
def get_stock_item_by_code(
    stock_code: str,
    db: Session = Depends(get_db)
):
    """Get stock item by code"""
    service = StockService(db)
    item = service.get_stock_item(stock_code=stock_code)
    return item


@router.put("/{item_id}", response_model=StockItemResponse)
def update_stock_item(
    item_id: int,
    item_data: StockItemUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Update stock item"""
    service = StockService(db)
    item = service.update_stock_item(
        stock_id=item_id,
        updates=item_data.dict(exclude_unset=True),
        user_id=current_user_id
    )
    return item


@router.get("/")
def search_stock_items(
    search_term: Optional[str] = Query(None),
    category_code: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    supplier_code: Optional[str] = Query(None),
    below_reorder: bool = Query(False),
    active_only: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search stock items"""
    service = StockService(db)
    result = service.search_stock_items(
        search_term=search_term,
        category_code=category_code,
        location=location,
        supplier_code=supplier_code,
        below_reorder=below_reorder,
        active_only=active_only,
        page=page,
        page_size=page_size
    )
    return result


@router.get("/summary")
def get_stock_summary(
    location_code: Optional[str] = Query(None),
    category_code: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get stock summary statistics"""
    service = StockService(db)
    summary = service.get_stock_summary(
        location_code=location_code,
        category_code=category_code
    )
    return summary


@router.post("/{item_id}/movement")
def create_stock_movement(
    item_id: int,
    movement_type: str = Query(...),
    quantity: Decimal = Query(...),
    unit_cost: Optional[Decimal] = Query(None),
    reference: Optional[str] = Query(None),
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create stock movement"""
    service = StockService(db)
    movement = service.create_stock_movement(
        stock_id=item_id,
        movement_type=movement_type,
        quantity=quantity,
        unit_cost=unit_cost,
        reference=reference,
        notes=notes,
        user_id=current_user_id
    )
    return {"message": "Stock movement created", "movement_id": movement.id}


@router.get("/{item_id}/movements")
def get_stock_movements(
    item_id: int,
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    movement_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get stock movements for item"""
    from app.services.stock_control.stock_movement_service import StockMovementService
    service = StockMovementService(db)
    movements = service.get_stock_movements(
        stock_id=item_id,
        from_date=from_date,
        to_date=to_date,
        movement_type=movement_type,
        page=page,
        page_size=page_size
    )
    return movements


@router.get("/{item_id}/valuation")
def get_stock_valuation(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Get stock valuation for item"""
    service = StockService(db)
    valuation = service.calculate_stock_value(stock_id=item_id)
    return valuation


@router.get("/below-reorder")
def get_items_below_reorder(
    db: Session = Depends(get_db)
):
    """Get items below reorder level"""
    service = StockService(db)
    items = service.check_reorder_levels()
    return {"items": items}