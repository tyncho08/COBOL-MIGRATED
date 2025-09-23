"""
Main API Router for V1
Combines all API routers into single entry point
"""
from fastapi import APIRouter

# Skip auth router since it's handled in main.py
from .users import router as users_router
from .purchase_orders import router as purchase_orders_router
from .goods_receipts import router as goods_receipts_router
from .purchase_invoices import router as purchase_invoices_router
from .supplier_payments import router as supplier_payments_router
from .sales import router as sales_router
from .sales_orders import router as sales_orders_router
from .sales_invoices import router as sales_invoices_router
from .customer_payments import router as customer_payments_router
from .stock_items import router as stock_items_router
from .stock_takes import router as stock_takes_router
from .chart_of_accounts import router as chart_of_accounts_router
from .journal_entries import router as journal_entries_router
from .gl_batches import router as gl_batches_router
from .financial_reports import router as financial_reports_router
from .budgets import router as budgets_router
from .suppliers import router as suppliers_router
from .customers import router as customers_router
from .system import router as system_router

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all sub-routers
# auth_router is handled in main.py
api_router.include_router(users_router)
api_router.include_router(purchase_orders_router)
api_router.include_router(goods_receipts_router)
api_router.include_router(purchase_invoices_router)
api_router.include_router(supplier_payments_router)
api_router.include_router(sales_router)
api_router.include_router(sales_orders_router)
api_router.include_router(sales_invoices_router)
api_router.include_router(customer_payments_router)
api_router.include_router(stock_items_router)
api_router.include_router(stock_takes_router)
api_router.include_router(chart_of_accounts_router)
api_router.include_router(journal_entries_router)
api_router.include_router(gl_batches_router)
api_router.include_router(financial_reports_router)
api_router.include_router(budgets_router)
api_router.include_router(suppliers_router)
api_router.include_router(customers_router)
api_router.include_router(system_router)

# Health check endpoint
@api_router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

# API info endpoint
@api_router.get("/")
def api_info():
    """API information"""
    return {
        "name": "ACAS API",
        "version": "1.0.0",
        "description": "Applewood Computers Accounting System - Migrated from COBOL",
        "endpoints": {
            "purchase_ledger": {
                "purchase_orders": "/purchase-orders",
                "goods_receipts": "/goods-receipts", 
                "purchase_invoices": "/purchase-invoices",
                "supplier_payments": "/supplier-payments"
            },
            "sales_ledger": {
                "sales": "/sales",
                "sales_orders": "/sales-orders",
                "sales_invoices": "/sales-invoices",
                "customer_payments": "/customer-payments"
            },
            "stock_control": {
                "stock_items": "/stock-items",
                "stock_takes": "/stock-takes"
            },
            "general_ledger": {
                "chart_of_accounts": "/chart-of-accounts",
                "journal_entries": "/journal-entries",
                "gl_batches": "/gl-batches",
                "financial_reports": "/financial-reports",
                "budgets": "/budgets"
            },
            "master_data": {
                "suppliers": "/suppliers",
                "customers": "/customers"
            },
            "system": {
                "administration": "/system"
            }
        }
    }