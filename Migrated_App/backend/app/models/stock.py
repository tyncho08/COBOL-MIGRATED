"""
Stock Control Models
Migrated from ACAS Stock Control (fdstock.cob, wsstock.cob)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base, COMP3, CurrencyAmount, Percentage
from sqlalchemy.sql import func


class StockItem(Base):
    """Stock Master Record - from fdstock.cob"""
    __tablename__ = "stock_items"
    
    # Primary key - 13 character stock code
    id = Column(Integer, primary_key=True)
    stock_code = Column(String(13), unique=True, nullable=False, index=True)
    abbreviated_code = Column(String(7), unique=True, nullable=True, index=True)
    
    # Description and Details
    description = Column(String(60), nullable=False, index=True)
    extended_description = Column(String(200))
    unit_of_measure = Column(String(10), default="EACH")
    
    # Categorization
    category_code = Column(String(10), index=True)
    sub_category = Column(String(10))
    analysis_code1 = Column(String(10))
    analysis_code2 = Column(String(10))
    analysis_code3 = Column(String(10))
    
    # Supplier Information (3 suppliers as per ACAS)
    supplier1_code = Column(String(7))
    supplier1_ref = Column(String(20))
    supplier1_pack_qty = Column(Integer, default=1)
    
    supplier2_code = Column(String(7))
    supplier2_ref = Column(String(20))
    supplier2_pack_qty = Column(Integer, default=1)
    
    supplier3_code = Column(String(7))
    supplier3_ref = Column(String(20))
    supplier3_pack_qty = Column(Integer, default=1)
    
    # Quantities
    quantity_on_hand = Column(COMP3(15, 3), default=0.000)
    quantity_allocated = Column(COMP3(15, 3), default=0.000)
    quantity_on_order = Column(COMP3(15, 3), default=0.000)
    quantity_back_order = Column(COMP3(15, 3), default=0.000)
    quantity_in_transit = Column(COMP3(15, 3), default=0.000)
    
    # Available = on_hand - allocated
    @property
    def quantity_available(self):
        return self.quantity_on_hand - self.quantity_allocated
    
    # Stock Levels
    reorder_level = Column(COMP3(15, 3), default=0.000)
    reorder_quantity = Column(COMP3(15, 3), default=0.000)
    minimum_stock = Column(COMP3(15, 3), default=0.000)
    maximum_stock = Column(COMP3(15, 3), default=0.000)
    
    # Costing Information
    cost_method = Column(String(10), default="AVERAGE")  # FIFO, LIFO, AVERAGE, STANDARD
    standard_cost = Column(CurrencyAmount(), default=0.00)
    last_cost = Column(CurrencyAmount(), default=0.00)
    average_cost = Column(CurrencyAmount(), default=0.00)
    replacement_cost = Column(CurrencyAmount(), default=0.00)
    
    # Selling Prices
    selling_price1 = Column(CurrencyAmount(), default=0.00)
    selling_price2 = Column(CurrencyAmount(), default=0.00)
    selling_price3 = Column(CurrencyAmount(), default=0.00)
    selling_price4 = Column(CurrencyAmount(), default=0.00)
    selling_price5 = Column(CurrencyAmount(), default=0.00)
    
    # VAT/Tax
    vat_code = Column(String(1), default="S")  # S=Standard, Z=Zero, E=Exempt
    
    # Status Flags
    is_active = Column(Boolean, default=True)
    is_stocked = Column(Boolean, default=True)
    is_serialized = Column(Boolean, default=False)
    is_batch_tracked = Column(Boolean, default=False)
    allow_negative_stock = Column(Boolean, default=False)
    
    # Physical Attributes
    weight = Column(COMP3(10, 3))
    volume = Column(COMP3(10, 3))
    shelf_location = Column(String(20))
    bin_location = Column(String(20))
    
    # Movement Summary (Current Year)
    ytd_receipts = Column(COMP3(15, 3), default=0.000)
    ytd_issues = Column(COMP3(15, 3), default=0.000)
    ytd_adjustments = Column(COMP3(15, 3), default=0.000)
    ytd_sales_value = Column(CurrencyAmount(), default=0.00)
    ytd_cost_value = Column(CurrencyAmount(), default=0.00)
    
    # Monthly Movement History (12 months as per ACAS)
    movement_history = Column(JSON, default=lambda: {"months": [{"receipts": 0, "issues": 0} for _ in range(12)]})
    
    # Last Transaction Dates
    last_receipt_date = Column(DateTime)
    last_issue_date = Column(DateTime)
    last_count_date = Column(DateTime)
    last_sale_date = Column(DateTime)
    
    # Additional Fields
    barcode = Column(String(20), unique=True, nullable=True)
    manufacturer_code = Column(String(20))
    country_of_origin = Column(String(2))
    commodity_code = Column(String(20))
    
    # Notes
    notes = Column(String(500))
    
    # Audit fields
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    movements = relationship("StockMovement", back_populates="stock_item")
    order_lines = relationship("SalesOrderLine", back_populates="stock_item")
    invoice_lines = relationship("SalesInvoiceLine", back_populates="stock_item")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_stock_description", "description"),
        Index("idx_stock_category", "category_code"),
        Index("idx_stock_supplier1", "supplier1_code"),
        Index("idx_stock_barcode", "barcode"),
    )


class StockMovement(Base):
    """Stock movement transactions"""
    __tablename__ = "stock_movements"
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stock_items.id"))
    
    movement_date = Column(DateTime, default=func.now())
    movement_type = Column(String(20), nullable=False)  # RECEIPT, ISSUE, ADJUSTMENT, TRANSFER
    reference_type = Column(String(20))  # INVOICE, ORDER, MANUAL, etc.
    reference_number = Column(String(20))
    
    quantity = Column(COMP3(15, 3), nullable=False)
    unit_cost = Column(CurrencyAmount())
    total_cost = Column(CurrencyAmount())
    
    # Location tracking
    from_location = Column(String(20))
    to_location = Column(String(20))
    
    # Reason/Notes
    reason_code = Column(String(10))
    notes = Column(String(200))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(20))
    
    # Relationships
    stock_item = relationship("StockItem", back_populates="movements")
    
    # Index for performance
    __table_args__ = (
        Index("idx_movement_date", "movement_date"),
        Index("idx_movement_stock", "stock_id", "movement_date"),
    )


class StockValuation(Base):
    """Period-end stock valuation snapshot"""
    __tablename__ = "stock_valuations"
    
    id = Column(Integer, primary_key=True)
    period_id = Column(Integer, ForeignKey("company_periods.id"))
    stock_id = Column(Integer, ForeignKey("stock_items.id"))
    
    valuation_date = Column(DateTime, nullable=False)
    quantity = Column(COMP3(15, 3), nullable=False)
    unit_cost = Column(CurrencyAmount(), nullable=False)
    total_value = Column(CurrencyAmount(), nullable=False)
    
    valuation_method = Column(String(10))  # FIFO, LIFO, AVERAGE
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(20))