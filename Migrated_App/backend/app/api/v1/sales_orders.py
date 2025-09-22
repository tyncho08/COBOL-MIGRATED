"""
Sales Orders API Router
Handles sales order management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.transactions import SalesOrder, SalesOrderLine, SalesOrderStatus
from app.models.users import User
from app.services.sales_order_service import SalesOrderService
from app.schemas.sales import SalesOrderCreate, SalesOrderUpdate, SalesOrderResponse

router = APIRouter(
    prefix="/sales-orders",
    tags=["Sales Orders"],
    responses={404: {"description": "Not found"}}
)


@router.get("/", response_model=List[SalesOrderResponse])
async def list_sales_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List sales orders with filtering and pagination"""
    service = SalesOrderService(db)
    return service.list_sales_orders(
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        status=status,
        from_date=from_date,
        to_date=to_date
    )


@router.post("/", response_model=SalesOrderResponse)
async def create_sales_order(
    order_data: SalesOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new sales order"""
    service = SalesOrderService(db)
    return service.create_sales_order(order_data, current_user.id)


@router.get("/{order_id}", response_model=SalesOrderResponse)
async def get_sales_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sales order by ID"""
    service = SalesOrderService(db)
    order = service.get_sales_order(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales order not found"
        )
    return order


@router.put("/{order_id}", response_model=SalesOrderResponse)
async def update_sales_order(
    order_id: int,
    order_data: SalesOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update sales order"""
    service = SalesOrderService(db)
    return service.update_sales_order(order_id, order_data, current_user.id)


@router.post("/{order_id}/approve")
async def approve_sales_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve sales order"""
    service = SalesOrderService(db)
    return service.approve_sales_order(order_id, current_user.id)


@router.post("/{order_id}/cancel")
async def cancel_sales_order(
    order_id: int,
    reason: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel sales order"""
    service = SalesOrderService(db)
    return service.cancel_sales_order(order_id, reason, current_user.id)


@router.post("/{order_id}/convert-to-invoice")
async def convert_to_invoice(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Convert sales order to invoice"""
    service = SalesOrderService(db)
    return service.convert_to_invoice(order_id, current_user.id)


@router.get("/{order_id}/availability")
async def check_stock_availability(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check stock availability for sales order"""
    service = SalesOrderService(db)
    return service.check_stock_availability(order_id)


@router.post("/{order_id}/allocate-stock")
async def allocate_stock(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Allocate stock for sales order"""
    service = SalesOrderService(db)
    return service.allocate_stock(order_id, current_user.id)


@router.get("/search", response_model=Dict[str, Any])
async def search_sales_orders(
    customer_code: Optional[str] = None,
    order_number: Optional[str] = None,
    customer_reference: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search sales orders"""
    service = SalesOrderService(db)
    return service.search_sales_orders(
        customer_code=customer_code,
        order_number=order_number,
        customer_reference=customer_reference,
        page=page,
        page_size=page_size
    )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_sales_order_statistics(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sales order statistics"""
    service = SalesOrderService(db)
    return service.get_statistics(from_date, to_date)