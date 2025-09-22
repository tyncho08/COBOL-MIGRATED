"""
Customers API Router
REST endpoints for customer management
"""
from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db

router = APIRouter(prefix="/customers", tags=["Customers"])


# Pydantic models
class CustomerCreate(BaseModel):
    customer_code: str
    customer_name: str
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
    discount_percent: Optional[Decimal] = Decimal("0")
    sales_rep_code: Optional[str] = None
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = None
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
    discount_percent: Optional[Decimal] = None
    sales_rep_code: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(BaseModel):
    id: int
    customer_code: str
    customer_name: str
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
    discount_percent: Decimal
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=CustomerResponse)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create new customer"""
    from app.models.customers import Customer
    
    # Check for duplicate
    existing = db.query(Customer).filter(
        Customer.customer_code == customer_data.customer_code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer code {customer_data.customer_code} already exists"
        )
    
    customer = Customer(
        **customer_data.dict(),
        balance=Decimal("0"),
        is_active=True,
        created_by=str(current_user_id)
    )
    
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """Get customer by ID"""
    from app.models.customers import Customer
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return customer


@router.get("/by-code/{customer_code}", response_model=CustomerResponse)
def get_customer_by_code(
    customer_code: str,
    db: Session = Depends(get_db)
):
    """Get customer by code"""
    from app.models.customers import Customer
    customer = db.query(Customer).filter(Customer.customer_code == customer_code).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Update customer"""
    from app.models.customers import Customer
    from datetime import datetime
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Update fields
    for field, value in customer_data.dict(exclude_unset=True).items():
        setattr(customer, field, value)
    
    customer.updated_at = datetime.now()
    customer.updated_by = str(current_user_id)
    
    db.commit()
    db.refresh(customer)
    
    return customer


@router.get("/")
def search_customers(
    search_term: Optional[str] = Query(None),
    active_only: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search customers"""
    from app.models.customers import Customer
    from sqlalchemy import or_
    
    query = db.query(Customer)
    
    if active_only:
        query = query.filter(Customer.is_active == True)
    
    if search_term:
        query = query.filter(
            or_(
                Customer.customer_code.ilike(f"%{search_term}%"),
                Customer.customer_name.ilike(f"%{search_term}%")
            )
        )
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    customers = query.order_by(Customer.customer_code)\
                    .offset((page - 1) * page_size)\
                    .limit(page_size)\
                    .all()
    
    return {
        "customers": customers,
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size
    }


@router.get("/{customer_id}/balance")
def get_customer_balance(
    customer_id: int,
    as_at_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get customer balance"""
    from app.models.customers import Customer
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # For now, return basic balance - in full implementation would calculate
    # from sales invoices and customer payments
    return {
        "customer_code": customer.customer_code,
        "customer_name": customer.customer_name,
        "current_balance": customer.balance,
        "credit_limit": customer.credit_limit,
        "available_credit": (customer.credit_limit - customer.balance) if customer.credit_limit else None,
        "as_at_date": as_at_date or date.today()
    }


@router.get("/{customer_id}/credit-check")
def perform_credit_check(
    customer_id: int,
    order_amount: Decimal = Query(...),
    db: Session = Depends(get_db)
):
    """Perform credit check for customer"""
    from app.models.customers import Customer
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer.credit_limit:
        return {
            "customer_code": customer.customer_code,
            "credit_approved": True,
            "reason": "No credit limit set"
        }
    
    total_exposure = customer.balance + order_amount
    credit_available = customer.credit_limit - customer.balance
    
    approved = total_exposure <= customer.credit_limit
    
    return {
        "customer_code": customer.customer_code,
        "customer_name": customer.customer_name,
        "order_amount": order_amount,
        "current_balance": customer.balance,
        "credit_limit": customer.credit_limit,
        "credit_available": credit_available,
        "total_exposure": total_exposure,
        "credit_approved": approved,
        "reason": "Approved" if approved else f"Exceeds credit limit by {total_exposure - customer.credit_limit}"
    }