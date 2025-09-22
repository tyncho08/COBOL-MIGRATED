"""
Supplier Payments API Router
REST endpoints for supplier payment management
"""
from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.purchase_ledger.supplier_payment_service import SupplierPaymentService

router = APIRouter(prefix="/supplier-payments", tags=["Supplier Payments"])


# Pydantic models
class PaymentAllocationCreate(BaseModel):
    invoice_id: int
    allocation_amount: Decimal
    discount_taken: Optional[Decimal] = Decimal("0")


class SupplierPaymentCreate(BaseModel):
    supplier_code: str
    payment_method: str
    payment_amount: Decimal
    allocations: List[PaymentAllocationCreate]
    reference: Optional[str] = None
    notes: Optional[str] = None


class SupplierPaymentResponse(BaseModel):
    id: int
    payment_number: str
    supplier_code: str
    payment_date: date
    payment_method: str
    payment_amount: Decimal
    allocated_amount: Decimal
    unallocated_amount: Decimal
    payment_status: str
    reference: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", response_model=SupplierPaymentResponse)
def create_supplier_payment(
    payment_data: SupplierPaymentCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create new supplier payment"""
    service = SupplierPaymentService(db)
    payment = service.create_supplier_payment(
        supplier_code=payment_data.supplier_code,
        payment_method=payment_data.payment_method,
        payment_amount=payment_data.payment_amount,
        allocations=[alloc.dict() for alloc in payment_data.allocations],
        reference=payment_data.reference,
        notes=payment_data.notes,
        user_id=current_user_id
    )
    return payment


@router.get("/{payment_id}", response_model=SupplierPaymentResponse)
def get_supplier_payment(
    payment_id: int,
    db: Session = Depends(get_db)
):
    """Get supplier payment by ID"""
    service = SupplierPaymentService(db)
    payment = service.get_supplier_payment(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier payment not found"
        )
    return payment


@router.post("/{payment_id}/process")
def process_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Process supplier payment"""
    service = SupplierPaymentService(db)
    result = service.process_payment(payment_id, current_user_id)
    return {"message": "Payment processed successfully", "journal_id": result}


@router.post("/{payment_id}/reverse")
def reverse_payment(
    payment_id: int,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Reverse supplier payment"""
    service = SupplierPaymentService(db)
    result = service.reverse_payment(payment_id, reason, current_user_id)
    return {"message": "Payment reversed successfully", "reversal_id": result}


@router.get("/")
def search_supplier_payments(
    supplier_code: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search supplier payments"""
    service = SupplierPaymentService(db)
    result = service.search_supplier_payments(
        supplier_code=supplier_code,
        payment_method=payment_method,
        status=status,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )
    return result


@router.get("/{payment_id}/allocations")
def get_payment_allocations(
    payment_id: int,
    db: Session = Depends(get_db)
):
    """Get payment allocations"""
    service = SupplierPaymentService(db)
    allocations = service.get_payment_allocations(payment_id)
    return {"allocations": allocations}


@router.get("/supplier/{supplier_code}/outstanding")
def get_outstanding_invoices(
    supplier_code: str,
    db: Session = Depends(get_db)
):
    """Get outstanding invoices for supplier"""
    service = SupplierPaymentService(db)
    invoices = service.get_outstanding_invoices(supplier_code)
    return {"invoices": invoices}


@router.post("/payment-run")
def create_payment_run(
    supplier_codes: List[str] = Query(...),
    payment_date: date = Query(...),
    payment_method: str = Query(...),
    max_amount: Optional[Decimal] = Query(None),
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create payment run for multiple suppliers"""
    service = SupplierPaymentService(db)
    result = service.create_payment_run(
        supplier_codes=supplier_codes,
        payment_date=payment_date,
        payment_method=payment_method,
        max_amount=max_amount,
        user_id=current_user_id
    )
    return result


@router.get("/payment-analysis")
def get_payment_analysis(
    from_date: date = Query(...),
    to_date: date = Query(...),
    supplier_code: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get payment analysis report"""
    service = SupplierPaymentService(db)
    analysis = service.generate_payment_analysis(
        from_date=from_date,
        to_date=to_date,
        supplier_code=supplier_code
    )
    return analysis