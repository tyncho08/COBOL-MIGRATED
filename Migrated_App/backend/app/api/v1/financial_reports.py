"""
Financial Reports API Router
REST endpoints for financial reporting
"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.general_ledger.reporting_service import ReportingService
from app.services.general_ledger.period_end_service import PeriodEndService
from app.models.general_ledger import AccountType

router = APIRouter(prefix="/financial-reports", tags=["Financial Reports"])


@router.get("/balance-sheet")
def generate_balance_sheet(
    period_id: int = Query(...),
    comparative_period_id: Optional[int] = Query(None),
    show_details: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Generate balance sheet"""
    service = ReportingService(db)
    report = service.generate_balance_sheet(
        period_id=period_id,
        comparative_period_id=comparative_period_id,
        show_details=show_details
    )
    return report


@router.get("/income-statement")
def generate_income_statement(
    period_id: int = Query(...),
    comparative_period_id: Optional[int] = Query(None),
    show_details: bool = Query(True),
    ytd: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Generate income statement (P&L)"""
    service = ReportingService(db)
    report = service.generate_income_statement(
        period_id=period_id,
        comparative_period_id=comparative_period_id,
        show_details=show_details,
        ytd=ytd
    )
    return report


@router.get("/cash-flow-statement")
def generate_cash_flow_statement(
    period_id: int = Query(...),
    ytd: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Generate cash flow statement"""
    service = ReportingService(db)
    report = service.generate_cash_flow_statement(
        period_id=period_id,
        ytd=ytd
    )
    return report


@router.get("/trial-balance")
def generate_trial_balance(
    period_id: int = Query(...),
    include_zero_balance: bool = Query(False),
    account_type: Optional[AccountType] = Query(None),
    db: Session = Depends(get_db)
):
    """Generate trial balance"""
    service = PeriodEndService(db)
    report = service.get_trial_balance(
        period_id=period_id,
        include_zero_balance=include_zero_balance,
        account_type=account_type
    )
    return report


@router.get("/account-detail")
def generate_account_detail_report(
    account_code: str = Query(...),
    from_period_id: int = Query(...),
    to_period_id: int = Query(...),
    include_journal_detail: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Generate detailed account activity report"""
    service = ReportingService(db)
    report = service.generate_account_detail_report(
        account_code=account_code,
        from_period_id=from_period_id,
        to_period_id=to_period_id,
        include_journal_detail=include_journal_detail
    )
    return report


@router.get("/budget-variance")
def generate_budget_variance_report(
    budget_id: int = Query(...),
    period_id: Optional[int] = Query(None),
    variance_threshold: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    """Generate budget vs actual variance report"""
    from app.services.general_ledger.budget_service import BudgetService
    service = BudgetService(db)
    report = service.get_budget_variance_report(
        budget_id=budget_id,
        period_id=period_id,
        variance_threshold=variance_threshold
    )
    return report


@router.get("/period-summary")
def get_period_summary(
    period_id: int = Query(...),
    account_type: Optional[AccountType] = Query(None),
    db: Session = Depends(get_db)
):
    """Get period summary with totals"""
    from app.services.general_ledger.gl_inquiry_service import GLInquiryService
    service = GLInquiryService(db)
    summary = service.get_period_summary(
        period_id=period_id,
        account_type=account_type
    )
    return summary


@router.get("/account-history")
def get_account_history(
    account_code: str = Query(...),
    year_number: int = Query(...),
    include_balances: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get account history for entire year"""
    from app.services.general_ledger.gl_inquiry_service import GLInquiryService
    service = GLInquiryService(db)
    history = service.get_account_history(
        account_code=account_code,
        year_number=year_number,
        include_balances=include_balances
    )
    return history


@router.get("/bank-reconciliation")
def get_bank_reconciliation_report(
    reconciliation_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Generate bank reconciliation report"""
    from app.services.general_ledger.bank_reconciliation_service import BankReconciliationService
    service = BankReconciliationService(db)
    report = service.get_reconciliation_report(reconciliation_id)
    return report


@router.get("/financial-package")
def generate_financial_package(
    period_id: int = Query(...),
    comparative_period_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Generate complete financial package (BS, P&L, CF)"""
    service = ReportingService(db)
    
    # Generate all three main reports
    balance_sheet = service.generate_balance_sheet(
        period_id=period_id,
        comparative_period_id=comparative_period_id,
        show_details=True
    )
    
    income_statement = service.generate_income_statement(
        period_id=period_id,
        comparative_period_id=comparative_period_id,
        show_details=True,
        ytd=True
    )
    
    cash_flow = service.generate_cash_flow_statement(
        period_id=period_id,
        ytd=True
    )
    
    return {
        "financial_package": {
            "balance_sheet": balance_sheet,
            "income_statement": income_statement,
            "cash_flow_statement": cash_flow
        }
    }