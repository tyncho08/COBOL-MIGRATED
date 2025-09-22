"""
Sales Invoices API Router
Handles sales invoice management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query, status, Response
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.transactions import SalesInvoice, SalesInvoiceLine, InvoiceType
from app.models.users import User
from app.services.invoice_service import InvoiceService
from app.schemas.sales import SalesInvoiceCreate, SalesInvoiceUpdate, SalesInvoiceResponse

router = APIRouter(
    prefix="/sales-invoices",
    tags=["Sales Invoices"],
    responses={404: {"description": "Not found"}}
)


@router.get("/", response_model=List[SalesInvoiceResponse])
async def list_sales_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    customer_id: Optional[int] = None,
    invoice_type: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    is_paid: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List sales invoices with filtering and pagination"""
    service = InvoiceService(db)
    return service.list_invoices(
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        invoice_type=invoice_type,
        from_date=from_date,
        to_date=to_date,
        is_paid=is_paid
    )


@router.post("/", response_model=SalesInvoiceResponse)
async def create_sales_invoice(
    invoice_data: SalesInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new sales invoice"""
    service = InvoiceService(db)
    return service.create_invoice(invoice_data, current_user.id)


@router.get("/{invoice_id}", response_model=SalesInvoiceResponse)
async def get_sales_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sales invoice by ID"""
    service = InvoiceService(db)
    invoice = service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales invoice not found"
        )
    return invoice


@router.put("/{invoice_id}", response_model=SalesInvoiceResponse)
async def update_sales_invoice(
    invoice_id: int,
    invoice_data: SalesInvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update sales invoice"""
    service = InvoiceService(db)
    return service.update_invoice(invoice_id, invoice_data, current_user.id)


@router.post("/{invoice_id}/post")
async def post_invoice_to_gl(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Post invoice to General Ledger"""
    service = InvoiceService(db)
    return service.post_to_gl(invoice_id, current_user.id)


@router.post("/{invoice_id}/reverse")
async def reverse_sales_invoice(
    invoice_id: int,
    reason: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reverse sales invoice"""
    service = InvoiceService(db)
    return service.reverse_invoice(invoice_id, reason, current_user.id)


@router.get("/{invoice_id}/print")
async def print_sales_invoice(
    invoice_id: int,
    format: str = Query("pdf", regex="^(pdf|html|text)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Print/export sales invoice"""
    service = InvoiceService(db)
    return service.print_invoice(invoice_id, format)


@router.post("/{invoice_id}/email")
async def email_sales_invoice(
    invoice_id: int,
    email_to: str,
    subject: Optional[str] = None,
    message: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Email sales invoice to customer"""
    service = InvoiceService(db)
    return service.email_invoice(invoice_id, email_to, subject, message, current_user.id)


@router.get("/search", response_model=Dict[str, Any])
async def search_sales_invoices(
    customer_code: Optional[str] = None,
    invoice_number: Optional[str] = None,
    order_number: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search sales invoices"""
    service = InvoiceService(db)
    return service.search_invoices(
        customer_code=customer_code,
        invoice_number=invoice_number,
        order_number=order_number,
        page=page,
        page_size=page_size
    )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_invoice_statistics(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sales invoice statistics"""
    service = InvoiceService(db)
    return service.get_statistics(from_date, to_date, customer_id)


@router.get("/aging-report")
async def get_aging_report(
    as_of_date: Optional[date] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get aging report for outstanding invoices"""
    service = InvoiceService(db)
    return service.get_aging_report(as_of_date, customer_id)


@router.post("/batch-operations")
async def batch_operations(
    operation: str,
    invoice_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform batch operations on multiple invoices"""
    service = InvoiceService(db)
    return service.batch_operations(operation, invoice_ids, current_user.id)