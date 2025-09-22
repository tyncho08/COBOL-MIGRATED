"""
Purchase Orders API Router
REST endpoints for purchase order management
"""
from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.purchase_ledger.purchase_order_service import PurchaseOrderService
from app.models.purchase_transactions import PurchaseOrder

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


# Pydantic models
class PurchaseOrderLineCreate(BaseModel):
    stock_code: str
    description: str
    quantity_ordered: Decimal
    unit_cost: Decimal
    discount_percent: Optional[Decimal] = Decimal("0")
    analysis_code1: Optional[str] = None
    analysis_code2: Optional[str] = None
    notes: Optional[str] = None


class PurchaseOrderCreate(BaseModel):
    supplier_code: str
    order_lines: List[PurchaseOrderLineCreate]
    delivery_address: Optional[str] = None
    delivery_date: Optional[date] = None
    notes: Optional[str] = None
    your_reference: Optional[str] = None


class PurchaseOrderUpdate(BaseModel):
    delivery_address: Optional[str] = None
    delivery_date: Optional[date] = None
    notes: Optional[str] = None
    your_reference: Optional[str] = None


class PurchaseOrderResponse(BaseModel):
    id: int
    order_number: str
    supplier_code: str
    order_date: date
    order_status: str
    total_value: Decimal
    delivery_date: Optional[date]
    notes: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", response_model=PurchaseOrderResponse)
def create_purchase_order(
    order_data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create new purchase order"""
    service = PurchaseOrderService(db)
    order = service.create_purchase_order(
        supplier_code=order_data.supplier_code,
        order_lines=[line.dict() for line in order_data.order_lines],
        delivery_address=order_data.delivery_address,
        delivery_date=order_data.delivery_date,
        notes=order_data.notes,
        your_reference=order_data.your_reference,
        user_id=current_user_id
    )
    return order


@router.get("/{order_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    """Get purchase order by ID"""
    service = PurchaseOrderService(db)
    order = service.get_purchase_order(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    return order


@router.put("/{order_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(
    order_id: int,
    order_data: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Update purchase order"""
    service = PurchaseOrderService(db)
    order = service.update_purchase_order(
        order_id=order_id,
        updates=order_data.dict(exclude_unset=True),
        user_id=current_user_id
    )
    return order


@router.post("/{order_id}/authorize")
def authorize_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Authorize purchase order"""
    service = PurchaseOrderService(db)
    order = service.authorize_order(order_id, current_user_id)
    return {"message": "Order authorized successfully", "order_number": order.order_number}


@router.post("/{order_id}/cancel")
def cancel_purchase_order(
    order_id: int,
    reason: str = Query(..., description="Cancellation reason"),
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Cancel purchase order"""
    service = PurchaseOrderService(db)
    order = service.cancel_order(order_id, reason, current_user_id)
    return {"message": "Order cancelled successfully", "order_number": order.order_number}


@router.get("/")
def search_purchase_orders(
    supplier_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search purchase orders"""
    service = PurchaseOrderService(db)
    result = service.search_purchase_orders(
        supplier_code=supplier_code,
        status=status,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )
    return result


@router.get("/{order_id}/lines")
def get_purchase_order_lines(
    order_id: int,
    db: Session = Depends(get_db)
):
    """Get purchase order lines"""
    service = PurchaseOrderService(db)
    lines = service.get_order_lines(order_id)
    return {"lines": lines}


@router.post("/{order_id}/print")
def print_purchase_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    """Generate purchase order document"""
    service = PurchaseOrderService(db)
    document = service.generate_purchase_order_document(order_id)
    return {"document_url": document}


@router.post("/{order_id}/receive")
def receive_goods(
    order_id: int,
    receipt_data: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create goods receipt for purchase order"""
    service = PurchaseOrderService(db)
    receipt = service.create_goods_receipt(
        order_id=order_id,
        receipt_data=receipt_data or {},
        user_id=current_user_id
    )
    return {"message": "Goods receipt created successfully", "receipt_number": receipt.get("receipt_number")}


@router.post("/{order_id}/convert-to-invoice")
def convert_to_invoice(
    order_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Convert purchase order to invoice"""
    service = PurchaseOrderService(db)
    invoice = service.convert_to_invoice(order_id, current_user_id)
    return {"message": "Purchase order converted to invoice", "invoice_number": invoice.get("invoice_number")}