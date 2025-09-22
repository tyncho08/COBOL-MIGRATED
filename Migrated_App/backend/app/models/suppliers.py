"""
Supplier Master Models (Purchase Ledger)
Migrated from ACAS Purchase Ledger COBOL structures
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base, COMP3, CurrencyAmount, Percentage
from sqlalchemy.sql import func


class Supplier(Base):
    """Supplier Master Record - from Purchase Ledger COBOL"""
    __tablename__ = "suppliers"
    
    # Primary key - 7 character supplier code
    id = Column(Integer, primary_key=True)
    supplier_code = Column(String(7), unique=True, nullable=False, index=True)
    
    # Basic Information
    supplier_name = Column(String(60), nullable=False, index=True)
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
    self_billing = Column(Boolean, default=False)
    
    # Account Status
    is_active = Column(Boolean, default=True)
    on_hold = Column(Boolean, default=False)
    approval_required = Column(Boolean, default=False)
    
    # Analysis Codes (for reporting)
    analysis_code1 = Column(String(10))
    analysis_code2 = Column(String(10))
    analysis_code3 = Column(String(10))
    
    # Financial Summary (updated by triggers)
    balance = Column(CurrencyAmount(), default=0.00)
    turnover_ytd = Column(CurrencyAmount(), default=0.00)
    turnover_last_year = Column(CurrencyAmount(), default=0.00)
    
    # Payment Information
    bank_name = Column(String(60))
    bank_account = Column(String(30))
    bank_sort_code = Column(String(10))
    payment_method = Column(String(20), default="CHECK")
    
    # Multi-currency support
    currency_code = Column(String(3), default="USD")
    
    # Lead Times
    lead_time_days = Column(Integer, default=7)
    minimum_order_value = Column(CurrencyAmount(), default=0.00)
    
    # Notes
    notes = Column(String(500))
    
    # Audit fields
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    purchase_invoices = relationship("PurchaseInvoice", back_populates="supplier")
    payments = relationship("SupplierPayment", back_populates="supplier")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_supplier_name", "supplier_name"),
        Index("idx_supplier_postcode", "postcode"),
        Index("idx_supplier_balance", "balance"),
    )