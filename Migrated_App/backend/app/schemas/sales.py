"""
Sales Module Schemas
Pydantic models for Sales Ledger operations
"""
from datetime import datetime, date
from decimal import Decimal as PyDecimal
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from app.models.transactions import InvoiceType


# Customer Schemas
class CustomerBase(BaseModel):
    customer_code: str = Field(..., min_length=7, max_length=7, description="7-character customer code")
    customer_name: str = Field(..., max_length=60)
    address_line1: Optional[str] = Field(None, max_length=60)
    address_line2: Optional[str] = Field(None, max_length=60)
    address_line3: Optional[str] = Field(None, max_length=60)
    postcode: Optional[str] = Field(None, max_length=10)
    country_code: str = Field(default="US", max_length=2)
    phone_number: Optional[str] = Field(None, max_length=20)
    email_address: Optional[str] = Field(None, max_length=100)
    credit_limit: PyDecimal = Field(default=PyDecimal("0.00"))
    payment_terms: int = Field(default=30, ge=0, le=365)
    discount_percentage: PyDecimal = Field(default=PyDecimal("0.00"))
    settlement_discount: PyDecimal = Field(default=PyDecimal("0.00"))
    settlement_days: int = Field(default=0, ge=0, le=30)
    vat_registration: Optional[str] = Field(None, max_length=20)
    vat_code: str = Field(default="S", max_length=1)
    analysis_code1: Optional[str] = Field(None, max_length=10)
    analysis_code2: Optional[str] = Field(None, max_length=10)
    analysis_code3: Optional[str] = Field(None, max_length=10)
    currency_code: str = Field(default="USD", max_length=3)
    is_active: bool = Field(default=True)
    on_hold: bool = Field(default=False)
    cash_only: bool = Field(default=False)
    allow_partial_shipment: bool = Field(default=False)
    
    @field_validator('credit_limit', 'discount_percentage', 'settlement_discount', mode='before')
    @classmethod
    def validate_decimal(cls, v):
        if v is not None:
            return PyDecimal(str(v))
        return v


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = Field(None, max_length=60)
    address_line1: Optional[str] = Field(None, max_length=60)
    address_line2: Optional[str] = Field(None, max_length=60)
    address_line3: Optional[str] = Field(None, max_length=60)
    postcode: Optional[str] = Field(None, max_length=10)
    phone_number: Optional[str] = Field(None, max_length=20)
    email_address: Optional[str] = Field(None, max_length=100)
    credit_limit: Optional[PyDecimal] = None
    payment_terms: Optional[int] = Field(None, ge=0, le=365)
    discount_percentage: Optional[PyDecimal] = None
    is_active: Optional[bool] = None
    on_hold: Optional[bool] = None


class CustomerResponse(CustomerBase):
    id: int
    balance: PyDecimal
    turnover_ytd: PyDecimal
    turnover_last_year: PyDecimal
    last_payment_date: Optional[datetime]
    last_invoice_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Invoice Schemas
class InvoiceLineBase(BaseModel):
    stock_code: Optional[str] = Field(None, max_length=13)
    description: str = Field(..., max_length=60)
    quantity: PyDecimal
    unit_price: PyDecimal
    discount_percent: Optional[PyDecimal] = Field(default=PyDecimal("0.00"))
    vat_code: str = Field(default="S", max_length=1)
    gl_account: Optional[str] = Field(None, max_length=8)
    analysis_code1: Optional[str] = Field(None, max_length=10)
    analysis_code2: Optional[str] = Field(None, max_length=10)
    analysis_code3: Optional[str] = Field(None, max_length=10)
    
    @field_validator('quantity', 'unit_price', 'discount_percent', mode='before')
    @classmethod
    def validate_decimal(cls, v):
        if v is not None:
            return PyDecimal(str(v))
        return v


class InvoiceLineCreate(InvoiceLineBase):
    pass


class InvoiceLineResponse(InvoiceLineBase):
    id: int
    line_number: int
    net_amount: PyDecimal
    vat_rate: PyDecimal
    vat_amount: PyDecimal
    
    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    customer_id: int
    invoice_date: Optional[datetime] = None
    invoice_type: InvoiceType = Field(default=InvoiceType.INVOICE)
    customer_reference: Optional[str] = Field(None, max_length=30)
    order_number: Optional[str] = Field(None, max_length=20)
    delivery_note: Optional[str] = Field(None, max_length=20)
    delivery_name: Optional[str] = Field(None, max_length=60)
    delivery_address1: Optional[str] = Field(None, max_length=60)
    delivery_address2: Optional[str] = Field(None, max_length=60)
    delivery_address3: Optional[str] = Field(None, max_length=60)
    delivery_postcode: Optional[str] = Field(None, max_length=10)
    notes: Optional[str] = Field(None, max_length=500)


