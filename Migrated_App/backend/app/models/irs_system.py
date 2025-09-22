"""
IRS System Models
Migrated from ACAS IRS COBOL structures
Simple bookkeeping system with automatic double-entry generation
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.config.database import Base, CurrencyAmount
from sqlalchemy.sql import func


class IRSTransactionType(str, enum.Enum):
    """IRS Transaction types"""
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    ASSET_PURCHASE = "ASSET_PURCHASE"
    ASSET_SALE = "ASSET_SALE"
    LIABILITY = "LIABILITY"
    CAPITAL = "CAPITAL"
    DRAWING = "DRAWING"
    VAT = "VAT"


class IRSPostingStatus(str, enum.Enum):
    """IRS Posting status"""
    DRAFT = "DRAFT"
    READY = "READY"
    POSTED = "POSTED"
    ERROR = "ERROR"


# IRS Configuration

class IRSConfiguration(Base):
    """IRS System Configuration - from COBOL irs system setup"""
    __tablename__ = "irs_configuration"
    
    id = Column(Integer, primary_key=True)
    
    # Business Details
    business_name = Column(String(60), nullable=False)
    business_type = Column(String(30))  # SOLE_TRADER, PARTNERSHIP, etc.
    tax_id = Column(String(20))
    
    # VAT Registration
    vat_registered = Column(Boolean, default=False)
    vat_registration_no = Column(String(20))
    vat_scheme = Column(String(20))  # STANDARD, FLAT_RATE, CASH
    flat_rate_percentage = Column(CurrencyAmount())
    
    # Tax Year
    tax_year_start_month = Column(Integer, default=4)  # April
    tax_year_start_day = Column(Integer, default=6)    # 6th
    
    # Accounting Method
    cash_basis = Column(Boolean, default=True)
    
    # Default Accounts
    bank_account = Column(String(8))
    cash_account = Column(String(8))
    capital_account = Column(String(8))
    drawings_account = Column(String(8))
    
    # Posting Rules
    auto_post_to_gl = Column(Boolean, default=True)
    require_receipts = Column(Boolean, default=True)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    updated_by = Column(String(20))


# IRS Categories

class IRSCategory(Base):
    """IRS Income/Expense Categories - from COBOL irs categories"""
    __tablename__ = "irs_categories"
    
    id = Column(Integer, primary_key=True)
    category_code = Column(String(10), unique=True, nullable=False, index=True)
    category_name = Column(String(60), nullable=False)
    category_type = Column(Enum(IRSTransactionType), nullable=False)
    
    # GL Mapping
    gl_account = Column(String(8))
    
    # VAT Treatment
    default_vat_code = Column(String(1), default="S")
    vat_inclusive = Column(Boolean, default=False)
    
    # Tax Treatment
    tax_deductible = Column(Boolean, default=True)
    capital_allowance = Column(Boolean, default=False)
    
    # Reporting
    schedule_box = Column(String(10))  # Tax form box reference
    
    # Status
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System categories cannot be deleted
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    entries = relationship("IRSEntry", back_populates="category")


# IRS Entries

class IRSEntry(Base):
    """IRS Transaction Entries - from COBOL irs010/irs020"""
    __tablename__ = "irs_entries"
    
    id = Column(Integer, primary_key=True)
    entry_number = Column(String(20), unique=True, nullable=False, index=True)
    entry_date = Column(DateTime, nullable=False)
    
    # Transaction Details
    transaction_type = Column(Enum(IRSTransactionType), nullable=False)
    category_id = Column(Integer, ForeignKey("irs_categories.id"), nullable=False)
    
    # Description
    description = Column(String(200), nullable=False)
    reference = Column(String(30))
    
    # Financial
    gross_amount = Column(CurrencyAmount(), nullable=False)
    vat_code = Column(String(1), default="S")
    vat_rate = Column(CurrencyAmount())
    vat_amount = Column(CurrencyAmount(), default=0.00)
    net_amount = Column(CurrencyAmount(), nullable=False)
    
    # Payment Method
    payment_method = Column(String(20))  # CASH, CHECK, CARD, TRANSFER
    bank_account = Column(String(8))
    
    # Customer/Supplier
    entity_type = Column(String(20))  # CUSTOMER, SUPPLIER, OTHER
    entity_name = Column(String(60))
    entity_reference = Column(String(20))
    
    # Receipt/Invoice
    receipt_number = Column(String(30))
    has_receipt = Column(Boolean, default=False)
    
    # Asset Information (for asset purchases)
    asset_description = Column(String(200))
    asset_life_years = Column(Integer)
    
    # Status
    posting_status = Column(Enum(IRSPostingStatus), default=IRSPostingStatus.DRAFT)
    posted_date = Column(DateTime)
    gl_journal_id = Column(Integer, ForeignKey("journal_headers.id"))
    
    # Period
    tax_year = Column(Integer, nullable=False)
    tax_period = Column(Integer, nullable=False)
    
    # Notes
    notes = Column(String(500))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    category = relationship("IRSCategory", back_populates="entries")
    gl_journal = relationship("JournalHeader")
    
    # Indexes
    __table_args__ = (
        Index("idx_irs_date", "entry_date"),
        Index("idx_irs_category", "category_id"),
        Index("idx_irs_status", "posting_status"),
        Index("idx_irs_tax_period", "tax_year", "tax_period"),
    )


# IRS Posting Batch

class IRSPostingBatch(Base):
    """IRS Posting Batch Control - from COBOL irs030"""
    __tablename__ = "irs_posting_batches"
    
    id = Column(Integer, primary_key=True)
    batch_number = Column(String(20), unique=True, nullable=False, index=True)
    batch_date = Column(DateTime, nullable=False)
    
    # Period
    tax_year = Column(Integer, nullable=False)
    tax_period = Column(Integer, nullable=False)
    
    # Selection Criteria
    from_date = Column(DateTime, nullable=False)
    to_date = Column(DateTime, nullable=False)
    transaction_types = Column(String(200))  # Comma-separated list
    
    # Control Totals
    entry_count = Column(Integer, default=0)
    total_income = Column(CurrencyAmount(), default=0.00)
    total_expenses = Column(CurrencyAmount(), default=0.00)
    total_vat = Column(CurrencyAmount(), default=0.00)
    
    # GL Integration
    gl_batch_id = Column(Integer, ForeignKey("gl_batches.id"))
    journal_count = Column(Integer, default=0)
    
    # Status
    is_posted = Column(Boolean, default=False)
    posted_date = Column(DateTime)
    posted_by = Column(String(20))
    
    # Errors
    error_count = Column(Integer, default=0)
    error_messages = Column(String(1000))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    gl_batch = relationship("GLBatch")


# IRS Reports Configuration

class IRSReport(Base):
    """IRS Report Definitions"""
    __tablename__ = "irs_reports"
    
    id = Column(Integer, primary_key=True)
    report_code = Column(String(20), unique=True, nullable=False)
    report_name = Column(String(60), nullable=False)
    
    # Report Type
    report_type = Column(String(30))  # TAX_RETURN, VAT_RETURN, ANALYSIS
    tax_form = Column(String(20))     # SA100, VAT100, etc.
    
    # Period
    period_type = Column(String(20))  # ANNUAL, QUARTERLY, MONTHLY
    
    # Configuration
    configuration = Column(String(2000))  # JSON configuration
    
    # Status
    is_active = Column(Boolean, default=True)
    is_official = Column(Boolean, default=False)  # Official tax form
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))


# Capital Assets Register

class IRSCapitalAsset(Base):
    """Capital Assets Register for depreciation"""
    __tablename__ = "irs_capital_assets"
    
    id = Column(Integer, primary_key=True)
    asset_code = Column(String(20), unique=True, nullable=False)
    
    # Asset Details
    description = Column(String(200), nullable=False)
    purchase_date = Column(DateTime, nullable=False)
    purchase_entry_id = Column(Integer, ForeignKey("irs_entries.id"))
    
    # Cost
    purchase_cost = Column(CurrencyAmount(), nullable=False)
    
    # Depreciation
    depreciation_method = Column(String(20), default="STRAIGHT_LINE")
    useful_life_years = Column(Integer, nullable=False)
    depreciation_rate = Column(CurrencyAmount())
    
    # Current Values
    accumulated_depreciation = Column(CurrencyAmount(), default=0.00)
    net_book_value = Column(CurrencyAmount())
    
    # Disposal
    is_disposed = Column(Boolean, default=False)
    disposal_date = Column(DateTime)
    disposal_proceeds = Column(CurrencyAmount())
    disposal_entry_id = Column(Integer, ForeignKey("irs_entries.id"))
    
    # Capital Allowances
    capital_allowance_rate = Column(CurrencyAmount())
    capital_allowances_claimed = Column(CurrencyAmount(), default=0.00)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    purchase_entry = relationship("IRSEntry", foreign_keys=[purchase_entry_id])
    disposal_entry = relationship("IRSEntry", foreign_keys=[disposal_entry_id])