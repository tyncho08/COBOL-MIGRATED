"""
Purchase Transaction Models
Migrated from ACAS Purchase Ledger COBOL structures
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.config.database import Base, COMP3, CurrencyAmount, Percentage, ExchangeRate
from sqlalchemy.sql import func


class PurchaseOrderStatus(str, enum.Enum):
    """Purchase order status values"""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    PARTIAL = "PARTIAL"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"


class GoodsReceiptStatus(str, enum.Enum):
    """Goods receipt status"""
    PENDING = "PENDING"
    RECEIVED = "RECEIVED"
    INSPECTED = "INSPECTED"
    REJECTED = "REJECTED"
    POSTED = "POSTED"


# Purchase Orders

class PurchaseOrder(Base):
    """Purchase Order Header - from COBOL pl800/pl900"""
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(20), unique=True, nullable=False, index=True)
    order_date = Column(DateTime, nullable=False, default=func.now())
    
    # Supplier
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    supplier_reference = Column(String(30))
    
    # Order Details
    buyer_code = Column(String(10))
    department = Column(String(10))
    order_status = Column(Enum(PurchaseOrderStatus), default=PurchaseOrderStatus.DRAFT)
    
    # Delivery
    delivery_address1 = Column(String(60))
    delivery_address2 = Column(String(60))
    delivery_address3 = Column(String(60))
    delivery_postcode = Column(String(10))
    expected_date = Column(DateTime)
    
    # Financial
    currency_code = Column(String(3), default="USD")
    exchange_rate = Column(ExchangeRate(), default=1.000000)
    
    # Totals
    goods_total = Column(CurrencyAmount(), default=0.00)
    discount_total = Column(CurrencyAmount(), default=0.00)
    net_total = Column(CurrencyAmount(), default=0.00)
    vat_total = Column(CurrencyAmount(), default=0.00)
    gross_total = Column(CurrencyAmount(), default=0.00)
    
    # Approval
    approval_required = Column(Boolean, default=False)
    approved_by = Column(String(20))
    approved_date = Column(DateTime)
    approval_limit = Column(CurrencyAmount())
    
    # Flags
    is_printed = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    is_complete = Column(Boolean, default=False)
    has_receipts = Column(Boolean, default=False)
    
    # Notes
    notes = Column(String(500))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    supplier = relationship("Supplier", back_populates="purchase_orders")
    order_lines = relationship("PurchaseOrderLine", back_populates="order", cascade="all, delete-orphan")
    goods_receipts = relationship("GoodsReceipt", back_populates="purchase_order")


class PurchaseOrderLine(Base):
    """Purchase Order Lines"""
    __tablename__ = "purchase_order_lines"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    line_number = Column(Integer, nullable=False)
    
    # Item
    stock_id = Column(Integer, ForeignKey("stock_items.id"))
    stock_code = Column(String(13))
    supplier_ref = Column(String(20))
    description = Column(String(60), nullable=False)
    
    # Quantities
    quantity_ordered = Column(COMP3(15, 3), nullable=False)
    quantity_received = Column(COMP3(15, 3), default=0.000)
    quantity_invoiced = Column(COMP3(15, 3), default=0.000)
    quantity_outstanding = Column(COMP3(15, 3))
    
    # Pricing
    unit_price = Column(CurrencyAmount(), nullable=False)
    discount_percent = Column(Percentage(), default=0.00)
    discount_amount = Column(CurrencyAmount(), default=0.00)
    net_amount = Column(CurrencyAmount(), nullable=False)
    vat_code = Column(String(1), default="S")
    vat_rate = Column(Percentage())
    vat_amount = Column(CurrencyAmount())
    
    # Delivery
    expected_date = Column(DateTime)
    
    # GL Coding
    gl_account = Column(String(8))
    analysis_code1 = Column(String(10))
    analysis_code2 = Column(String(10))
    analysis_code3 = Column(String(10))
    
    # Status
    line_status = Column(String(20), default="OPEN")
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    order = relationship("PurchaseOrder", back_populates="order_lines")
    stock_item = relationship("StockItem")
    
    # Indexes
    __table_args__ = (
        Index("idx_po_line", "order_id", "line_number"),
    )


# Goods Receipts

class GoodsReceipt(Base):
    """Goods Receipt Note - from COBOL pl100/pl115"""
    __tablename__ = "goods_receipts"
    
    id = Column(Integer, primary_key=True)
    receipt_number = Column(String(20), unique=True, nullable=False, index=True)
    receipt_date = Column(DateTime, nullable=False, default=func.now())
    
    # References
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    delivery_note = Column(String(30))
    
    # Receipt Details
    received_by = Column(String(20))
    receipt_status = Column(Enum(GoodsReceiptStatus), default=GoodsReceiptStatus.PENDING)
    inspection_date = Column(DateTime)
    inspected_by = Column(String(20))
    
    # Totals
    total_lines = Column(Integer, default=0)
    total_quantity = Column(COMP3(15, 3), default=0.000)
    
    # Posting
    posted_to_stock = Column(Boolean, default=False)
    stock_posting_date = Column(DateTime)
    invoice_matched = Column(Boolean, default=False)
    
    # Notes
    notes = Column(String(500))
    rejection_reason = Column(String(200))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    supplier = relationship("Supplier")
    purchase_order = relationship("PurchaseOrder", back_populates="goods_receipts")
    receipt_lines = relationship("GoodsReceiptLine", back_populates="receipt", cascade="all, delete-orphan")


class GoodsReceiptLine(Base):
    """Goods Receipt Lines"""
    __tablename__ = "goods_receipt_lines"
    
    id = Column(Integer, primary_key=True)
    receipt_id = Column(Integer, ForeignKey("goods_receipts.id"), nullable=False)
    line_number = Column(Integer, nullable=False)
    
    # References
    po_line_id = Column(Integer, ForeignKey("purchase_order_lines.id"))
    
    # Item
    stock_id = Column(Integer, ForeignKey("stock_items.id"))
    stock_code = Column(String(13))
    description = Column(String(60), nullable=False)
    
    # Quantities
    quantity_ordered = Column(COMP3(15, 3))
    quantity_received = Column(COMP3(15, 3), nullable=False)
    quantity_accepted = Column(COMP3(15, 3))
    quantity_rejected = Column(COMP3(15, 3), default=0.000)
    
    # Location
    location_code = Column(String(20))
    bin_number = Column(String(20))
    
    # Quality
    inspection_result = Column(String(20))  # PASS, FAIL, PARTIAL
    rejection_reason = Column(String(200))
    
    # Batch/Serial
    batch_number = Column(String(20))
    serial_numbers = Column(String(500))  # Comma separated
    expiry_date = Column(DateTime)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    receipt = relationship("GoodsReceipt", back_populates="receipt_lines")
    po_line = relationship("PurchaseOrderLine")
    stock_item = relationship("StockItem")
    
    # Indexes
    __table_args__ = (
        Index("idx_receipt_line", "receipt_id", "line_number"),
    )


# Purchase Invoices

class PurchaseInvoice(Base):
    """Purchase Invoice/Credit Note - from COBOL pl910/pl920"""
    __tablename__ = "purchase_invoices"
    
    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(20), unique=True, nullable=False, index=True)
    invoice_date = Column(DateTime, nullable=False)
    invoice_type = Column(String(20), default="INVOICE")  # INVOICE, CREDIT_NOTE
    
    # Supplier
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    supplier_invoice_no = Column(String(30), nullable=False)
    
    # References
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"))
    goods_receipt_id = Column(Integer, ForeignKey("goods_receipts.id"))
    
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
    
    # Matching
    matched_amount = Column(CurrencyAmount(), default=0.00)
    variance_amount = Column(CurrencyAmount(), default=0.00)
    is_matched = Column(Boolean, default=False)
    matched_date = Column(DateTime)
    matched_by = Column(String(20))
    
    # Payment Status
    amount_paid = Column(CurrencyAmount(), default=0.00)
    balance = Column(CurrencyAmount())
    is_paid = Column(Boolean, default=False)
    
    # GL Posting
    period_number = Column(Integer)
    gl_posted = Column(Boolean, default=False)
    gl_batch_number = Column(String(20))
    
    # Approval
    approved_for_payment = Column(Boolean, default=False)
    approved_by = Column(String(20))
    approved_date = Column(DateTime)
    
    # Hold/Dispute
    on_hold = Column(Boolean, default=False)
    hold_reason = Column(String(200))
    dispute_flag = Column(Boolean, default=False)
    dispute_reason = Column(String(200))
    
    # Notes
    notes = Column(String(500))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    supplier = relationship("Supplier", back_populates="purchase_invoices")
    invoice_lines = relationship("PurchaseInvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    purchase_order = relationship("PurchaseOrder")
    goods_receipt = relationship("GoodsReceipt")


class PurchaseInvoiceLine(Base):
    """Purchase Invoice Lines"""
    __tablename__ = "purchase_invoice_lines"
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("purchase_invoices.id"), nullable=False)
    line_number = Column(Integer, nullable=False)
    
    # References
    po_line_id = Column(Integer, ForeignKey("purchase_order_lines.id"))
    receipt_line_id = Column(Integer, ForeignKey("goods_receipt_lines.id"))
    
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
    
    # GL Coding
    gl_account = Column(String(8))
    analysis_code1 = Column(String(10))
    analysis_code2 = Column(String(10))
    analysis_code3 = Column(String(10))
    
    # Matching
    po_price = Column(CurrencyAmount())
    price_variance = Column(CurrencyAmount())
    quantity_variance = Column(COMP3(15, 3))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    invoice = relationship("PurchaseInvoice", back_populates="invoice_lines")
    po_line = relationship("PurchaseOrderLine")
    receipt_line = relationship("GoodsReceiptLine")
    stock_item = relationship("StockItem")
    
    # Indexes
    __table_args__ = (
        Index("idx_pinv_line", "invoice_id", "line_number"),
    )


# Supplier Payments

class SupplierPayment(Base):
    """Supplier Payment/Remittance - from COBOL pl120/pl130"""
    __tablename__ = "supplier_payments"
    
    id = Column(Integer, primary_key=True)
    payment_number = Column(String(20), unique=True, nullable=False, index=True)
    payment_date = Column(DateTime, nullable=False, default=func.now())
    payment_run_number = Column(String(20))  # For batch payments
    
    # Supplier
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    supplier_code = Column(String(7), nullable=False)
    
    # Payment Details
    payment_method = Column(String(20), nullable=False)  # CHECK, TRANSFER, CASH
    bank_account = Column(String(20))
    check_number = Column(String(20))
    
    # Amounts
    currency_code = Column(String(3), default="USD")
    payment_amount = Column(CurrencyAmount(), nullable=False)
    allocated_amount = Column(CurrencyAmount(), default=0.00)
    unallocated_amount = Column(CurrencyAmount())
    
    # Bank Details
    bank_reference = Column(String(30))
    bank_charges = Column(CurrencyAmount(), default=0.00)
    
    # GL Posting
    period_number = Column(Integer)
    gl_posted = Column(Boolean, default=False)
    gl_batch_number = Column(String(20))
    
    # Status
    is_allocated = Column(Boolean, default=False)
    is_cancelled = Column(Boolean, default=False)
    is_printed = Column(Boolean, default=False)
    
    # Notes
    notes = Column(String(500))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    supplier = relationship("Supplier", back_populates="payments")
    allocations = relationship("SupplierPaymentAllocation", back_populates="payment", cascade="all, delete-orphan")


class SupplierPaymentAllocation(Base):
    """Supplier Payment to Invoice Allocation"""
    __tablename__ = "supplier_payment_allocations"
    
    id = Column(Integer, primary_key=True)
    payment_id = Column(Integer, ForeignKey("supplier_payments.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("purchase_invoices.id"), nullable=False)
    
    allocation_date = Column(DateTime, default=func.now())
    allocated_amount = Column(CurrencyAmount(), nullable=False)
    discount_taken = Column(CurrencyAmount(), default=0.00)
    
    # Exchange difference (multi-currency)
    exchange_difference = Column(CurrencyAmount(), default=0.00)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(20))
    
    # Relationships
    payment = relationship("SupplierPayment", back_populates="allocations")
    invoice = relationship("PurchaseInvoice")
    
    # Indexes
    __table_args__ = (
        Index("idx_sup_alloc_payment", "payment_id"),
        Index("idx_sup_alloc_invoice", "invoice_id"),
    )