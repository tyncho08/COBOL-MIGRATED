"""
Chart of Accounts Service
Migrated from COBOL gl010.cbl, gl020.cbl, gl030.cbl
Handles chart of accounts maintenance and structure
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from app.models.general_ledger import (
    ChartOfAccounts, AccountType, AccountBalance,
    JournalLine
)
from app.models.system import CompanyPeriod
from app.services.base import BaseService


class ChartOfAccountsService(BaseService):
    """Chart of accounts management service"""
    
    def create_account(
        self,
        account_code: str,
        account_name: str,
        account_type: AccountType,
        parent_account: Optional[str] = None,
        is_header: bool = False,
        currency_code: str = "USD",
        allow_posting: bool = True,
        budget_enabled: bool = False,
        notes: Optional[str] = None,
        user_id: int = None
    ) -> ChartOfAccounts:
        """
        Create new GL account
        Migrated from gl010.cbl CREATE-ACCOUNT
        """
        try:
            # Validate account code format
            if not self._validate_account_code(account_code):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid account code format. Must be ####.####"
                )
            
            # Check for duplicate
            existing = self.db.query(ChartOfAccounts).filter(
                ChartOfAccounts.account_code == account_code
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Account {account_code} already exists"
                )
            
            # Validate parent account
            parent_level = 0
            if parent_account:
                parent = self.db.query(ChartOfAccounts).filter(
                    ChartOfAccounts.account_code == parent_account
                ).first()
                if not parent:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Parent account {parent_account} not found"
                    )
                if not parent.is_header:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Parent account must be a header account"
                    )
                parent_level = parent.level
            
            # Determine level based on account code
            level = self._determine_account_level(account_code)
            
            # Header accounts cannot allow posting
            if is_header:
                allow_posting = False
            
            # Create account
            account = ChartOfAccounts(
                account_code=account_code,
                account_name=account_name,
                account_type=account_type,
                parent_account=parent_account,
                is_header=is_header,
                level=level,
                is_active=True,
                allow_posting=allow_posting,
                currency_code=currency_code,
                budget_enabled=budget_enabled,
                notes=notes,
                opening_balance=Decimal("0"),
                current_balance=Decimal("0"),
                ytd_movement=Decimal("0"),
                created_by=str(user_id) if user_id else None
            )
            
            self.db.add(account)
            self.db.commit()
            self.db.refresh(account)
            
            # Create initial balance record for current period
            self._create_initial_balance_record(account)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="chart_of_accounts",
                record_id=str(account.id),
                operation="CREATE",
                user_id=user_id,
                details=f"Created GL account {account_code} - {account_name}"
            )
            
            return account
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating account: {str(e)}"
            )
    
    def update_account(
        self,
        account_id: int,
        updates: Dict,
        user_id: int = None
    ) -> ChartOfAccounts:
        """
        Update GL account
        Migrated from gl020.cbl UPDATE-ACCOUNT
        """
        try:
            account = self.db.query(ChartOfAccounts).filter(
                ChartOfAccounts.id == account_id
            ).first()
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found"
                )
            
            # Track changes
            changes = {}
            
            # Update allowed fields
            updatable_fields = [
                "account_name", "is_active", "allow_posting",
                "budget_enabled", "default_vat_code", "notes",
                "analysis_code1_required", "analysis_code2_required",
                "analysis_code3_required"
            ]
            
            for field in updatable_fields:
                if field in updates:
                    old_value = getattr(account, field)
                    new_value = updates[field]
                    if old_value != new_value:
                        # Special validation for certain fields
                        if field == "allow_posting" and account.is_header and new_value:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Header accounts cannot allow posting"
                            )
                        
                        changes[field] = {"old": old_value, "new": new_value}
                        setattr(account, field, new_value)
            
            account.updated_at = datetime.now()
            account.updated_by = str(user_id) if user_id else None
            
            self.db.commit()
            self.db.refresh(account)
            
            # Create audit trail
            if changes:
                self._create_audit_trail(
                    table_name="chart_of_accounts",
                    record_id=str(account.id),
                    operation="UPDATE",
                    user_id=user_id,
                    details=f"Updated GL account {account.account_code}",
                    changes=changes
                )
            
            return account
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating account: {str(e)}"
            )
    
    def get_account_structure(
        self,
        parent_code: Optional[str] = None,
        account_type: Optional[AccountType] = None,
        active_only: bool = True
    ) -> List[Dict]:
        """
        Get hierarchical account structure
        Migrated from gl030.cbl ACCOUNT-HIERARCHY
        """
        try:
            # Build query
            query = self.db.query(ChartOfAccounts)
            
            if active_only:
                query = query.filter(ChartOfAccounts.is_active == True)
            
            if account_type:
                query = query.filter(ChartOfAccounts.account_type == account_type)
            
            if parent_code is not None:
                query = query.filter(ChartOfAccounts.parent_account == parent_code)
            else:
                # Get top-level accounts
                query = query.filter(ChartOfAccounts.parent_account.is_(None))
            
            accounts = query.order_by(ChartOfAccounts.account_code).all()
            
            # Build hierarchical structure
            account_tree = []
            for account in accounts:
                account_dict = {
                    "id": account.id,
                    "account_code": account.account_code,
                    "account_name": account.account_name,
                    "account_type": account.account_type.value,
                    "is_header": account.is_header,
                    "level": account.level,
                    "allow_posting": account.allow_posting,
                    "current_balance": account.current_balance,
                    "ytd_movement": account.ytd_movement,
                    "children": self.get_account_structure(
                        parent_code=account.account_code,
                        account_type=account_type,
                        active_only=active_only
                    ) if account.is_header else []
                }
                account_tree.append(account_dict)
            
            return account_tree
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving account structure: {str(e)}"
            )
    
    def get_account_balances(
        self,
        period_id: Optional[int] = None,
        account_type: Optional[AccountType] = None,
        include_zero_balance: bool = False
    ) -> List[Dict]:
        """
        Get account balances
        Migrated from gl030.cbl ACCOUNT-BALANCES
        """
        try:
            # Get period
            if period_id:
                period = self.db.query(CompanyPeriod).filter(
                    CompanyPeriod.id == period_id
                ).first()
            else:
                period = self._get_current_period()
            
            if not period:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Period not found"
                )
            
            # Query accounts with balances
            query = self.db.query(
                ChartOfAccounts,
                AccountBalance
            ).outerjoin(
                AccountBalance,
                and_(
                    AccountBalance.account_id == ChartOfAccounts.id,
                    AccountBalance.period_id == period.id
                )
            )
            
            if account_type:
                query = query.filter(ChartOfAccounts.account_type == account_type)
            
            if not include_zero_balance:
                query = query.filter(
                    or_(
                        AccountBalance.closing_balance != 0,
                        AccountBalance.period_debits != 0,
                        AccountBalance.period_credits != 0
                    )
                )
            
            results = query.order_by(ChartOfAccounts.account_code).all()
            
            # Format results
            balances = []
            for account, balance in results:
                balance_dict = {
                    "account_id": account.id,
                    "account_code": account.account_code,
                    "account_name": account.account_name,
                    "account_type": account.account_type.value,
                    "period": period.period_number,
                    "year": period.year_number,
                    "opening_balance": balance.opening_balance if balance else Decimal("0"),
                    "period_debits": balance.period_debits if balance else Decimal("0"),
                    "period_credits": balance.period_credits if balance else Decimal("0"),
                    "closing_balance": balance.closing_balance if balance else Decimal("0"),
                    "ytd_movement": (
                        (balance.period_debits - balance.period_credits)
                        if balance else Decimal("0")
                    )
                }
                balances.append(balance_dict)
            
            return balances
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving balances: {str(e)}"
            )
    
    def validate_account_code(
        self,
        account_code: str
    ) -> bool:
        """
        Validate account code exists and can accept postings
        Migrated from gl030.cbl VALIDATE-ACCOUNT
        """
        try:
            account = self.db.query(ChartOfAccounts).filter(
                ChartOfAccounts.account_code == account_code
            ).first()
            
            if not account:
                return False
            
            if not account.is_active:
                return False
            
            if not account.allow_posting:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_control_accounts(
        self,
        control_type: Optional[str] = None
    ) -> List[ChartOfAccounts]:
        """
        Get control accounts
        Migrated from gl030.cbl GET-CONTROL-ACCOUNTS
        """
        try:
            query = self.db.query(ChartOfAccounts).filter(
                and_(
                    ChartOfAccounts.is_control == True,
                    ChartOfAccounts.is_active == True
                )
            )
            
            if control_type:
                query = query.filter(ChartOfAccounts.control_type == control_type)
            
            return query.order_by(ChartOfAccounts.account_code).all()
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving control accounts: {str(e)}"
            )
    
    def reconcile_control_account(
        self,
        account_id: int,
        period_id: int,
        user_id: int
    ) -> Dict:
        """
        Reconcile control account with sub-ledger
        Migrated from gl030.cbl RECONCILE-CONTROL
        """
        try:
            # Get account
            account = self.db.query(ChartOfAccounts).filter(
                ChartOfAccounts.id == account_id
            ).first()
            if not account or not account.is_control:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Control account not found"
                )
            
            # Get GL balance
            gl_balance = self.db.query(AccountBalance).filter(
                and_(
                    AccountBalance.account_id == account_id,
                    AccountBalance.period_id == period_id
                )
            ).first()
            
            gl_total = gl_balance.closing_balance if gl_balance else Decimal("0")
            
            # Get sub-ledger balance based on control type
            sub_ledger_total = Decimal("0")
            
            if account.control_type == "DEBTORS":
                # Get customer balances
                from app.models.customers import Customer
                result = self.db.query(func.sum(Customer.balance)).scalar()
                sub_ledger_total = result or Decimal("0")
                
            elif account.control_type == "CREDITORS":
                # Get supplier balances
                from app.models.suppliers import Supplier
                result = self.db.query(func.sum(Supplier.balance)).scalar()
                sub_ledger_total = result or Decimal("0")
                
            elif account.control_type == "STOCK":
                # Get stock valuation
                from app.services.stock_control import StockValuationService
                stock_service = StockValuationService(self.db)
                valuation = stock_service.calculate_stock_value()
                sub_ledger_total = valuation["total_value_cost"]
            
            # Calculate difference
            difference = gl_total - sub_ledger_total
            is_reconciled = difference == 0
            
            # Create reconciliation record
            reconciliation = {
                "account_code": account.account_code,
                "account_name": account.account_name,
                "control_type": account.control_type,
                "period_id": period_id,
                "gl_balance": gl_total,
                "sub_ledger_balance": sub_ledger_total,
                "difference": difference,
                "is_reconciled": is_reconciled,
                "reconciled_date": datetime.now(),
                "reconciled_by": str(user_id)
            }
            
            # Create audit trail
            self._create_audit_trail(
                table_name="control_reconciliations",
                record_id=f"{account_id}_{period_id}",
                operation="RECONCILE",
                user_id=user_id,
                details=f"Control account reconciliation: {account.account_code}",
                changes=reconciliation
            )
            
            return reconciliation
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reconciling control account: {str(e)}"
            )
    
    def _validate_account_code(self, account_code: str) -> bool:
        """Validate account code format (####.####)"""
        import re
        pattern = r'^\d{4}\.\d{4}$'
        return bool(re.match(pattern, account_code))
    
    def _determine_account_level(self, account_code: str) -> int:
        """Determine account level from code"""
        main_code, sub_code = account_code.split('.')
        
        if sub_code == "0000":
            return 0  # Main account
        elif sub_code.endswith("00"):
            return 1  # Sub-account
        else:
            return 2  # Detail account
    
    def _create_initial_balance_record(self, account: ChartOfAccounts):
        """Create initial balance record for new account"""
        try:
            current_period = self._get_current_period()
            if current_period:
                balance = AccountBalance(
                    account_id=account.id,
                    period_id=current_period.id,
                    opening_balance=Decimal("0"),
                    period_debits=Decimal("0"),
                    period_credits=Decimal("0"),
                    closing_balance=Decimal("0")
                )
                self.db.add(balance)
                self.db.commit()
        except Exception:
            # Non-critical error
            pass