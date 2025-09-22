"""
Period End Service
Migrated from COBOL gl900.cbl, gl910.cbl, gl920.cbl
Handles period and year-end processing
"""
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from app.models.general_ledger import (
    ChartOfAccounts, AccountType, AccountBalance,
    JournalHeader, JournalLine, JournalType, PostingStatus
)
from app.models.system import CompanyPeriod, SystemConfig
from app.services.base import BaseService
from app.services.general_ledger.journal_entry_service import JournalEntryService


class PeriodEndService(BaseService):
    """Period and year-end processing service"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.journal_service = JournalEntryService(db)
    
    def validate_period_close(
        self,
        period_id: int,
        user_id: int
    ) -> Dict:
        """
        Validate period can be closed
        Migrated from gl900.cbl VALIDATE-PERIOD
        """
        try:
            # Get period
            period = self.db.query(CompanyPeriod).filter(
                CompanyPeriod.id == period_id
            ).first()
            if not period:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Period not found"
                )
            
            validation_errors = []
            warnings = []
            
            # Check if period is already closed
            if not period.is_open:
                validation_errors.append({
                    "type": "ALREADY_CLOSED",
                    "message": "Period is already closed"
                })
            
            # Check for unposted journals
            unposted_count = self.db.query(JournalHeader).filter(
                and_(
                    JournalHeader.period_id == period_id,
                    JournalHeader.posting_status == PostingStatus.DRAFT
                )
            ).count()
            
            if unposted_count > 0:
                validation_errors.append({
                    "type": "UNPOSTED_JOURNALS",
                    "message": f"{unposted_count} unposted journals found"
                })
            
            # Check control account reconciliation
            control_accounts = self.db.query(ChartOfAccounts).filter(
                and_(
                    ChartOfAccounts.is_control == True,
                    ChartOfAccounts.is_active == True
                )
            ).all()
            
            for account in control_accounts:
                # Would check reconciliation status
                # For now, just add warning
                warnings.append({
                    "type": "CONTROL_ACCOUNT",
                    "message": f"Verify control account {account.account_code} is reconciled"
                })
            
            # Check sub-ledger closings
            if not period.sl_closed:
                warnings.append({
                    "type": "SUB_LEDGER",
                    "message": "Sales Ledger not closed"
                })
            
            if not period.pl_closed:
                warnings.append({
                    "type": "SUB_LEDGER",
                    "message": "Purchase Ledger not closed"
                })
            
            if not period.stock_closed:
                warnings.append({
                    "type": "SUB_LEDGER",
                    "message": "Stock Control not closed"
                })
            
            return {
                "period_id": period_id,
                "period": f"{period.period_number}/{period.year_number}",
                "can_close": len(validation_errors) == 0,
                "validation_errors": validation_errors,
                "warnings": warnings
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error validating period close: {str(e)}"
            )
    
    def close_period(
        self,
        period_id: int,
        user_id: int
    ) -> CompanyPeriod:
        """
        Close accounting period
        Migrated from gl910.cbl CLOSE-PERIOD
        """
        try:
            # Validate first
            validation = self.validate_period_close(period_id, user_id)
            if not validation["can_close"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Period cannot be closed",
                    errors=validation["validation_errors"]
                )
            
            # Get period
            period = self.db.query(CompanyPeriod).filter(
                CompanyPeriod.id == period_id
            ).first()
            
            # Create closing journal entries if needed
            self._create_period_closing_entries(period, user_id)
            
            # Calculate and store period-end balances
            self._calculate_period_end_balances(period)
            
            # Close the period
            period.is_open = False
            period.is_current = False
            period.gl_closed = True
            period.closed_date = datetime.now()
            period.closed_by = str(user_id)
            
            # Open next period if it exists
            next_period = self.db.query(CompanyPeriod).filter(
                and_(
                    CompanyPeriod.period_number == period.period_number + 1,
                    CompanyPeriod.year_number == period.year_number
                )
            ).first()
            
            if not next_period and period.period_number == 12:
                # Year-end - look for period 1 of next year
                next_period = self.db.query(CompanyPeriod).filter(
                    and_(
                        CompanyPeriod.period_number == 1,
                        CompanyPeriod.year_number == period.year_number + 1
                    )
                ).first()
            
            if next_period:
                next_period.is_current = True
                # Carry forward balances
                self._carry_forward_balances(period, next_period)
            
            self.db.commit()
            self.db.refresh(period)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="company_periods",
                record_id=str(period.id),
                operation="CLOSE",
                user_id=user_id,
                details=f"Closed period {period.period_number}/{period.year_number}"
            )
            
            return period
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error closing period: {str(e)}"
            )
    
    def process_year_end(
        self,
        year_number: int,
        user_id: int
    ) -> Dict:
        """
        Process year-end closing
        Migrated from gl920.cbl YEAR-END-PROCESS
        """
        try:
            # Validate all periods are closed
            open_periods = self.db.query(CompanyPeriod).filter(
                and_(
                    CompanyPeriod.year_number == year_number,
                    CompanyPeriod.is_open == True
                )
            ).all()
            
            if open_periods:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{len(open_periods)} periods still open for year {year_number}"
                )
            
            # Get last period of year
            last_period = self.db.query(CompanyPeriod).filter(
                and_(
                    CompanyPeriod.year_number == year_number,
                    CompanyPeriod.period_number == 12
                )
            ).first()
            
            if not last_period:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Period 12 not found for year {year_number}"
                )
            
            # Create year-end closing entries
            closing_entries = self._create_year_end_entries(last_period, user_id)
            
            # Calculate retained earnings
            retained_earnings = self._calculate_retained_earnings(year_number)
            
            # Create new year periods if needed
            self._create_new_year_periods(year_number + 1, user_id)
            
            # Get first period of new year
            new_year_period = self.db.query(CompanyPeriod).filter(
                and_(
                    CompanyPeriod.year_number == year_number + 1,
                    CompanyPeriod.period_number == 1
                )
            ).first()
            
            if new_year_period:
                # Carry forward balances
                self._carry_forward_year_end_balances(
                    last_period, new_year_period, retained_earnings
                )
            
            self.db.commit()
            
            return {
                "year_closed": year_number,
                "closing_entries": len(closing_entries),
                "retained_earnings": retained_earnings,
                "new_year": year_number + 1,
                "new_year_periods_created": new_year_period is not None
            }
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing year-end: {str(e)}"
            )
    
    def get_trial_balance(
        self,
        period_id: int,
        include_zero_balance: bool = False,
        account_type: Optional[AccountType] = None
    ) -> Dict:
        """
        Get trial balance
        Migrated from gl920.cbl TRIAL-BALANCE
        """
        try:
            # Get period
            period = self.db.query(CompanyPeriod).filter(
                CompanyPeriod.id == period_id
            ).first()
            if not period:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Period not found"
                )
            
            # Query accounts with balances
            query = self.db.query(
                ChartOfAccounts,
                AccountBalance
            ).join(
                AccountBalance,
                and_(
                    AccountBalance.account_id == ChartOfAccounts.id,
                    AccountBalance.period_id == period_id
                )
            )
            
            if account_type:
                query = query.filter(ChartOfAccounts.account_type == account_type)
            
            if not include_zero_balance:
                query = query.filter(
                    or_(
                        AccountBalance.period_debits != 0,
                        AccountBalance.period_credits != 0,
                        AccountBalance.closing_balance != 0
                    )
                )
            
            results = query.order_by(ChartOfAccounts.account_code).all()
            
            # Calculate totals
            total_debits = Decimal("0")
            total_credits = Decimal("0")
            
            accounts = []
            for account, balance in results:
                # Determine debit/credit based on normal balance
                if account.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                    # Normal debit balance
                    if balance.closing_balance >= 0:
                        debit_balance = balance.closing_balance
                        credit_balance = Decimal("0")
                    else:
                        debit_balance = Decimal("0")
                        credit_balance = abs(balance.closing_balance)
                else:
                    # Normal credit balance
                    if balance.closing_balance >= 0:
                        debit_balance = Decimal("0")
                        credit_balance = balance.closing_balance
                    else:
                        debit_balance = abs(balance.closing_balance)
                        credit_balance = Decimal("0")
                
                accounts.append({
                    "account_code": account.account_code,
                    "account_name": account.account_name,
                    "account_type": account.account_type.value,
                    "period_debits": balance.period_debits,
                    "period_credits": balance.period_credits,
                    "debit_balance": debit_balance,
                    "credit_balance": credit_balance
                })
                
                total_debits += debit_balance
                total_credits += credit_balance
            
            return {
                "period": f"{period.period_number}/{period.year_number}",
                "as_at_date": period.end_date,
                "accounts": accounts,
                "totals": {
                    "total_debits": total_debits,
                    "total_credits": total_credits,
                    "difference": total_debits - total_credits
                },
                "is_balanced": total_debits == total_credits
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating trial balance: {str(e)}"
            )
    
    def _create_period_closing_entries(
        self,
        period: CompanyPeriod,
        user_id: int
    ):
        """Create period closing entries if needed"""
        # In many systems, period closing doesn't require entries
        # Year-end closing typically does
        pass
    
    def _create_year_end_entries(
        self,
        period: CompanyPeriod,
        user_id: int
    ) -> List[JournalHeader]:
        """Create year-end closing entries"""
        closing_entries = []
        
        # Close revenue accounts
        revenue_accounts = self.db.query(
            ChartOfAccounts,
            AccountBalance
        ).join(
            AccountBalance,
            and_(
                AccountBalance.account_id == ChartOfAccounts.id,
                AccountBalance.period_id == period.id
            )
        ).filter(
            ChartOfAccounts.account_type == AccountType.INCOME
        ).all()
        
        revenue_total = sum(b.closing_balance for a, b in revenue_accounts)
        
        if revenue_total != 0:
            # Create closing entry for revenue
            revenue_lines = []
            for account, balance in revenue_accounts:
                if balance.closing_balance != 0:
                    revenue_lines.append({
                        "account_code": account.account_code,
                        "debit_amount": balance.closing_balance if balance.closing_balance > 0 else 0,
                        "credit_amount": abs(balance.closing_balance) if balance.closing_balance < 0 else 0,
                        "description": f"Close {account.account_name}"
                    })
            
            # Add P&L summary line
            revenue_lines.append({
                "account_code": "3999.0000",  # P&L Summary account
                "debit_amount": 0 if revenue_total > 0 else abs(revenue_total),
                "credit_amount": revenue_total if revenue_total > 0 else 0,
                "description": "Revenue to P&L Summary"
            })
            
            revenue_journal = self.journal_service.create_journal_entry(
                journal_date=period.end_date,
                journal_type=JournalType.CLOSING,
                description="Year-end: Close revenue accounts",
                journal_lines=revenue_lines,
                auto_post=True,
                user_id=user_id
            )
            closing_entries.append(revenue_journal)
        
        # Close expense accounts
        expense_accounts = self.db.query(
            ChartOfAccounts,
            AccountBalance
        ).join(
            AccountBalance,
            and_(
                AccountBalance.account_id == ChartOfAccounts.id,
                AccountBalance.period_id == period.id
            )
        ).filter(
            ChartOfAccounts.account_type == AccountType.EXPENSE
        ).all()
        
        expense_total = sum(b.closing_balance for a, b in expense_accounts)
        
        if expense_total != 0:
            # Create closing entry for expenses
            expense_lines = []
            for account, balance in expense_accounts:
                if balance.closing_balance != 0:
                    expense_lines.append({
                        "account_code": account.account_code,
                        "debit_amount": abs(balance.closing_balance) if balance.closing_balance < 0 else 0,
                        "credit_amount": balance.closing_balance if balance.closing_balance > 0 else 0,
                        "description": f"Close {account.account_name}"
                    })
            
            # Add P&L summary line
            expense_lines.append({
                "account_code": "3999.0000",  # P&L Summary account
                "debit_amount": expense_total if expense_total > 0 else 0,
                "credit_amount": 0 if expense_total > 0 else abs(expense_total),
                "description": "Expenses to P&L Summary"
            })
            
            expense_journal = self.journal_service.create_journal_entry(
                journal_date=period.end_date,
                journal_type=JournalType.CLOSING,
                description="Year-end: Close expense accounts",
                journal_lines=expense_lines,
                auto_post=True,
                user_id=user_id
            )
            closing_entries.append(expense_journal)
        
        return closing_entries
    
    def _calculate_period_end_balances(self, period: CompanyPeriod):
        """Calculate and store period-end balances"""
        # Already maintained in AccountBalance table
        pass
    
    def _calculate_retained_earnings(self, year_number: int) -> Decimal:
        """Calculate retained earnings for year"""
        # Get P&L for the year
        revenue_total = self.db.query(
            func.sum(AccountBalance.closing_balance)
        ).join(ChartOfAccounts).filter(
            and_(
                ChartOfAccounts.account_type == AccountType.INCOME,
                AccountBalance.period_id.in_(
                    self.db.query(CompanyPeriod.id).filter(
                        CompanyPeriod.year_number == year_number
                    )
                )
            )
        ).scalar() or Decimal("0")
        
        expense_total = self.db.query(
            func.sum(AccountBalance.closing_balance)
        ).join(ChartOfAccounts).filter(
            and_(
                ChartOfAccounts.account_type == AccountType.EXPENSE,
                AccountBalance.period_id.in_(
                    self.db.query(CompanyPeriod.id).filter(
                        CompanyPeriod.year_number == year_number
                    )
                )
            )
        ).scalar() or Decimal("0")
        
        return revenue_total - expense_total
    
    def _carry_forward_balances(
        self,
        from_period: CompanyPeriod,
        to_period: CompanyPeriod
    ):
        """Carry forward balances from one period to next"""
        # Get closing balances
        closing_balances = self.db.query(
            AccountBalance
        ).filter(
            AccountBalance.period_id == from_period.id
        ).all()
        
        for closing in closing_balances:
            # Check if opening balance exists
            opening = self.db.query(AccountBalance).filter(
                and_(
                    AccountBalance.account_id == closing.account_id,
                    AccountBalance.period_id == to_period.id
                )
            ).first()
            
            if not opening:
                # Create opening balance
                opening = AccountBalance(
                    account_id=closing.account_id,
                    period_id=to_period.id,
                    opening_balance=closing.closing_balance,
                    period_debits=Decimal("0"),
                    period_credits=Decimal("0"),
                    closing_balance=closing.closing_balance
                )
                self.db.add(opening)
            else:
                # Update opening balance
                opening.opening_balance = closing.closing_balance
                opening.closing_balance = (
                    opening.opening_balance +
                    opening.period_debits -
                    opening.period_credits
                )
    
    def _carry_forward_year_end_balances(
        self,
        from_period: CompanyPeriod,
        to_period: CompanyPeriod,
        retained_earnings: Decimal
    ):
        """Carry forward year-end balances"""
        # Only carry forward balance sheet accounts
        balance_sheet_accounts = self.db.query(
            ChartOfAccounts,
            AccountBalance
        ).join(
            AccountBalance,
            and_(
                AccountBalance.account_id == ChartOfAccounts.id,
                AccountBalance.period_id == from_period.id
            )
        ).filter(
            ChartOfAccounts.account_type.in_([
                AccountType.ASSET,
                AccountType.LIABILITY,
                AccountType.CAPITAL
            ])
        ).all()
        
        for account, closing in balance_sheet_accounts:
            # Create opening balance
            opening = AccountBalance(
                account_id=account.id,
                period_id=to_period.id,
                opening_balance=closing.closing_balance,
                period_debits=Decimal("0"),
                period_credits=Decimal("0"),
                closing_balance=closing.closing_balance
            )
            self.db.add(opening)
        
        # Add retained earnings to retained earnings account
        if retained_earnings != 0:
            re_account = self.db.query(ChartOfAccounts).filter(
                ChartOfAccounts.account_code == "3100.0000"  # Retained Earnings
            ).first()
            
            if re_account:
                re_balance = AccountBalance(
                    account_id=re_account.id,
                    period_id=to_period.id,
                    opening_balance=retained_earnings,
                    period_debits=Decimal("0"),
                    period_credits=Decimal("0"),
                    closing_balance=retained_earnings
                )
                self.db.add(re_balance)
    
    def _create_new_year_periods(self, year_number: int, user_id: int):
        """Create periods for new year"""
        # Check if periods already exist
        existing = self.db.query(CompanyPeriod).filter(
            CompanyPeriod.year_number == year_number
        ).first()
        
        if existing:
            return
        
        # Get fiscal year start
        config = self.db.query(SystemConfig).first()
        fiscal_start_month = config.fiscal_year_start if config else 1
        
        # Create 12 periods
        for period_num in range(1, 13):
            # Calculate period dates
            month = (fiscal_start_month + period_num - 2) % 12 + 1
            year = year_number if month >= fiscal_start_month else year_number + 1
            
            start_date = date(year, month, 1)
            
            # Last day of month
            if month == 12:
                end_date = date(year, 12, 31)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            period = CompanyPeriod(
                period_number=period_num,
                year_number=year_number,
                start_date=start_date,
                end_date=end_date,
                is_open=True if period_num == 1 else False,
                is_current=True if period_num == 1 else False,
                created_by=str(user_id)
            )
            self.db.add(period)