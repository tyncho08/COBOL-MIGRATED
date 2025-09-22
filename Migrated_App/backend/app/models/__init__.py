"""
Database Models
Import all models to ensure they are registered with SQLAlchemy
"""
from .system import SystemConfig, User, AuditTrail, CompanyPeriod, SystemParameter
from .customers import Customer, CustomerContact, CustomerCreditHistory
from .suppliers import Supplier
from .stock import StockItem, StockMovement, StockValuation
from .transactions import (
    SalesOrder, SalesOrderLine, 
    SalesInvoice, SalesInvoiceLine,
    CustomerPayment, PaymentAllocation,
    TransactionStatus, InvoiceType
)
from .purchase_transactions import (
    PurchaseOrder, PurchaseOrderLine,
    GoodsReceipt, GoodsReceiptLine,
    PurchaseInvoice, PurchaseInvoiceLine,
    SupplierPayment, SupplierPaymentAllocation,
    PurchaseOrderStatus, GoodsReceiptStatus
)
from .general_ledger import (
    ChartOfAccounts, JournalHeader, JournalLine,
    GLBatch, AccountBalance, BudgetHeader, BudgetLine,
    BankReconciliation,
    AccountType, JournalType, PostingStatus
)
from .irs_system import (
    IRSConfiguration, IRSCategory, IRSEntry,
    IRSPostingBatch, IRSReport, IRSCapitalAsset,
    IRSTransactionType, IRSPostingStatus
)
from .control_tables import (
    AnalysisCodeMaster, VATCodeMaster, VATRateHistory,
    Currency, ExchangeRateHistory,
    DeliveryNote, BackOrder,
    NumberSequence, DocumentAttachment, EmailQueue
)

__all__ = [
    # System
    "SystemConfig", "User", "AuditTrail", "CompanyPeriod", "SystemParameter",
    # Sales
    "Customer", "CustomerContact", "CustomerCreditHistory",
    # Purchase
    "Supplier",
    # Stock
    "StockItem", "StockMovement", "StockValuation",
    # Sales Transactions
    "SalesOrder", "SalesOrderLine",
    "SalesInvoice", "SalesInvoiceLine",
    "CustomerPayment", "PaymentAllocation",
    "TransactionStatus", "InvoiceType",
    # Purchase Transactions
    "PurchaseOrder", "PurchaseOrderLine",
    "GoodsReceipt", "GoodsReceiptLine",
    "PurchaseInvoice", "PurchaseInvoiceLine",
    "SupplierPayment", "SupplierPaymentAllocation",
    "PurchaseOrderStatus", "GoodsReceiptStatus",
    # General Ledger
    "ChartOfAccounts", "JournalHeader", "JournalLine",
    "GLBatch", "AccountBalance", "BudgetHeader", "BudgetLine",
    "BankReconciliation",
    "AccountType", "JournalType", "PostingStatus",
    # IRS System
    "IRSConfiguration", "IRSCategory", "IRSEntry",
    "IRSPostingBatch", "IRSReport", "IRSCapitalAsset",
    "IRSTransactionType", "IRSPostingStatus",
    # Control Tables
    "AnalysisCodeMaster", "VATCodeMaster", "VATRateHistory",
    "Currency", "ExchangeRateHistory",
    "DeliveryNote", "BackOrder",
    "NumberSequence", "DocumentAttachment", "EmailQueue",
]