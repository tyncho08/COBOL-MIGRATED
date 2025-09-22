"""
Purchase Invoices API Router
REST endpoints for purchase invoice management
"""
from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.purchase_ledger.purchase_invoice_service import PurchaseInvoiceService

router = APIRouter(prefix="/purchase-invoices", tags=["Purchase Invoices"])


# Pydantic models
class PurchaseInvoiceLineCreate(BaseModel):
    goods_receipt_line_id: Optional[int] = None
    stock_code: Optional[str] = None
    description: str
    quantity: Decimal
    unit_cost: Decimal
    vat_code: str = "S"
    analysis_code1: Optional[str] = None
    analysis_code2: Optional[str] = None


class PurchaseInvoiceCreate(BaseModel):
    supplier_code: str
    supplier_invoice_number: str
    invoice_lines: List[PurchaseInvoiceLineCreate]
    invoice_date: date
    due_date: Optional[date] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None


class PurchaseInvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    supplier_code: str
    supplier_invoice_number: str
    invoice_date: date
    due_date: Optional[date]
    invoice_status: str
    gross_amount: Decimal
    vat_amount: Decimal
    net_amount: Decimal
    outstanding_amount: Decimal
    notes: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", response_model=PurchaseInvoiceResponse)
def create_purchase_invoice(
    invoice_data: PurchaseInvoiceCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create new purchase invoice"""
    service = PurchaseInvoiceService(db)
    invoice = service.create_purchase_invoice(
        supplier_code=invoice_data.supplier_code,
        supplier_invoice_number=invoice_data.supplier_invoice_number,
        invoice_lines=[line.dict() for line in invoice_data.invoice_lines],
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        payment_terms=invoice_data.payment_terms,
        notes=invoice_data.notes,
        user_id=current_user_id
    )
    return invoice


@router.get("/{invoice_id}", response_model=PurchaseInvoiceResponse)
def get_purchase_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Get purchase invoice by ID"""
    service = PurchaseInvoiceService(db)
    invoice = service.get_purchase_invoice(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase invoice not found"
        )
    return invoice


@router.post("/{invoice_id}/match-receipts")
def match_invoice_to_receipts(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Match invoice to goods receipts"""
    service = PurchaseInvoiceService(db)
    matches = service.match_invoice_to_receipts(invoice_id, current_user_id)
    return {"message": "Invoice matched successfully", "matches": matches}


@router.post("/{invoice_id}/post")
def post_purchase_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Post purchase invoice to ledger"""
    service = PurchaseInvoiceService(db)
    result = service.post_invoice(invoice_id, current_user_id)
    return {"message": "Invoice posted successfully", "journal_id": result}


@router.post("/{invoice_id}/approve")
def approve_purchase_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Approve purchase invoice for payment"""
    service = PurchaseInvoiceService(db)
    invoice = service.approve_invoice(invoice_id, current_user_id)
    return {"message": "Invoice approved successfully"}


@router.get("/")
def search_purchase_invoices(
    supplier_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    due_from: Optional[date] = Query(None),
    due_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search purchase invoices"""
    service = PurchaseInvoiceService(db)
    result = service.search_purchase_invoices(
        supplier_code=supplier_code,
        status=status,
        from_date=from_date,
        to_date=to_date,
        due_from=due_from,
        due_to=due_to,
        page=page,
        page_size=page_size
    )
    return result


@router.get("/{invoice_id}/lines")
def get_purchase_invoice_lines(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Get purchase invoice lines"""
    service = PurchaseInvoiceService(db)
    lines = service.get_invoice_lines(invoice_id)
    return {"lines": lines}


@router.get("/aging-report")
def get_purchase_aging_report(
    as_at_date: date = Query(...),
    supplier_code: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get purchase ledger aging report"""
    service = PurchaseInvoiceService(db)
    report = service.generate_aging_report(as_at_date, supplier_code)
    return report


@router.get("/pending-approval")
def get_pending_approval(
    db: Session = Depends(get_db)
):
    """Get invoices pending approval"""
    service = PurchaseInvoiceService(db)
    invoices = service.get_pending_approval()
    return {"invoices": invoices}