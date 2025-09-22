"""
General Ledger Models
Migrated from ACAS General Ledger COBOL structures
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.config.database import Base, COMP3, CurrencyAmount
from sqlalchemy.sql import func


class AccountType(str, enum.Enum):
    """GL Account types"""
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    CAPITAL = "CAPITAL"
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    CONTROL = "CONTROL"  # Control accounts (Debtors, Creditors)
    MEMO = "MEMO"        # Memorandum accounts


class JournalType(str, enum.Enum):
    """Journal entry types"""
    MANUAL = "MANUAL"
    SALES = "SALES"
    PURCHASE = "PURCHASE"
    CASH_RECEIPT = "CASH_RECEIPT"
    CASH_PAYMENT = "CASH_PAYMENT"
    STOCK = "STOCK"
    PAYROLL = "PAYROLL"
    OPENING = "OPENING"
    CLOSING = "CLOSING"
    ADJUSTMENT = "ADJUSTMENT"
    REVERSAL = "REVERSAL"


class PostingStatus(str, enum.Enum):
    """Posting status"""
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    REVERSED = "REVERSED"


# Chart of Accounts

class ChartOfAccounts(Base):
    """Chart of Accounts - from COBOL gl020"""
    __tablename__ = "chart_of_accounts"
    
    id = Column(Integer, primary_key=True)
    account_code = Column(String(8), unique=True, nullable=False, index=True)  # Format: ####.####
    
    # Account Details
    account_name = Column(String(60), nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    
    # Hierarchy
    parent_account = Column(String(8))
    is_header = Column(Boolean, default=False)  # Header accounts for grouping
    level = Column(Integer, default=0)  # 0=Main, 1=Sub, 2=Detail
    
    # Control
    is_active = Column(Boolean, default=True)
    is_control = Column(Boolean, default=False)  # Control account
    control_type = Column(String(20))  # DEBTORS, CREDITORS, BANK, etc.
    allow_posting = Column(Boolean, default=True)  # Can post transactions
    
    # Budgeting
    budget_enabled = Column(Boolean, default=False)
    
    # Analysis
    analysis_code1_required = Column(Boolean, default=False)
    analysis_code2_required = Column(Boolean, default=False)
    analysis_code3_required = Column(Boolean, default=False)
    
    # Currency
    currency_code = Column(String(3), default="USD")
    multi_currency = Column(Boolean, default=False)
    
    # VAT/Tax
    default_vat_code = Column(String(1))
    
    # Current Balances
    opening_balance = Column(CurrencyAmount(), default=0.00)
    current_balance = Column(CurrencyAmount(), default=0.00)
    ytd_movement = Column(CurrencyAmount(), default=0.00)
    
    # Notes
    notes = Column(String(500))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    journal_lines = relationship("JournalLine", back_populates="account")
    budget_lines = relationship("BudgetLine", back_populates="account")
    
    # Indexes
    __table_args__ = (
        Index("idx_gl_account_type", "account_type"),
        Index("idx_gl_parent", "parent_account"),
    )


# Journal Entries

class JournalHeader(Base):
    """Journal Entry Header - from COBOL gl050/gl060"""
    __tablename__ = "journal_headers"
    
    id = Column(Integer, primary_key=True)
    journal_number = Column(String(20), unique=True, nullable=False, index=True)
    journal_date = Column(DateTime, nullable=False)
    journal_type = Column(Enum(JournalType), nullable=False)
    
    # Period
    period_id = Column(Integer, ForeignKey("company_periods.id"), nullable=False)
    period_number = Column(Integer, nullable=False)
    year_number = Column(Integer, nullable=False)
    
    # Description
    description = Column(String(200), nullable=False)
    reference = Column(String(30))
    
    # Source
    source_module = Column(String(10))  # SL, PL, ST, etc.
    source_reference = Column(String(30))  # Invoice no, etc.
    
    # Status
    posting_status = Column(Enum(PostingStatus), default=PostingStatus.DRAFT)
    posted_date = Column(DateTime)
    posted_by = Column(String(20))
    
    # Reversal
    is_reversal = Column(Boolean, default=False)
    reversal_of_id = Column(Integer, ForeignKey("journal_headers.id"))
    auto_reverse = Column(Boolean, default=False)
    reverse_date = Column(DateTime)
    
    # Totals (for validation)
    total_debits = Column(CurrencyAmount(), default=0.00)
    total_credits = Column(CurrencyAmount(), default=0.00)
    line_count = Column(Integer, default=0)
    
    # Batch
    batch_id = Column(Integer, ForeignKey("gl_batches.id"))
    
    # Approval
    approval_required = Column(Boolean, default=False)
    approved_by = Column(String(20))
    approved_date = Column(DateTime)
    
    # Notes
    notes = Column(String(500))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    period = relationship("CompanyPeriod")
    journal_lines = relationship("JournalLine", back_populates="journal", cascade="all, delete-orphan")
    batch = relationship("GLBatch", back_populates="journals")
    reversal_of = relationship("JournalHeader", remote_side=[id])


class JournalLine(Base):
    """Journal Entry Lines - from COBOL gl050/gl060"""
    __tablename__ = "journal_lines"
    
    id = Column(Integer, primary_key=True)
    journal_id = Column(Integer, ForeignKey("journal_headers.id"), nullable=False)
    line_number = Column(Integer, nullable=False)
    
    # Account
    account_id = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=False)
    account_code = Column(String(8), nullable=False)
    
    # Amounts
    debit_amount = Column(CurrencyAmount(), default=0.00)
    credit_amount = Column(CurrencyAmount(), default=0.00)
    
    # Foreign Currency
    currency_code = Column(String(3), default="USD")
    exchange_rate = Column(CurrencyAmount(), default=1.0000)
    foreign_debit = Column(CurrencyAmount(), default=0.00)
    foreign_credit = Column(CurrencyAmount(), default=0.00)
    
    # Description
    description = Column(String(200))
    reference = Column(String(30))
    
    # Analysis Codes
    analysis_code1 = Column(String(10))
    analysis_code2 = Column(String(10))
    analysis_code3 = Column(String(10))
    
    # Quantity (for unit cost analysis)
    quantity = Column(COMP3(15, 3))
    unit_description = Column(String(20))
    
    # VAT/Tax
    vat_code = Column(String(1))
    vat_amount = Column(CurrencyAmount())
    
    # Reconciliation
    reconciled = Column(Boolean, default=False)
    reconciliation_date = Column(DateTime)
    reconciliation_ref = Column(String(20))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    journal = relationship("JournalHeader", back_populates="journal_lines")
    account = relationship("ChartOfAccounts", back_populates="journal_lines")
    
    # Indexes
    __table_args__ = (
        Index("idx_journal_line", "journal_id", "line_number"),
        Index("idx_journal_account", "account_code", "journal_id"),
        UniqueConstraint("journal_id", "line_number", name="uq_journal_line"),
    )


# GL Batches

class GLBatch(Base):
    """GL Batch Control - from COBOL gl030"""
    __tablename__ = "gl_batches"
    
    id = Column(Integer, primary_key=True)
    batch_number = Column(String(20), unique=True, nullable=False, index=True)
    batch_date = Column(DateTime, nullable=False)
    
    # Batch Details
    batch_type = Column(String(20), nullable=False)  # MANUAL, AUTO, IMPORT
    description = Column(String(200))
    source_module = Column(String(10))
    
    # Period
    period_id = Column(Integer, ForeignKey("company_periods.id"), nullable=False)
    
    # Control Totals
    control_count = Column(Integer, default=0)
    control_debits = Column(CurrencyAmount(), default=0.00)
    control_credits = Column(CurrencyAmount(), default=0.00)
    
    # Actual Totals
    actual_count = Column(Integer, default=0)
    actual_debits = Column(CurrencyAmount(), default=0.00)
    actual_credits = Column(CurrencyAmount(), default=0.00)
    
    # Status
    is_balanced = Column(Boolean, default=False)
    is_posted = Column(Boolean, default=False)
    posted_date = Column(DateTime)
    posted_by = Column(String(20))
    
    # Validation
    validation_errors = Column(String(1000))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    period = relationship("CompanyPeriod")
    journals = relationship("JournalHeader", back_populates="batch")


# Account Balances by Period

class AccountBalance(Base):
    """Account Balances by Period - for performance"""
    __tablename__ = "account_balances"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("company_periods.id"), nullable=False)
    
    # Balances
    opening_balance = Column(CurrencyAmount(), default=0.00)
    period_debits = Column(CurrencyAmount(), default=0.00)
    period_credits = Column(CurrencyAmount(), default=0.00)
    closing_balance = Column(CurrencyAmount(), default=0.00)
    
    # Movement Count
    transaction_count = Column(Integer, default=0)
    
    # Budget Comparison
    budget_amount = Column(CurrencyAmount(), default=0.00)
    variance_amount = Column(CurrencyAmount(), default=0.00)
    variance_percent = Column(CurrencyAmount(), default=0.00)
    
    # Foreign Currency
    foreign_opening = Column(CurrencyAmount(), default=0.00)
    foreign_debits = Column(CurrencyAmount(), default=0.00)
    foreign_credits = Column(CurrencyAmount(), default=0.00)
    foreign_closing = Column(CurrencyAmount(), default=0.00)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("ChartOfAccounts")
    period = relationship("CompanyPeriod")
    
    # Indexes
    __table_args__ = (
        UniqueConstraint("account_id", "period_id", name="uq_account_period"),
        Index("idx_balance_period", "period_id"),
        Index("idx_balance_account", "account_id"),
    )


# Budget

class BudgetHeader(Base):
    """Budget Header"""
    __tablename__ = "budget_headers"
    
    id = Column(Integer, primary_key=True)
    budget_name = Column(String(60), nullable=False)
    budget_year = Column(Integer, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(String(20))
    approved_date = Column(DateTime)
    
    # Type
    budget_type = Column(String(20), default="ANNUAL")  # ANNUAL, QUARTERLY, MONTHLY
    
    # Notes
    notes = Column(String(500))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    budget_lines = relationship("BudgetLine", back_populates="budget", cascade="all, delete-orphan")


class BudgetLine(Base):
    """Budget Lines by Account and Period"""
    __tablename__ = "budget_lines"
    
    id = Column(Integer, primary_key=True)
    budget_id = Column(Integer, ForeignKey("budget_headers.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=False)
    period_number = Column(Integer, nullable=False)
    
    # Budget Amount
    budget_amount = Column(CurrencyAmount(), nullable=False)
    
    # Analysis
    analysis_code1 = Column(String(10))
    analysis_code2 = Column(String(10))
    analysis_code3 = Column(String(10))
    
    # Notes
    notes = Column(String(200))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    budget = relationship("BudgetHeader", back_populates="budget_lines")
    account = relationship("ChartOfAccounts", back_populates="budget_lines")
    
    # Indexes
    __table_args__ = (
        UniqueConstraint("budget_id", "account_id", "period_number", name="uq_budget_account_period"),
        Index("idx_budget_account", "account_id"),
    )


# Bank Reconciliation

class BankReconciliation(Base):
    """Bank Reconciliation Header"""
    __tablename__ = "bank_reconciliations"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=False)
    reconciliation_date = Column(DateTime, nullable=False)
    
    # Balances
    statement_balance = Column(CurrencyAmount(), nullable=False)
    book_balance = Column(CurrencyAmount(), nullable=False)
    reconciled_balance = Column(CurrencyAmount())
    difference = Column(CurrencyAmount())
    
    # Counts
    items_cleared = Column(Integer, default=0)
    items_outstanding = Column(Integer, default=0)
    
    # Status
    is_complete = Column(Boolean, default=False)
    completed_date = Column(DateTime)
    completed_by = Column(String(20))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(20))
    updated_by = Column(String(20))
    
    # Relationships
    account = relationship("ChartOfAccounts")