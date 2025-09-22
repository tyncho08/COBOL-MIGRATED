"""
Goods Receipts API Router
REST endpoints for goods receipt management
"""
from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.purchase_ledger.goods_receipt_service import GoodsReceiptService

router = APIRouter(prefix="/goods-receipts", tags=["Goods Receipts"])


# Pydantic models
class GoodsReceiptLineCreate(BaseModel):
    purchase_order_line_id: int
    quantity_received: Decimal
    unit_cost: Optional[Decimal] = None
    inspection_status: str = "PASSED"
    notes: Optional[str] = None


class GoodsReceiptCreate(BaseModel):
    purchase_order_id: int
    receipt_lines: List[GoodsReceiptLineCreate]
    delivery_note_number: Optional[str] = None
    notes: Optional[str] = None


class GoodsReceiptResponse(BaseModel):
    id: int
    receipt_number: str
    purchase_order_id: int
    purchase_order_number: str
    receipt_date: date
    receipt_status: str
    total_value: Decimal
    delivery_note_number: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", response_model=GoodsReceiptResponse)
def create_goods_receipt(
    receipt_data: GoodsReceiptCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create new goods receipt"""
    service = GoodsReceiptService(db)
    receipt = service.create_goods_receipt(
        purchase_order_id=receipt_data.purchase_order_id,
        receipt_lines=[line.dict() for line in receipt_data.receipt_lines],
        delivery_note_number=receipt_data.delivery_note_number,
        notes=receipt_data.notes,
        user_id=current_user_id
    )
    return receipt


@router.get("/{receipt_id}", response_model=GoodsReceiptResponse)
def get_goods_receipt(
    receipt_id: int,
    db: Session = Depends(get_db)
):
    """Get goods receipt by ID"""
    service = GoodsReceiptService(db)
    receipt = service.get_goods_receipt(receipt_id)
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goods receipt not found"
        )
    return receipt


@router.post("/{receipt_id}/inspect")
def update_inspection_status(
    receipt_id: int,
    line_id: int = Query(...),
    status: str = Query(...),
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Update inspection status for receipt line"""
    service = GoodsReceiptService(db)
    result = service.update_inspection_status(
        receipt_id=receipt_id,
        line_id=line_id,
        status=status,
        notes=notes,
        user_id=current_user_id
    )
    return {"message": "Inspection status updated", "status": status}


@router.post("/{receipt_id}/post-to-stock")
def post_receipt_to_stock(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Post goods receipt to stock"""
    service = GoodsReceiptService(db)
    result = service.post_receipt_to_stock(receipt_id, current_user_id)
    return {"message": "Receipt posted to stock successfully"}


@router.get("/")
def search_goods_receipts(
    purchase_order_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search goods receipts"""
    service = GoodsReceiptService(db)
    result = service.search_goods_receipts(
        purchase_order_id=purchase_order_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )
    return result


@router.get("/{receipt_id}/lines")
def get_goods_receipt_lines(
    receipt_id: int,
    db: Session = Depends(get_db)
):
    """Get goods receipt lines"""
    service = GoodsReceiptService(db)
    lines = service.get_receipt_lines(receipt_id)
    return {"lines": lines}


@router.get("/pending-inspection")
def get_pending_inspection(
    db: Session = Depends(get_db)
):
    """Get receipts pending inspection"""
    service = GoodsReceiptService(db)
    receipts = service.get_pending_inspection()
    return {"receipts": receipts}