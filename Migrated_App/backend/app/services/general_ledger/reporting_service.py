"""
Financial Reporting Service
Migrated from COBOL gl300.cbl, gl310.cbl, gl320.cbl
Generates financial statements and reports
"""
from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from app.models.general_ledger import (
    ChartOfAccounts, AccountType, AccountBalance
)
from app.models.system import CompanyPeriod
from app.services.base import BaseService


class ReportingService(BaseService):
    """Financial reporting service"""
    
    def generate_balance_sheet(
        self,
        period_id: int,
        comparative_period_id: Optional[int] = None,
        show_details: bool = True
    ) -> Dict:
        """
        Generate balance sheet
        Migrated from gl300.cbl BALANCE-SHEET
        """
        try:
            # Get periods
            period = self.db.query(CompanyPeriod).filter(
                CompanyPeriod.id == period_id
            ).first()
            if not period:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Period not found"
                )
            
            comparative = None
            if comparative_period_id:
                comparative = self.db.query(CompanyPeriod).filter(
                    CompanyPeriod.id == comparative_period_id
                ).first()
            
            # Get asset accounts
            assets = self._get_account_section(
                period_id, AccountType.ASSET, show_details
            )
            
            # Get liability accounts
            liabilities = self._get_account_section(
                period_id, AccountType.LIABILITY, show_details
            )
            
            # Get capital/equity accounts
            equity = self._get_account_section(
                period_id, AccountType.CAPITAL, show_details
            )
            
            # Calculate retained earnings
            retained_earnings = self._calculate_current_retained_earnings(period_id)
            
            # Add retained earnings to equity
            equity["lines"].append({
                "account_code": "3999.9999",
                "account_name": "Current Year Earnings",
                "level": 1,
                "is_header": False,
                "current_balance": retained_earnings,
                "comparative_balance": (
                    self._calculate_current_retained_earnings(comparative_period_id)
                    if comparative_period_id else None
                )
            })
            equity["total"] += retained_earnings
            
            # Calculate totals
            total_assets = assets["total"]
            total_liabilities = liabilities["total"]
            total_equity = equity["total"]
            
            # Comparative totals
            if comparative_period_id:
                comp_assets = self._get_account_section(
                    comparative_period_id, AccountType.ASSET, show_details
                )
                comp_liabilities = self._get_account_section(
                    comparative_period_id, AccountType.LIABILITY, show_details
                )
                comp_equity = self._get_account_section(
                    comparative_period_id, AccountType.CAPITAL, show_details
                )
                comp_equity["total"] += self._calculate_current_retained_earnings(
                    comparative_period_id
                )
            
            return {
                "report_date": period.end_date,
                "period": f"{period.period_number}/{period.year_number}",
                "comparative_period": (
                    f"{comparative.period_number}/{comparative.year_number}"
                    if comparative else None
                ),
                "assets": {
                    "lines": assets["lines"],
                    "total": total_assets,
                    "comparative_total": (
                        comp_assets["total"] if comparative_period_id else None
                    )
                },
                "liabilities": {
                    "lines": liabilities["lines"],
                    "total": total_liabilities,
                    "comparative_total": (
                        comp_liabilities["total"] if comparative_period_id else None
                    )
                },
                "equity": {
                    "lines": equity["lines"],
                    "total": total_equity,
                    "comparative_total": (
                        comp_equity["total"] if comparative_period_id else None
                    )
                },
                "totals": {
                    "liabilities_and_equity": total_liabilities + total_equity,
                    "is_balanced": total_assets == (total_liabilities + total_equity)
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating balance sheet: {str(e)}"
            )
    
    def generate_income_statement(
        self,
        period_id: int,
        comparative_period_id: Optional[int] = None,
        show_details: bool = True,
        ytd: bool = True
    ) -> Dict:
        """
        Generate income statement
        Migrated from gl310.cbl INCOME-STATEMENT
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
            
            # Get revenue accounts
            if ytd:
                revenue = self._get_ytd_account_section(
                    period, AccountType.INCOME, show_details
                )
            else:
                revenue = self._get_account_section(
                    period_id, AccountType.INCOME, show_details
                )
            
            # Get expense accounts
            if ytd:
                expenses = self._get_ytd_account_section(
                    period, AccountType.EXPENSE, show_details
                )
            else:
                expenses = self._get_account_section(
                    period_id, AccountType.EXPENSE, show_details
                )
            
            # Calculate gross profit (simplified - would need COGS)
            gross_profit = revenue["total"]
            
            # Calculate net income
            net_income = revenue["total"] - expenses["total"]
            
            # Comparative data
            if comparative_period_id:
                comp_period = self.db.query(CompanyPeriod).filter(
                    CompanyPeriod.id == comparative_period_id
                ).first()
                
                if ytd:
                    comp_revenue = self._get_ytd_account_section(
                        comp_period, AccountType.INCOME, show_details
                    )
                    comp_expenses = self._get_ytd_account_section(
                        comp_period, AccountType.EXPENSE, show_details
                    )
                else:
                    comp_revenue = self._get_account_section(
                        comparative_period_id, AccountType.INCOME, show_details
                    )
                    comp_expenses = self._get_account_section(
                        comparative_period_id, AccountType.EXPENSE, show_details
                    )
                
                comp_net_income = comp_revenue["total"] - comp_expenses["total"]
            
            return {
                "report_date": period.end_date,
                "period": f"{period.period_number}/{period.year_number}",
                "is_ytd": ytd,
                "comparative_period": (
                    f"{comp_period.period_number}/{comp_period.year_number}"
                    if comparative_period_id else None
                ),
                "revenue": {
                    "lines": revenue["lines"],
                    "total": revenue["total"],
                    "comparative_total": (
                        comp_revenue["total"] if comparative_period_id else None
                    )
                },
                "gross_profit": {
                    "amount": gross_profit,
                    "margin_pct": (
                        (gross_profit / revenue["total"] * 100)
                        if revenue["total"] != 0 else 0
                    )
                },
                "expenses": {
                    "lines": expenses["lines"],
                    "total": expenses["total"],
                    "comparative_total": (
                        comp_expenses["total"] if comparative_period_id else None
                    )
                },
                "net_income": {
                    "amount": net_income,
                    "margin_pct": (
                        (net_income / revenue["total"] * 100)
                        if revenue["total"] != 0 else 0
                    ),
                    "comparative_amount": (
                        comp_net_income if comparative_period_id else None
                    )
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating income statement: {str(e)}"
            )
    
    def generate_cash_flow_statement(
        self,
        period_id: int,
        ytd: bool = True
    ) -> Dict:
        """
        Generate cash flow statement
        Migrated from gl320.cbl CASH-FLOW
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
            
            # In a full implementation, would calculate:
            # - Operating activities (net income + adjustments)
            # - Investing activities (capital expenditures, asset sales)
            # - Financing activities (debt, equity changes)
            
            # Simplified version
            net_income = self._calculate_current_retained_earnings(period_id)
            
            # Get cash accounts
            cash_accounts = self.db.query(
                ChartOfAccounts,
                AccountBalance
            ).join(
                AccountBalance,
                and_(
                    AccountBalance.account_id == ChartOfAccounts.id,
                    AccountBalance.period_id == period_id
                )
            ).filter(
                and_(
                    ChartOfAccounts.account_type == AccountType.ASSET,
                    ChartOfAccounts.account_code.like("1000.%")  # Cash accounts
                )
            ).all()
            
            ending_cash = sum(
                balance.closing_balance 
                for account, balance in cash_accounts
            )
            
            # Get beginning cash (would need prior period)
            beginning_cash = sum(
                balance.opening_balance 
                for account, balance in cash_accounts
            )
            
            net_cash_flow = ending_cash - beginning_cash
            
            return {
                "report_date": period.end_date,
                "period": f"{period.period_number}/{period.year_number}",
                "is_ytd": ytd,
                "operating_activities": {
                    "net_income": net_income,
                    "adjustments": [],
                    "net_cash_from_operating": net_income  # Simplified
                },
                "investing_activities": {
                    "capital_expenditures": Decimal("0"),
                    "asset_sales": Decimal("0"),
                    "net_cash_from_investing": Decimal("0")
                },
                "financing_activities": {
                    "debt_proceeds": Decimal("0"),
                    "debt_repayments": Decimal("0"),
                    "dividends": Decimal("0"),
                    "net_cash_from_financing": Decimal("0")
                },
                "summary": {
                    "beginning_cash": beginning_cash,
                    "net_increase": net_cash_flow,
                    "ending_cash": ending_cash
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating cash flow statement: {str(e)}"
            )
    
    def generate_account_detail_report(
        self,
        account_code: str,
        from_period_id: int,
        to_period_id: int,
        include_journal_detail: bool = True
    ) -> Dict:
        """
        Generate detailed account activity report
        Migrated from gl320.cbl ACCOUNT-DETAIL
        """
        try:
            # Get account
            account = self.db.query(ChartOfAccounts).filter(
                ChartOfAccounts.account_code == account_code
            ).first()
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Account {account_code} not found"
                )
            
            # Get periods
            from_period = self.db.query(CompanyPeriod).filter(
                CompanyPeriod.id == from_period_id
            ).first()
            to_period = self.db.query(CompanyPeriod).filter(
                CompanyPeriod.id == to_period_id
            ).first()
            
            if not from_period or not to_period:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Period not found"
                )
            
            # Get opening balance
            opening_balance_record = self.db.query(AccountBalance).filter(
                and_(
                    AccountBalance.account_id == account.id,
                    AccountBalance.period_id == from_period_id
                )
            ).first()
            
            opening_balance = (
                opening_balance_record.opening_balance 
                if opening_balance_record else Decimal("0")
            )
            
            # Get period balances
            period_balances = self.db.query(AccountBalance).filter(
                and_(
                    AccountBalance.account_id == account.id,
                    AccountBalance.period_id >= from_period_id,
                    AccountBalance.period_id <= to_period_id
                )
            ).order_by(AccountBalance.period_id).all()
            
            # Get journal details if requested
            journal_details = []
            if include_journal_detail:
                from app.models.general_ledger import JournalLine, JournalHeader
                
                journal_entries = self.db.query(
                    JournalHeader,
                    JournalLine
                ).join(
                    JournalLine,
                    JournalLine.journal_id == JournalHeader.id
                ).filter(
                    and_(
                        JournalLine.account_id == account.id,
                        JournalHeader.period_id >= from_period_id,
                        JournalHeader.period_id <= to_period_id,
                        JournalHeader.posting_status == "POSTED"
                    )
                ).order_by(
                    JournalHeader.journal_date,
                    JournalHeader.journal_number
                ).all()
                
                running_balance = opening_balance
                for header, line in journal_entries:
                    if account.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                        # Normal debit balance
                        running_balance += line.debit_amount - line.credit_amount
                    else:
                        # Normal credit balance
                        running_balance += line.credit_amount - line.debit_amount
                    
                    journal_details.append({
                        "journal_date": header.journal_date,
                        "journal_number": header.journal_number,
                        "description": line.description or header.description,
                        "reference": line.reference or header.reference,
                        "debit": line.debit_amount,
                        "credit": line.credit_amount,
                        "balance": running_balance
                    })
            
            # Calculate totals
            total_debits = sum(b.period_debits for b in period_balances)
            total_credits = sum(b.period_credits for b in period_balances)
            net_movement = total_debits - total_credits
            
            closing_balance = (
                period_balances[-1].closing_balance 
                if period_balances else opening_balance
            )
            
            return {
                "account": {
                    "account_code": account.account_code,
                    "account_name": account.account_name,
                    "account_type": account.account_type.value
                },
                "period_range": {
                    "from": f"{from_period.period_number}/{from_period.year_number}",
                    "to": f"{to_period.period_number}/{to_period.year_number}"
                },
                "opening_balance": opening_balance,
                "movements": {
                    "total_debits": total_debits,
                    "total_credits": total_credits,
                    "net_movement": net_movement
                },
                "closing_balance": closing_balance,
                "period_balances": [
                    {
                        "period_id": b.period_id,
                        "opening": b.opening_balance,
                        "debits": b.period_debits,
                        "credits": b.period_credits,
                        "closing": b.closing_balance
                    }
                    for b in period_balances
                ],
                "journal_details": journal_details
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating account detail report: {str(e)}"
            )
    
    def _get_account_section(
        self,
        period_id: int,
        account_type: AccountType,
        show_details: bool
    ) -> Dict:
        """Get accounts of specific type with balances"""
        # Query accounts with balances
        query = self.db.query(
            ChartOfAccounts,
            AccountBalance
        ).outerjoin(
            AccountBalance,
            and_(
                AccountBalance.account_id == ChartOfAccounts.id,
                AccountBalance.period_id == period_id
            )
        ).filter(
            and_(
                ChartOfAccounts.account_type == account_type,
                ChartOfAccounts.is_active == True
            )
        )
        
        if not show_details:
            query = query.filter(ChartOfAccounts.is_header == True)
        
        results = query.order_by(ChartOfAccounts.account_code).all()
        
        # Build hierarchical structure
        lines = []
        total = Decimal("0")
        
        for account, balance in results:
            account_balance = balance.closing_balance if balance else Decimal("0")
            
            # For headers, calculate total of children
            if account.is_header:
                child_total = self._calculate_header_total(account.account_code, period_id)
                account_balance = child_total
            
            lines.append({
                "account_code": account.account_code,
                "account_name": account.account_name,
                "level": account.level,
                "is_header": account.is_header,
                "current_balance": account_balance
            })
            
            if not account.is_header:
                total += account_balance
        
        return {
            "lines": lines,
            "total": total
        }
    
    def _get_ytd_account_section(
        self,
        period: CompanyPeriod,
        account_type: AccountType,
        show_details: bool
    ) -> Dict:
        """Get YTD totals for accounts of specific type"""
        # Get all periods up to current
        periods = self.db.query(CompanyPeriod.id).filter(
            and_(
                CompanyPeriod.year_number == period.year_number,
                CompanyPeriod.period_number <= period.period_number
            )
        ).all()
        period_ids = [p[0] for p in periods]
        
        # Query YTD totals
        query = self.db.query(
            ChartOfAccounts,
            func.sum(AccountBalance.period_debits).label("ytd_debits"),
            func.sum(AccountBalance.period_credits).label("ytd_credits")
        ).outerjoin(
            AccountBalance,
            and_(
                AccountBalance.account_id == ChartOfAccounts.id,
                AccountBalance.period_id.in_(period_ids)
            )
        ).filter(
            and_(
                ChartOfAccounts.account_type == account_type,
                ChartOfAccounts.is_active == True
            )
        ).group_by(ChartOfAccounts.id)
        
        if not show_details:
            query = query.filter(ChartOfAccounts.is_header == True)
        
        results = query.order_by(ChartOfAccounts.account_code).all()
        
        # Build structure
        lines = []
        total = Decimal("0")
        
        for account, ytd_debits, ytd_credits in results:
            ytd_debits = ytd_debits or Decimal("0")
            ytd_credits = ytd_credits or Decimal("0")
            
            if account.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                balance = ytd_debits - ytd_credits
            else:
                balance = ytd_credits - ytd_debits
            
            lines.append({
                "account_code": account.account_code,
                "account_name": account.account_name,
                "level": account.level,
                "is_header": account.is_header,
                "current_balance": balance
            })
            
            if not account.is_header:
                total += balance
        
        return {
            "lines": lines,
            "total": abs(total)  # Revenue/Income shown as positive
        }
    
    def _calculate_header_total(self, header_code: str, period_id: int) -> Decimal:
        """Calculate total for header account including all children"""
        # Get all child accounts
        children = self.db.query(
            ChartOfAccounts,
            AccountBalance
        ).outerjoin(
            AccountBalance,
            and_(
                AccountBalance.account_id == ChartOfAccounts.id,
                AccountBalance.period_id == period_id
            )
        ).filter(
            and_(
                ChartOfAccounts.parent_account == header_code,
                ChartOfAccounts.is_active == True,
                ChartOfAccounts.allow_posting == True
            )
        ).all()
        
        total = Decimal("0")
        for account, balance in children:
            if balance:
                total += balance.closing_balance
        
        return total
    
    def _calculate_current_retained_earnings(self, period_id: int) -> Decimal:
        """Calculate current year retained earnings (P&L)"""
        if not period_id:
            return Decimal("0")
            
        period = self.db.query(CompanyPeriod).filter(
            CompanyPeriod.id == period_id
        ).first()
        
        if not period:
            return Decimal("0")
        
        # Get YTD revenue
        revenue_result = self.db.query(
            func.sum(AccountBalance.closing_balance)
        ).join(ChartOfAccounts).join(CompanyPeriod).filter(
            and_(
                ChartOfAccounts.account_type == AccountType.INCOME,
                CompanyPeriod.year_number == period.year_number,
                CompanyPeriod.period_number <= period.period_number
            )
        ).scalar()
        
        revenue = revenue_result or Decimal("0")
        
        # Get YTD expenses
        expense_result = self.db.query(
            func.sum(AccountBalance.closing_balance)
        ).join(ChartOfAccounts).join(CompanyPeriod).filter(
            and_(
                ChartOfAccounts.account_type == AccountType.EXPENSE,
                CompanyPeriod.year_number == period.year_number,
                CompanyPeriod.period_number <= period.period_number
            )
        ).scalar()
        
        expenses = expense_result or Decimal("0")
        
        # Revenue is typically negative (credit), expenses positive (debit)
        # So retained earnings = -revenue - expenses
        return -(revenue + expenses)