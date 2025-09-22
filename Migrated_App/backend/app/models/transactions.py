"""
Transaction Models
Migrated from ACAS transaction files (invoices, orders, payments)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.config.database import Base, COMP3, CurrencyAmount, Percentage, ExchangeRate
from sqlalchemy.sql import func


class TransactionStatus(str, enum.Enum):
    """Transaction status values"""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"
    REVERSED = "REVERSED"


class InvoiceType(str, enum.Enum):
    """Invoice types"""
    INVOICE = "INVOICE"
    CREDIT_NOTE = "CREDIT_NOTE"
    DEBIT_NOTE = "DEBIT_NOTE"
    PROFORMA = "PROFORMA"


# Sales Transactions

class SalesOrder(Base):
    """Sales Order Header"""
    __tablename__ = "sales_orders"
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(20), unique=True, nullable=False, index=True)
    order_date = Column(DateTime, nullable=False, default=func.now())
    
    # Customer
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    delivery_name = Column(String(60))
    delivery_address1 = Column(String(60))
    delivery_address2 = Column(String(60))
    delivery_address3 = Column(String(60))
    delivery_postcode = Column(String(10))
    
    # Order Details
    customer_reference = Column(String(30))
    sales_rep = Column(String(10))
    order_status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    
    # Dates
    required_date = Column(DateTime)
    promised_date = Column(DateTime)
    shipped_date = Column(DateTime)
    
    # Financial
    currency_code = Column(String(3), default="USD")
    exchange_rate = Column(ExchangeRate(), default=1.000000)
    
    # Totals (calculated)
    goods_total = Column(CurrencyAmount(), default=0.00)
    discount_total = Column(CurrencyAmount(), default=0.00)
    net_total = Column(CurrencyAmount(), default=0.00)
    vat_total = Column(CurrencyAmount(), default=0.00)
    gross_total = Column(CurrencyAmount(), default=0.00)
    
    # Flags
    is_exported = Column(Boolean, default=False)
    is_delivered = Column(Boolean, default=False)
    is_invoiced = Column(Boolean, default=False)
    has_backorders = Column(Boolean, default=False)
    
    # Notes
    notes = Column(String(500))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    customer = relationship("Customer", back_populates="orders")
    order_lines = relationship("SalesOrderLine", back_populates="order", cascade="all, delete-orphan")


class SalesOrderLine(Base):
    """Sales Order Lines"""
    __tablename__ = "sales_order_lines"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    line_number = Column(Integer, nullable=False)
    
    # Item
    stock_id = Column(Integer, ForeignKey("stock_items.id"))
    stock_code = Column(String(13))
    description = Column(String(60), nullable=False)
    
    # Quantities
    quantity_ordered = Column(COMP3(15, 3), nullable=False)
    quantity_allocated = Column(COMP3(15, 3), default=0.000)
    quantity_delivered = Column(COMP3(15, 3), default=0.000)
    quantity_invoiced = Column(COMP3(15, 3), default=0.000)
    quantity_back_order = Column(COMP3(15, 3), default=0.000)
    
    # Pricing
    unit_price = Column(CurrencyAmount(), nullable=False)
    discount_percent = Column(Percentage(), default=0.00)
    discount_amount = Column(CurrencyAmount(), default=0.00)
    net_amount = Column(CurrencyAmount(), nullable=False)
    vat_code = Column(String(1), default="S")
    vat_rate = Column(Percentage())
    vat_amount = Column(CurrencyAmount())
    
    # Status
    line_status = Column(String(20), default="OPEN")  # OPEN, PARTIAL, COMPLETE, CANCELLED
    
    # Delivery
    promised_date = Column(DateTime)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    order = relationship("SalesOrder", back_populates="order_lines")
    stock_item = relationship("StockItem", back_populates="order_lines")
    
    # Indexes
    __table_args__ = (
        Index("idx_order_line", "order_id", "line_number"),
    )


class SalesInvoice(Base):
    """Sales Invoice Header"""
    __tablename__ = "sales_invoices"
    
    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(20), unique=True, nullable=False, index=True)
    invoice_date = Column(DateTime, nullable=False, default=func.now())
    invoice_type = Column(Enum(InvoiceType), default=InvoiceType.INVOICE)
    
    # Customer
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    customer_code = Column(String(7), nullable=False)
    customer_name = Column(String(60), nullable=False)
    
    # Delivery Address (captured at invoice time)
    delivery_name = Column(String(60))
    delivery_address1 = Column(String(60))
    delivery_address2 = Column(String(60))
    delivery_address3 = Column(String(60))
    delivery_postcode = Column(String(10))
    
    # References
    customer_reference = Column(String(30))
    order_number = Column(String(20))
    delivery_note = Column(String(20))
    
    # Financial
    currency_code = Column(String(3), default="USD")
    exchange_rate = Column(ExchangeRate(), default=1.000000)
    
    # Terms
    payment_terms = Column(Integer, default=30)
    due_date = Column(DateTime)
    settlement_discount = Column(Percentage(), default=0.00)
    settlement_days = Column(Integer, default=0)
    
    # Totals
    goods_total = Column(CurrencyAmount(), nullable=False)
    discount_total = Column(CurrencyAmount(), default=0.00)
    net_total = Column(CurrencyAmount(), nullable=False)
    vat_total = Column(CurrencyAmount(), default=0.00)
    gross_total = Column(CurrencyAmount(), nullable=False)
    
    # Payment Status
    amount_paid = Column(CurrencyAmount(), default=0.00)
    balance = Column(CurrencyAmount())
    is_paid = Column(Boolean, default=False)
    
    # GL Posting
    period_number = Column(Integer)
    gl_posted = Column(Boolean, default=False)
    gl_batch_number = Column(String(20))
    
    # Status
    invoice_status = Column(Enum(TransactionStatus), default=TransactionStatus.POSTED)
    
    # Print/Export
    print_count = Column(Integer, default=0)
    is_exported = Column(Boolean, default=False)
    
    # Notes
    notes = Column(String(500))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    invoice_lines = relationship("SalesInvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("PaymentAllocation", back_populates="invoice")


class SalesInvoiceLine(Base):
    """Sales Invoice Lines"""
    __tablename__ = "sales_invoice_lines"
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("sales_invoices.id"), nullable=False)
    line_number = Column(Integer, nullable=False)
    
    # Item
    stock_id = Column(Integer, ForeignKey("stock_items.id"))
    stock_code = Column(String(13))
    description = Column(String(60), nullable=False)
    
    # Quantity and Pricing
    quantity = Column(COMP3(15, 3), nullable=False)
    unit_price = Column(CurrencyAmount(), nullable=False)
    discount_percent = Column(Percentage(), default=0.00)
    discount_amount = Column(CurrencyAmount(), default=0.00)
    net_amount = Column(CurrencyAmount(), nullable=False)
    
    # VAT/Tax
    vat_code = Column(String(1), default="S")
    vat_rate = Column(Percentage())
    vat_amount = Column(CurrencyAmount())
    
    # Cost (for margin calculation)
    unit_cost = Column(CurrencyAmount())
    
    # GL Coding
    gl_account = Column(String(8))
    analysis_code1 = Column(String(10))
    analysis_code2 = Column(String(10))
    analysis_code3 = Column(String(10))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    invoice = relationship("SalesInvoice", back_populates="invoice_lines")
    stock_item = relationship("StockItem", back_populates="invoice_lines")
    
    # Indexes
    __table_args__ = (
        Index("idx_invoice_line", "invoice_id", "line_number"),
    )


class CustomerPayment(Base):
    """Customer Payment/Receipt"""
    __tablename__ = "customer_payments"
    
    id = Column(Integer, primary_key=True)
    payment_number = Column(String(20), unique=True, nullable=False, index=True)
    payment_date = Column(DateTime, nullable=False, default=func.now())
    
    # Customer
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    customer_code = Column(String(7), nullable=False)
    
    # Payment Details
    payment_method = Column(String(20), nullable=False)  # CASH, CHECK, CARD, TRANSFER
    reference = Column(String(30))
    
    # Amounts
    currency_code = Column(String(3), default="USD")
    payment_amount = Column(CurrencyAmount(), nullable=False)
    allocated_amount = Column(CurrencyAmount(), default=0.00)
    unallocated_amount = Column(CurrencyAmount())
    
    # Bank Details
    bank_account = Column(String(20))
    bank_reference = Column(String(30))
    
    # GL Posting
    period_number = Column(Integer)
    gl_posted = Column(Boolean, default=False)
    gl_batch_number = Column(String(20))
    
    # Status
    is_allocated = Column(Boolean, default=False)
    is_reversed = Column(Boolean, default=False)
    
    # Notes
    notes = Column(String(500))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    customer = relationship("Customer", back_populates="payments")
    allocations = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan")


class PaymentAllocation(Base):
    """Payment to Invoice Allocation"""
    __tablename__ = "payment_allocations"
    
    id = Column(Integer, primary_key=True)
    payment_id = Column(Integer, ForeignKey("customer_payments.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("sales_invoices.id"), nullable=False)
    
    allocation_date = Column(DateTime, default=func.now())
    allocated_amount = Column(CurrencyAmount(), nullable=False)
    discount_taken = Column(CurrencyAmount(), default=0.00)
    
    # Exchange difference (multi-currency)
    exchange_difference = Column(CurrencyAmount(), default=0.00)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(20))
    
    # Relationships
    payment = relationship("CustomerPayment", back_populates="allocations")
    invoice = relationship("SalesInvoice", back_populates="payments")
    
    # Indexes
    __table_args__ = (
        Index("idx_allocation_payment", "payment_id"),
        Index("idx_allocation_invoice", "invoice_id"),
    )