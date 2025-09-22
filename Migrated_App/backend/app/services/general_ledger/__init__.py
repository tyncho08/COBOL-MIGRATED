"""
General Ledger Services Package
Migrated from COBOL GL programs (gl*.cbl)
Complete GL functionality including chart of accounts, journals, batches, 
period-end, budgets, reporting, inquiries, and bank reconciliation
"""

from .chart_of_accounts_service import ChartOfAccountsService
from .journal_entry_service import JournalEntryService
from .gl_batch_service import GLBatchService
from .period_end_service import PeriodEndService
from .budget_service import BudgetService
from .reporting_service import ReportingService
from .gl_inquiry_service import GLInquiryService
from .bank_reconciliation_service import BankReconciliationService

__all__ = [
    "ChartOfAccountsService",
    "JournalEntryService", 
    "GLBatchService",
    "PeriodEndService",
    "BudgetService",
    "ReportingService",
    "GLInquiryService",
    "BankReconciliationService"
]

# Service mapping for easy access
GL_SERVICES = {
    "chart_of_accounts": ChartOfAccountsService,
    "journal_entry": JournalEntryService,
    "gl_batch": GLBatchService,
    "period_end": PeriodEndService,
    "budget": BudgetService,
    "reporting": ReportingService,
    "gl_inquiry": GLInquiryService,
    "bank_reconciliation": BankReconciliationService
}

def get_gl_service(service_name: str, db_session):
    """
    Factory function to get GL service instance
    
    Args:
        service_name: Name of the service (key from GL_SERVICES)
        db_session: Database session
    
    Returns:
        Service instance
    
    Example:
        chart_service = get_gl_service("chart_of_accounts", db)
    """
    if service_name not in GL_SERVICES:
        raise ValueError(f"Unknown GL service: {service_name}. Available: {list(GL_SERVICES.keys())}")
    
    service_class = GL_SERVICES[service_name]
    return service_class(db_session)