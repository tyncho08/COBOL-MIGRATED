"""ACAS Router Module - Central import point for all routers"""

from .auth import router as auth_router
from .sales import router as sales_router
from .purchase import router as purchase_router
from .stock import router as stock_router
from .general import router as general_router
from .irs import router as irs_router
from .system import router as system_router

__all__ = [
    "auth_router",
    "sales_router",
    "purchase_router",
    "stock_router",
    "general_router",
    "irs_router",
    "system_router"
]