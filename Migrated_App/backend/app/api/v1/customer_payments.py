"""
Customer Payments API Router
Handles customer payment and receipt management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.transactions import CustomerPayment, PaymentAllocation
from app.models.users import User
from app.services.payment_service import PaymentService
from app.schemas.sales import CustomerPaymentCreate, CustomerPaymentUpdate, CustomerPaymentResponse, PaymentAllocationCreate

router = APIRouter(
    prefix="/customer-payments",
    tags=["Customer Payments"],
    responses={404: {"description": "Not found"}}
)


@router.get("/", response_model=List[CustomerPaymentResponse])
async def list_customer_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    customer_id: Optional[int] = None,
    payment_method: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    is_allocated: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List customer payments with filtering and pagination"""
    service = PaymentService(db)
    return service.list_payments(
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        payment_method=payment_method,
        from_date=from_date,
        to_date=to_date,
        is_allocated=is_allocated
    )


@router.post("/", response_model=CustomerPaymentResponse)
async def create_customer_payment(
    payment_data: CustomerPaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new customer payment"""
    service = PaymentService(db)
    return service.create_payment(payment_data, current_user.id)


@router.get("/{payment_id}", response_model=CustomerPaymentResponse)
async def get_customer_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get customer payment by ID"""
    service = PaymentService(db)
    payment = service.get_payment(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer payment not found"
        )
    return payment


@router.put("/{payment_id}", response_model=CustomerPaymentResponse)
async def update_customer_payment(
    payment_id: int,
    payment_data: CustomerPaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update customer payment"""
    service = PaymentService(db)
    return service.update_payment(payment_id, payment_data, current_user.id)


@router.post("/{payment_id}/allocate")
async def allocate_payment_to_invoices(
    payment_id: int,
    allocations: List[PaymentAllocationCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Allocate payment to invoices"""
    service = PaymentService(db)
    return service.allocate_payment(payment_id, allocations, current_user.id)


@router.delete("/{payment_id}/allocations/{allocation_id}")
async def remove_payment_allocation(
    payment_id: int,
    allocation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove payment allocation"""
    service = PaymentService(db)
    return service.remove_allocation(payment_id, allocation_id, current_user.id)


@router.post("/{payment_id}/reverse")
async def reverse_customer_payment(
    payment_id: int,
    reason: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reverse customer payment"""
    service = PaymentService(db)
    return service.reverse_payment(payment_id, reason, current_user.id)


@router.get("/{payment_id}/allocations")
async def get_payment_allocations(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get payment allocations"""
    service = PaymentService(db)
    return service.get_allocations(payment_id)


@router.get("/search", response_model=Dict[str, Any])
async def search_customer_payments(
    customer_code: Optional[str] = None,
    payment_number: Optional[str] = None,
    reference: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search customer payments"""
    service = PaymentService(db)
    return service.search_payments(
        customer_code=customer_code,
        payment_number=payment_number,
        reference=reference,
        page=page,
        page_size=page_size
    )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_payment_statistics(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    customer_id: Optional[int] = None,
    payment_method: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get payment statistics"""
    service = PaymentService(db)
    return service.get_statistics(from_date, to_date, customer_id, payment_method)


@router.get("/unallocated")
async def get_unallocated_payments(
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get unallocated payments"""
    service = PaymentService(db)
    return service.get_unallocated_payments(customer_id)


@router.post("/auto-allocate")
async def auto_allocate_payments(
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Auto-allocate payments to oldest invoices"""
    service = PaymentService(db)
    return service.auto_allocate_payments(customer_id, current_user.id)


@router.get("/cash-receipts-journal")
async def get_cash_receipts_journal(
    from_date: date,
    to_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get cash receipts journal report"""
    service = PaymentService(db)
    return service.get_cash_receipts_journal(from_date, to_date)