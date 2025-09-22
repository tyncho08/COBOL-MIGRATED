"""
Control and Master Tables
Additional tables for system control and configuration
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, JSON, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base, CurrencyAmount, Percentage, ExchangeRate
from sqlalchemy.sql import func


# Analysis Codes

class AnalysisCodeMaster(Base):
    """Analysis Code Master - for multi-dimensional reporting"""
    __tablename__ = "analysis_code_master"
    
    id = Column(Integer, primary_key=True)
    dimension_number = Column(Integer, nullable=False)  # 1, 2, or 3
    code = Column(String(10), nullable=False)
    description = Column(String(60), nullable=False)
    
    # Hierarchy
    parent_code = Column(String(10))
    level = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Valid From/To
    valid_from = Column(DateTime, default=func.now())
    valid_to = Column(DateTime)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Unique constraint
    __table_args__ = (
        Index("idx_analysis_code", "dimension_number", "code", unique=True),
    )


# VAT/Tax Codes

class VATCodeMaster(Base):
    """VAT/Tax Code Master"""
    __tablename__ = "vat_code_master"
    
    id = Column(Integer, primary_key=True)
    vat_code = Column(String(1), unique=True, nullable=False)
    description = Column(String(60), nullable=False)
    
    # Rates
    current_rate = Column(Percentage(), nullable=False)
    
    # GL Accounts
    input_vat_account = Column(String(8))   # Purchase VAT
    output_vat_account = Column(String(8))  # Sales VAT
    
    # Type
    vat_type = Column(String(20))  # STANDARD, REDUCED, ZERO, EXEMPT
    is_reverse_charge = Column(Boolean, default=False)
    is_ec = Column(Boolean, default=False)  # European Community
    
    # Reporting
    vat_return_box = Column(String(10))  # Box on VAT return
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))


class VATRateHistory(Base):
    """VAT Rate History for historical transactions"""
    __tablename__ = "vat_rate_history"
    
    id = Column(Integer, primary_key=True)
    vat_code = Column(String(1), ForeignKey("vat_code_master.vat_code"), nullable=False)
    effective_date = Column(DateTime, nullable=False)
    rate = Column(Percentage(), nullable=False)
    
    # End date (null for current rate)
    end_date = Column(DateTime)
    
    # Reason for change
    change_reason = Column(String(200))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(20))
    
    # Index
    __table_args__ = (
        Index("idx_vat_history", "vat_code", "effective_date"),
    )


# Currency Exchange

class Currency(Base):
    """Currency Master"""
    __tablename__ = "currencies"
    
    id = Column(Integer, primary_key=True)
    currency_code = Column(String(3), unique=True, nullable=False)
    currency_name = Column(String(60), nullable=False)
    symbol = Column(String(5))
    
    # Decimal places
    decimal_places = Column(Integer, default=2)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_base = Column(Boolean, default=False)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ExchangeRateHistory(Base):
    """Exchange Rate History"""
    __tablename__ = "exchange_rate_history"
    
    id = Column(Integer, primary_key=True)
    from_currency = Column(String(3), ForeignKey("currencies.currency_code"), nullable=False)
    to_currency = Column(String(3), ForeignKey("currencies.currency_code"), nullable=False)
    effective_date = Column(DateTime, nullable=False)
    
    # Rates
    exchange_rate = Column(ExchangeRate(), nullable=False)
    inverse_rate = Column(ExchangeRate())
    
    # Source
    rate_source = Column(String(30))  # BANK, OFFICIAL, MANUAL
    
    # Status
    is_month_end = Column(Boolean, default=False)
    is_year_end = Column(Boolean, default=False)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(20))
    
    # Index
    __table_args__ = (
        Index("idx_exchange_rate", "from_currency", "to_currency", "effective_date"),
    )


# Delivery and Shipping

class DeliveryNote(Base):
    """Delivery Notes"""
    __tablename__ = "delivery_notes"
    
    id = Column(Integer, primary_key=True)
    delivery_number = Column(String(20), unique=True, nullable=False, index=True)
    delivery_date = Column(DateTime, nullable=False)
    
    # Type
    delivery_type = Column(String(20))  # SALES, PURCHASE, TRANSFER
    
    # References
    order_type = Column(String(20))  # SALES_ORDER, PURCHASE_ORDER
    order_id = Column(Integer)
    
    # Customer/Supplier
    entity_type = Column(String(20))  # CUSTOMER, SUPPLIER
    entity_id = Column(Integer)
    entity_name = Column(String(60))
    
    # Delivery Address
    delivery_name = Column(String(60))
    delivery_address1 = Column(String(60))
    delivery_address2 = Column(String(60))
    delivery_address3 = Column(String(60))
    delivery_postcode = Column(String(10))
    
    # Shipping
    carrier = Column(String(60))
    tracking_number = Column(String(50))
    shipping_method = Column(String(30))
    
    # Status
    is_delivered = Column(Boolean, default=False)
    delivered_date = Column(DateTime)
    received_by = Column(String(60))
    
    # Items Count
    total_lines = Column(Integer, default=0)
    total_quantity = Column(Numeric(15, 3), default=0.000)
    
    # Notes
    notes = Column(String(500))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))


# Back Orders

class BackOrder(Base):
    """Back Order Management"""
    __tablename__ = "back_orders"
    
    id = Column(Integer, primary_key=True)
    back_order_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Original Order
    order_type = Column(String(20))  # SALES, PURCHASE
    order_id = Column(Integer)
    order_line_id = Column(Integer)
    
    # Customer/Supplier
    entity_type = Column(String(20))
    entity_id = Column(Integer)
    entity_code = Column(String(7))
    entity_name = Column(String(60))
    
    # Item
    stock_id = Column(Integer, ForeignKey("stock_items.id"))
    stock_code = Column(String(13))
    description = Column(String(60))
    
    # Quantities
    ordered_quantity = Column(Numeric(15, 3), nullable=False)
    allocated_quantity = Column(Numeric(15, 3), default=0.000)
    outstanding_quantity = Column(Numeric(15, 3))
    
    # Dates
    order_date = Column(DateTime, nullable=False)
    required_date = Column(DateTime)
    expected_date = Column(DateTime)
    
    # Price (locked at order time)
    unit_price = Column(CurrencyAmount())
    discount_percent = Column(Percentage())
    
    # Priority
    priority = Column(Integer, default=5)  # 1-10, 1 is highest
    
    # Status
    status = Column(String(20), default="OPEN")  # OPEN, PARTIAL, FULFILLED, CANCELLED
    
    # Notes
    notes = Column(String(500))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    stock_item = relationship("StockItem")
    
    # Indexes
    __table_args__ = (
        Index("idx_backorder_stock", "stock_id"),
        Index("idx_backorder_entity", "entity_type", "entity_id"),
        Index("idx_backorder_status", "status"),
    )


# Number Sequences

class NumberSequence(Base):
    """Configurable Number Sequences"""
    __tablename__ = "number_sequences"
    
    id = Column(Integer, primary_key=True)
    sequence_type = Column(String(30), unique=True, nullable=False)
    
    # Format
    prefix = Column(String(10), default="")
    suffix = Column(String(10), default="")
    current_number = Column(Integer, nullable=False)
    min_digits = Column(Integer, default=6)
    
    # Reset
    reset_frequency = Column(String(20))  # NEVER, MONTHLY, YEARLY
    last_reset_date = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    updated_by = Column(String(20))


# Document Attachments

class DocumentAttachment(Base):
    """Document Attachments for any record"""
    __tablename__ = "document_attachments"
    
    id = Column(Integer, primary_key=True)
    
    # Reference to any table
    table_name = Column(String(50), nullable=False, index=True)
    record_id = Column(String(50), nullable=False, index=True)
    
    # File Information
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    file_path = Column(String(500))
    
    # Document Type
    document_type = Column(String(30))  # INVOICE, RECEIPT, CONTRACT, etc.
    description = Column(String(200))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Audit
    uploaded_at = Column(DateTime, default=func.now())
    uploaded_by = Column(String(20))


# Email Queue

class EmailQueue(Base):
    """Email Queue for async sending"""
    __tablename__ = "email_queue"
    
    id = Column(Integer, primary_key=True)
    
    # Email Details
    to_email = Column(String(255), nullable=False)
    cc_email = Column(String(500))
    bcc_email = Column(String(500))
    from_email = Column(String(255))
    subject = Column(String(255), nullable=False)
    body = Column(String(5000))
    body_html = Column(String(5000))
    
    # Attachments (JSON array)
    attachments = Column(JSON)
    
    # Reference
    reference_type = Column(String(30))  # INVOICE, STATEMENT, etc.
    reference_id = Column(String(50))
    
    # Status
    status = Column(String(20), default="PENDING")  # PENDING, SENT, FAILED
    attempts = Column(Integer, default=0)
    last_attempt = Column(DateTime)
    sent_date = Column(DateTime)
    error_message = Column(String(500))
    
    # Priority
    priority = Column(Integer, default=5)  # 1-10, 1 is highest
    
    # Scheduled
    scheduled_date = Column(DateTime)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    
    # Indexes
    __table_args__ = (
        Index("idx_email_status", "status", "priority"),
        Index("idx_email_reference", "reference_type", "reference_id"),
    )