class InvoiceCreate(InvoiceBase):
    lines: List[InvoiceLineCreate]
    header_discount_pct: Optional[PyDecimal] = Field(default=PyDecimal("0.00"))
    extra_charges: Optional[PyDecimal] = Field(default=PyDecimal("0.00"))
    shipping_charge: Optional[PyDecimal] = Field(default=PyDecimal("0.00"))
    cash_sale: bool = Field(default=False)
    
    @field_validator('header_discount_pct', 'extra_charges', 'shipping_charge', mode='before')
    @classmethod
    def validate_decimal(cls, v):
        if v is not None:
            return PyDecimal(str(v))
        return v


class InvoiceResponse(InvoiceBase):
    id: int
    invoice_number: str
    currency_code: str
    exchange_rate: PyDecimal
    payment_terms: int
    due_date: datetime
    settlement_discount: PyDecimal
    settlement_days: int
    goods_total: PyDecimal
    discount_total: PyDecimal
    net_total: PyDecimal
    vat_total: PyDecimal
    gross_total: PyDecimal
    amount_paid: PyDecimal
    balance: PyDecimal
    is_paid: bool
    gl_posted: bool
    period_number: Optional[int]
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse]
    
    class Config:
        from_attributes = True


# Order Schemas
class OrderLineCreate(BaseModel):
    stock_code: Optional[str] = Field(None, max_length=13)
    description: str = Field(..., max_length=60)
    quantity_ordered: PyDecimal
    unit_price: PyDecimal
    discount_percent: Optional[PyDecimal] = Field(default=PyDecimal("0.00"))
    vat_code: str = Field(default="S", max_length=1)
    promised_date: Optional[date] = None
    
    @field_validator('quantity_ordered', 'unit_price', 'discount_percent', mode='before')
    @classmethod
    def validate_decimal(cls, v):
        if v is not None:
            return PyDecimal(str(v))
        return v


class OrderCreate(BaseModel):
    customer_id: int
    order_date: Optional[datetime] = None
    customer_reference: Optional[str] = Field(None, max_length=30)
    sales_rep: Optional[str] = Field(None, max_length=10)
    required_date: Optional[datetime] = None
    delivery_name: Optional[str] = Field(None, max_length=60)
    delivery_address1: Optional[str] = Field(None, max_length=60)
    delivery_address2: Optional[str] = Field(None, max_length=60)
    delivery_address3: Optional[str] = Field(None, max_length=60)
    delivery_postcode: Optional[str] = Field(None, max_length=10)
    notes: Optional[str] = Field(None, max_length=500)
    lines: List[OrderLineCreate]


# Payment Schemas
class PaymentCreate(BaseModel):
    customer_id: int
    payment_date: Optional[datetime] = None
    payment_method: str = Field(..., max_length=20)
    payment_amount: PyDecimal
    reference: Optional[str] = Field(None, max_length=30)
    bank_reference: Optional[str] = Field(None, max_length=30)
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator('payment_amount', mode='before')
    @classmethod
    def validate_decimal(cls, v):
        if v is not None:
            return PyDecimal(str(v))
        return v


class PaymentAllocationCreate(BaseModel):
    invoice_id: int
    allocated_amount: PyDecimal
    discount_taken: Optional[PyDecimal] = Field(default=PyDecimal("0.00"))
    
    @field_validator('allocated_amount', 'discount_taken', mode='before')
    @classmethod
    def validate_decimal(cls, v):
        if v is not None:
            return PyDecimal(str(v))
        return v


# Report Schemas
class CustomerStatementRequest(BaseModel):
    customer_id: int
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    include_paid: bool = Field(default=False)
    include_allocations: bool = Field(default=True)


class AgedDebtorsRequest(BaseModel):
    as_of_date: Optional[date] = None
    include_zero_balance: bool = Field(default=False)
    analysis_code: Optional[str] = None
    aging_periods: List[int] = Field(default=[30, 60, 90, 120])


class SalesAnalysisRequest(BaseModel):
    from_date: date
    to_date: date
    group_by: str = Field(default="customer", pattern="^(customer|product|analysis1|analysis2|analysis3)$")
    include_details: bool = Field(default=False)