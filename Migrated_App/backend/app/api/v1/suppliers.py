"""
Suppliers API Router
REST endpoints for supplier management
"""
from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


# Pydantic models
class SupplierCreate(BaseModel):
    supplier_code: str
    supplier_name: str
    contact_person: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str = "USA"
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    payment_terms: str = "30 DAYS"
    currency_code: str = "USD"
    vat_registration: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    notes: Optional[str] = None


class SupplierUpdate(BaseModel):
    supplier_name: Optional[str] = None
    contact_person: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    payment_terms: Optional[str] = None
    currency_code: Optional[str] = None
    vat_registration: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(BaseModel):
    id: int
    supplier_code: str
    supplier_name: str
    contact_person: Optional[str]
    address_line1: str
    city: str
    postal_code: str
    country: str
    phone: Optional[str]
    email: Optional[str]
    payment_terms: str
    currency_code: str
    balance: Decimal
    credit_limit: Optional[Decimal]
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=SupplierResponse)
def create_supplier(
    supplier_data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create new supplier"""
    from app.models.suppliers import Supplier
    
    # Check for duplicate
    existing = db.query(Supplier).filter(
        Supplier.supplier_code == supplier_data.supplier_code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supplier code {supplier_data.supplier_code} already exists"
        )
    
    supplier = Supplier(
        **supplier_data.dict(),
        balance=Decimal("0"),
        is_active=True,
        created_by=str(current_user_id)
    )
    
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    
    return supplier


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db)
):
    """Get supplier by ID"""
    from app.models.suppliers import Supplier
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    return supplier


@router.get("/by-code/{supplier_code}", response_model=SupplierResponse)
def get_supplier_by_code(
    supplier_code: str,
    db: Session = Depends(get_db)
):
    """Get supplier by code"""
    from app.models.suppliers import Supplier
    supplier = db.query(Supplier).filter(Supplier.supplier_code == supplier_code).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    supplier_data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Update supplier"""
    from app.models.suppliers import Supplier
    from datetime import datetime
    
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    # Update fields
    for field, value in supplier_data.dict(exclude_unset=True).items():
        setattr(supplier, field, value)
    
    supplier.updated_at = datetime.now()
    supplier.updated_by = str(current_user_id)
    
    db.commit()
    db.refresh(supplier)
    
    return supplier


@router.get("/")
def search_suppliers(
    search_term: Optional[str] = Query(None),
    active_only: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search suppliers"""
    from app.models.suppliers import Supplier
    from sqlalchemy import or_
    
    query = db.query(Supplier)
    
    if active_only:
        query = query.filter(Supplier.is_active == True)
    
    if search_term:
        query = query.filter(
            or_(
                Supplier.supplier_code.ilike(f"%{search_term}%"),
                Supplier.supplier_name.ilike(f"%{search_term}%")
            )
        )
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    suppliers = query.order_by(Supplier.supplier_code)\
                    .offset((page - 1) * page_size)\
                    .limit(page_size)\
                    .all()
    
    return {
        "suppliers": suppliers,
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size
    }


@router.get("/{supplier_id}/balance")
def get_supplier_balance(
    supplier_id: int,
    as_at_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get supplier balance"""
    from app.models.suppliers import Supplier
    from app.models.purchase_transactions import PurchaseInvoice, SupplierPayment
    from sqlalchemy import func, and_
    
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Calculate outstanding invoices
    invoice_query = db.query(func.sum(PurchaseInvoice.outstanding_amount)).filter(
        PurchaseInvoice.supplier_id == supplier_id
    )
    
    if as_at_date:
        invoice_query = invoice_query.filter(PurchaseInvoice.invoice_date <= as_at_date)
    
    outstanding_invoices = invoice_query.scalar() or Decimal("0")
    
    return {
        "supplier_code": supplier.supplier_code,
        "supplier_name": supplier.supplier_name,
        "current_balance": supplier.balance,
        "outstanding_invoices": outstanding_invoices,
        "credit_limit": supplier.credit_limit,
        "available_credit": (supplier.credit_limit - outstanding_invoices) if supplier.credit_limit else None,
        "as_at_date": as_at_date or date.today()
    }


@router.get("/{supplier_id}/transactions")
def get_supplier_transactions(
    supplier_id: int,
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    transaction_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get supplier transaction history"""
    from app.models.purchase_transactions import PurchaseInvoice, SupplierPayment
    from sqlalchemy import union_all, and_
    
    # Build invoice query
    invoice_query = db.query(
        PurchaseInvoice.invoice_date.label("date"),
        PurchaseInvoice.invoice_number.label("reference"),
        PurchaseInvoice.net_amount.label("amount"),
        "INVOICE".label("type"),
        PurchaseInvoice.invoice_status.label("status")
    ).filter(PurchaseInvoice.supplier_id == supplier_id)
    
    # Build payment query
    payment_query = db.query(
        SupplierPayment.payment_date.label("date"),
        SupplierPayment.payment_number.label("reference"),
        (-SupplierPayment.payment_amount).label("amount"),
        "PAYMENT".label("type"),
        SupplierPayment.payment_status.label("status")
    ).filter(SupplierPayment.supplier_id == supplier_id)
    
    # Apply date filters
    if from_date:
        invoice_query = invoice_query.filter(PurchaseInvoice.invoice_date >= from_date)
        payment_query = payment_query.filter(SupplierPayment.payment_date >= from_date)
    
    if to_date:
        invoice_query = invoice_query.filter(PurchaseInvoice.invoice_date <= to_date)
        payment_query = payment_query.filter(SupplierPayment.payment_date <= to_date)
    
    # Apply transaction type filter
    if transaction_type == "INVOICE":
        query = invoice_query
    elif transaction_type == "PAYMENT":
        query = payment_query
    else:
        query = union_all(invoice_query, payment_query)
    
    # Apply pagination and ordering
    transactions = query.order_by("date DESC").offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "transactions": [
            {
                "date": t.date,
                "reference": t.reference,
                "amount": t.amount,
                "type": t.type,
                "status": t.status
            }
            for t in transactions
        ]
    }