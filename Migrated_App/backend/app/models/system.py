"""
System Configuration Models
Migrated from ACAS system.dat and wssystem.cob
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base, COMP3, CurrencyAmount, Percentage
from sqlalchemy.sql import func


class SystemConfig(Base):
    """Main system configuration - replaces system.dat"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True)
    
    # Company Information
    company_name = Column(String(60), nullable=False)
    company_address1 = Column(String(60))
    company_address2 = Column(String(60))
    company_address3 = Column(String(60))
    company_postcode = Column(String(10))
    company_phone = Column(String(20))
    company_email = Column(String(100))
    company_registration = Column(String(20))
    vat_registration = Column(String(20))
    
    # System Settings
    system_date = Column(DateTime, default=func.now())
    fiscal_year_start = Column(Integer, default=1)
    current_period = Column(Integer, default=1)
    periods_per_year = Column(Integer, default=12)
    
    # Module Enable Flags
    sales_ledger_enabled = Column(Boolean, default=True)
    purchase_ledger_enabled = Column(Boolean, default=True)
    stock_control_enabled = Column(Boolean, default=True)
    general_ledger_enabled = Column(Boolean, default=True)
    irs_enabled = Column(Boolean, default=True)
    
    # VAT/Tax Settings
    vat_enabled = Column(Boolean, default=True)
    default_vat_rate = Column(Percentage(), default=20.0)
    reduced_vat_rate = Column(Percentage(), default=5.0)
    zero_vat_rate = Column(Percentage(), default=0.0)
    
    # Currency Settings
    base_currency = Column(String(3), default="USD")
    multi_currency_enabled = Column(Boolean, default=False)
    
    # Control Settings
    force_credit_limit = Column(Boolean, default=True)
    allow_negative_stock = Column(Boolean, default=False)
    auto_generate_gl_postings = Column(Boolean, default=True)
    
    # Numbering
    next_invoice_number = Column(Integer, default=1)
    next_order_number = Column(Integer, default=1)
    next_payment_number = Column(Integer, default=1)
    next_batch_number = Column(Integer, default=1)
    
    # Additional Settings (JSON for flexibility)
    additional_settings = Column(JSON, default={})
    
    # Audit fields
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    updated_by = Column(String(20))


class User(Base):
    """User accounts - migrated from ACAS security"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(60), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # ACAS-specific fields
    user_level = Column(Integer, default=1)  # 1-9 permission levels
    allowed_companies = Column(JSON, default=[])  # Multi-company support
    module_access = Column(JSON, default={})  # Module-specific permissions
    
    # Session tracking
    last_login = Column(DateTime)
    last_activity = Column(DateTime)
    login_count = Column(Integer, default=0)
    
    # Audit fields
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    audit_trails = relationship("AuditTrail", back_populates="user")


class AuditTrail(Base):
    """Comprehensive audit trail - critical ACAS feature"""
    __tablename__ = "audit_trail"
    
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(50), nullable=False, index=True)
    record_id = Column(String(50), nullable=False, index=True)
    operation_type = Column(String(10), nullable=False)  # INSERT, UPDATE, DELETE
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=func.now(), index=True)
    
    # Change tracking
    before_image = Column(JSON)
    after_image = Column(JSON)
    changed_fields = Column(JSON)
    
    # Session info
    session_id = Column(String(50))
    ip_address = Column(String(45))
    user_agent = Column(String(200))
    application_version = Column(String(20))
    
    # Relationships
    user = relationship("User", back_populates="audit_trails")


class CompanyPeriod(Base):
    """Financial periods - controls transaction dates"""
    __tablename__ = "company_periods"
    
    id = Column(Integer, primary_key=True)
    period_number = Column(Integer, nullable=False)
    year_number = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Status flags
    is_open = Column(Boolean, default=True)
    is_current = Column(Boolean, default=False)
    gl_closed = Column(Boolean, default=False)
    sl_closed = Column(Boolean, default=False)
    pl_closed = Column(Boolean, default=False)
    stock_closed = Column(Boolean, default=False)
    
    # Control totals
    sl_control_total = Column(CurrencyAmount())
    pl_control_total = Column(CurrencyAmount())
    gl_control_total = Column(CurrencyAmount())
    
    # Audit
    closed_date = Column(DateTime)
    closed_by = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SystemParameter(Base):
    """Flexible system parameters - extends system config"""
    __tablename__ = "system_parameters"
    
    id = Column(Integer, primary_key=True)
    module_code = Column(String(10), nullable=False)
    parameter_name = Column(String(50), nullable=False)
    parameter_value = Column(String(200))
    parameter_type = Column(String(20))  # STRING, NUMBER, BOOLEAN, DATE
    description = Column(String(200))
    is_encrypted = Column(Boolean, default=False)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    updated_by = Column(String(20))