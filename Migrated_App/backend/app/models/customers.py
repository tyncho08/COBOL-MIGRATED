"""
Customer Master Models
Migrated from ACAS Sales Ledger (fdsl.cob, slselsl.cob)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base, COMP3, CurrencyAmount, Percentage
from sqlalchemy.sql import func


class Customer(Base):
    """Customer Master Record - from fdsl.cob"""
    __tablename__ = "customers"
    
    # Primary key - 7 character customer code (6 digits + check digit)
    id = Column(Integer, primary_key=True)
    customer_code = Column(String(7), unique=True, nullable=False, index=True)
    
    # Basic Information
    customer_name = Column(String(60), nullable=False, index=True)
    address_line1 = Column(String(60))
    address_line2 = Column(String(60))
    address_line3 = Column(String(60))
    postcode = Column(String(10), index=True)
    country_code = Column(String(2), default="US")
    
    # Contact Information
    phone_number = Column(String(20))
    fax_number = Column(String(20))
    email_address = Column(String(100))
    website = Column(String(100))
    contact_name = Column(String(60))
    
    # Financial Information
    credit_limit = Column(CurrencyAmount(), default=0.00)
    payment_terms = Column(Integer, default=30)  # Days
    discount_percentage = Column(Percentage(), default=0.00)
    settlement_discount = Column(Percentage(), default=0.00)
    settlement_days = Column(Integer, default=0)
    
    # VAT/Tax Information
    vat_registration = Column(String(20))
    vat_code = Column(String(1), default="S")  # S=Standard, Z=Zero, E=Exempt
    ec_code = Column(String(1))  # European Community code
    
    # Account Status
    is_active = Column(Boolean, default=True)
    on_hold = Column(Boolean, default=False)
    cash_only = Column(Boolean, default=False)
    
    # Analysis Codes (for reporting)
    analysis_code1 = Column(String(10))
    analysis_code2 = Column(String(10))
    analysis_code3 = Column(String(10))
    
    # Financial Summary (updated by triggers)
    balance = Column(CurrencyAmount(), default=0.00)
    turnover_ytd = Column(CurrencyAmount(), default=0.00)
    turnover_last_year = Column(CurrencyAmount(), default=0.00)
    
    # Quarterly Turnover (ACAS feature)
    turnover_q1 = Column(CurrencyAmount(), default=0.00)
    turnover_q2 = Column(CurrencyAmount(), default=0.00)
    turnover_q3 = Column(CurrencyAmount(), default=0.00)
    turnover_q4 = Column(CurrencyAmount(), default=0.00)
    
    # Credit Control
    credit_rating = Column(String(1), default="A")  # A-E rating
    last_payment_date = Column(DateTime)
    last_invoice_date = Column(DateTime)
    average_payment_days = Column(Integer, default=30)
    
    # Additional Fields
    price_list_code = Column(String(10))
    sales_rep_code = Column(String(10))
    delivery_route = Column(String(10))
    invoice_copies = Column(Integer, default=1)
    statement_required = Column(Boolean, default=True)
    
    # Multi-currency support
    currency_code = Column(String(3), default="USD")
    
    # Notes
    notes = Column(String(500))
    
    # Audit fields
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    invoices = relationship("SalesInvoice", back_populates="customer")
    orders = relationship("SalesOrder", back_populates="customer")
    payments = relationship("CustomerPayment", back_populates="customer")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_customer_name", "customer_name"),
        Index("idx_customer_postcode", "postcode"),
        Index("idx_customer_balance", "balance"),
    )


class CustomerContact(Base):
    """Additional contacts for customer"""
    __tablename__ = "customer_contacts"
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    
    contact_name = Column(String(60), nullable=False)
    job_title = Column(String(60))
    department = Column(String(60))
    
    phone = Column(String(20))
    mobile = Column(String(20))
    email = Column(String(100))
    
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class CustomerCreditHistory(Base):
    """Credit history tracking"""
    __tablename__ = "customer_credit_history"
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    
    change_date = Column(DateTime, default=func.now())
    old_limit = Column(CurrencyAmount())
    new_limit = Column(CurrencyAmount())
    old_rating = Column(String(1))
    new_rating = Column(String(1))
    
    reason = Column(String(200))
    approved_by = Column(String(20))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(20))