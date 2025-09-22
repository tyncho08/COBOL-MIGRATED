"""
Chart of Accounts API Router
REST endpoints for chart of accounts management
"""
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.general_ledger.chart_of_accounts_service import ChartOfAccountsService
from app.models.general_ledger import AccountType

router = APIRouter(prefix="/chart-of-accounts", tags=["Chart of Accounts"])


# Pydantic models
class AccountCreate(BaseModel):
    account_code: str = Field(..., regex=r'^\d{4}\.\d{4}$')
    account_name: str
    account_type: AccountType
    parent_account: Optional[str] = None
    is_header: bool = False
    currency_code: str = "USD"
    allow_posting: bool = True
    budget_enabled: bool = False
    notes: Optional[str] = None


class AccountUpdate(BaseModel):
    account_name: Optional[str] = None
    is_active: Optional[bool] = None
    allow_posting: Optional[bool] = None
    budget_enabled: Optional[bool] = None
    default_vat_code: Optional[str] = None
    notes: Optional[str] = None
    analysis_code1_required: Optional[bool] = None
    analysis_code2_required: Optional[bool] = None
    analysis_code3_required: Optional[bool] = None


class AccountResponse(BaseModel):
    id: int
    account_code: str
    account_name: str
    account_type: str
    is_header: bool
    level: int
    allow_posting: bool
    current_balance: Decimal
    ytd_movement: Decimal
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=AccountResponse)
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create new GL account"""
    service = ChartOfAccountsService(db)
    account = service.create_account(
        **account_data.dict(),
        user_id=current_user_id
    )
    return account


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    """Get account by ID"""
    service = ChartOfAccountsService(db)
    from app.models.general_ledger import ChartOfAccounts
    account = db.query(ChartOfAccounts).filter(ChartOfAccounts.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return account


@router.get("/by-code/{account_code}", response_model=AccountResponse)
def get_account_by_code(
    account_code: str,
    db: Session = Depends(get_db)
):
    """Get account by code"""
    service = ChartOfAccountsService(db)
    from app.models.general_ledger import ChartOfAccounts
    account = db.query(ChartOfAccounts).filter(ChartOfAccounts.account_code == account_code).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return account


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Update GL account"""
    service = ChartOfAccountsService(db)
    account = service.update_account(
        account_id=account_id,
        updates=account_data.dict(exclude_unset=True),
        user_id=current_user_id
    )
    return account


@router.get("/structure")
def get_account_structure(
    parent_code: Optional[str] = Query(None),
    account_type: Optional[AccountType] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get hierarchical account structure"""
    service = ChartOfAccountsService(db)
    structure = service.get_account_structure(
        parent_code=parent_code,
        account_type=account_type,
        active_only=active_only
    )
    return {"structure": structure}


@router.get("/balances")
def get_account_balances(
    period_id: Optional[int] = Query(None),
    account_type: Optional[AccountType] = Query(None),
    include_zero_balance: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Get account balances"""
    service = ChartOfAccountsService(db)
    balances = service.get_account_balances(
        period_id=period_id,
        account_type=account_type,
        include_zero_balance=include_zero_balance
    )
    return {"balances": balances}


@router.post("/validate/{account_code}")
def validate_account_code(
    account_code: str,
    db: Session = Depends(get_db)
):
    """Validate account code for posting"""
    service = ChartOfAccountsService(db)
    is_valid = service.validate_account_code(account_code)
    return {"account_code": account_code, "is_valid": is_valid}


@router.get("/control-accounts")
def get_control_accounts(
    control_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get control accounts"""
    service = ChartOfAccountsService(db)
    accounts = service.get_control_accounts(control_type)
    return {"control_accounts": accounts}


@router.post("/{account_id}/reconcile")
def reconcile_control_account(
    account_id: int,
    period_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Reconcile control account with sub-ledger"""
    service = ChartOfAccountsService(db)
    reconciliation = service.reconcile_control_account(
        account_id=account_id,
        period_id=period_id,
        user_id=current_user_id
    )
    return reconciliation


@router.get("/")
def search_accounts(
    search_term: Optional[str] = Query(None),
    account_type: Optional[AccountType] = Query(None),
    is_header: Optional[bool] = Query(None),
    allow_posting: Optional[bool] = Query(None),
    active_only: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search chart of accounts"""
    from app.services.general_ledger.gl_inquiry_service import GLInquiryService
    service = GLInquiryService(db)
    result = service.search_accounts(
        search_term=search_term,
        account_type=account_type,
        is_header=is_header,
        allow_posting=allow_posting,
        active_only=active_only,
        page=page,
        page_size=page_size
    )
    return result