"""
GL Inquiry Service
Migrated from COBOL gl400.cbl, gl410.cbl, gl420.cbl
Handles general ledger inquiries and lookups
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from fastapi import HTTPException, status

from app.models.general_ledger import (
    ChartOfAccounts, AccountBalance, JournalHeader, JournalLine,
    AccountType, PostingStatus
)
from app.models.system import CompanyPeriod
from app.services.base import BaseService


class GLInquiryService(BaseService):
    """GL inquiry and lookup service"""
    
    def get_account_inquiry(
        self,
        account_code: str,
        period_id: Optional[int] = None,
        include_journal_lines: bool = True,
        limit: int = 100
    ) -> Dict:
        """
        Get account inquiry with balances and movements
        Migrated from gl400.cbl ACCOUNT-INQUIRY
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
            
            # Get account balance
            balance = self.db.query(AccountBalance).filter(
                and_(
                    AccountBalance.account_id == account.id,
                    AccountBalance.period_id == period.id
                )
            ).first()
            
            balance_info = {
                "opening_balance": balance.opening_balance if balance else Decimal("0"),
                "period_debits": balance.period_debits if balance else Decimal("0"),
                "period_credits": balance.period_credits if balance else Decimal("0"),
                "closing_balance": balance.closing_balance if balance else Decimal("0")
            }
            
            # Get YTD totals
            ytd_totals = self._get_ytd_totals(account.id, period.year_number)
            
            # Get recent journal lines
            journal_lines = []
            if include_journal_lines:
                lines_query = self.db.query(
                    JournalHeader,
                    JournalLine
                ).join(
                    JournalLine,
                    JournalLine.journal_id == JournalHeader.id
                ).filter(
                    and_(
                        JournalLine.account_id == account.id,
                        JournalHeader.posting_status == PostingStatus.POSTED
                    )
                ).order_by(
                    JournalHeader.journal_date.desc(),
                    JournalHeader.journal_number.desc()
                ).limit(limit)
                
                for header, line in lines_query:
                    journal_lines.append({
                        "journal_date": header.journal_date,
                        "journal_number": header.journal_number,
                        "period": f"{header.period_number}/{header.year_number}",
                        "description": line.description or header.description,
                        "reference": line.reference or header.reference,
                        "debit_amount": line.debit_amount,
                        "credit_amount": line.credit_amount,
                        "source_module": header.source_module
                    })
            
            return {
                "account": {
                    "account_code": account.account_code,
                    "account_name": account.account_name,
                    "account_type": account.account_type.value,
                    "is_header": account.is_header,
                    "allow_posting": account.allow_posting,
                    "is_active": account.is_active,
                    "currency_code": account.currency_code
                },
                "period": {
                    "period_id": period.id,
                    "period_number": period.period_number,
                    "year_number": period.year_number,
                    "period_name": f"{period.period_number}/{period.year_number}",
                    "start_date": period.start_date,
                    "end_date": period.end_date
                },
                "balances": balance_info,
                "ytd_totals": ytd_totals,
                "recent_activity": journal_lines
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in account inquiry: {str(e)}"
            )
    
    def search_accounts(
        self,
        search_term: Optional[str] = None,
        account_type: Optional[AccountType] = None,
        is_header: Optional[bool] = None,
        allow_posting: Optional[bool] = None,
        active_only: bool = True,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """
        Search chart of accounts
        Migrated from gl410.cbl ACCOUNT-SEARCH
        """
        try:
            query = self.db.query(ChartOfAccounts)
            
            # Apply filters
            if active_only:
                query = query.filter(ChartOfAccounts.is_active == True)
            
            if search_term:
                query = query.filter(
                    or_(
                        ChartOfAccounts.account_code.ilike(f"%{search_term}%"),
                        ChartOfAccounts.account_name.ilike(f"%{search_term}%")
                    )
                )
            
            if account_type:
                query = query.filter(ChartOfAccounts.account_type == account_type)
            
            if is_header is not None:
                query = query.filter(ChartOfAccounts.is_header == is_header)
            
            if allow_posting is not None:
                query = query.filter(ChartOfAccounts.allow_posting == allow_posting)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            accounts = query.order_by(ChartOfAccounts.account_code)\\\n                         .offset((page - 1) * page_size)\\\n                         .limit(page_size)\\\n                         .all()
            
            return {
                "accounts": [
                    {
                        "id": acc.id,
                        "account_code": acc.account_code,
                        "account_name": acc.account_name,
                        "account_type": acc.account_type.value,
                        "is_header": acc.is_header,
                        "allow_posting": acc.allow_posting,
                        "current_balance": acc.current_balance,
                        "is_active": acc.is_active
                    }
                    for acc in accounts
                ],
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error searching accounts: {str(e)}"
            )
    
    def get_journal_inquiry(
        self,
        journal_number: Optional[str] = None,
        journal_id: Optional[int] = None,
        include_lines: bool = True
    ) -> Dict:
        """
        Get journal inquiry
        Migrated from gl410.cbl JOURNAL-INQUIRY
        """
        try:
            query = self.db.query(JournalHeader)
            
            if journal_id:
                query = query.filter(JournalHeader.id == journal_id)
            elif journal_number:
                query = query.filter(JournalHeader.journal_number == journal_number)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Must provide either journal_id or journal_number"
                )
            
            journal = query.first()
            if not journal:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Journal not found"
                )
            
            # Get journal lines
            lines = []
            if include_lines:
                journal_lines = self.db.query(
                    JournalLine,
                    ChartOfAccounts
                ).join(
                    ChartOfAccounts,
                    ChartOfAccounts.id == JournalLine.account_id
                ).filter(
                    JournalLine.journal_id == journal.id
                ).order_by(JournalLine.line_number).all()
                
                for line, account in journal_lines:
                    lines.append({
                        "line_number": line.line_number,
                        "account_code": account.account_code,
                        "account_name": account.account_name,
                        "debit_amount": line.debit_amount,
                        "credit_amount": line.credit_amount,
                        "description": line.description,
                        "reference": line.reference,
                        "analysis_code1": line.analysis_code1,
                        "analysis_code2": line.analysis_code2,
                        "analysis_code3": line.analysis_code3
                    })
            
            return {
                "journal": {
                    "id": journal.id,
                    "journal_number": journal.journal_number,
                    "journal_date": journal.journal_date,
                    "journal_type": journal.journal_type.value,
                    "description": journal.description,
                    "reference": journal.reference,
                    "source_module": journal.source_module,
                    "source_reference": journal.source_reference,
                    "posting_status": journal.posting_status.value,
                    "total_debits": journal.total_debits,
                    "total_credits": journal.total_credits,
                    "line_count": journal.line_count,
                    "period": f"{journal.period_number}/{journal.year_number}",
                    "posted_date": journal.posted_date,
                    "posted_by": journal.posted_by,
                    "created_date": journal.created_at,
                    "created_by": journal.created_by
                },
                "lines": lines
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in journal inquiry: {str(e)}"
            )
    
    def search_journals(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        journal_type: Optional[str] = None,
        source_module: Optional[str] = None,
        posting_status: Optional[PostingStatus] = None,
        reference: Optional[str] = None,
        description: Optional[str] = None,
        amount_from: Optional[Decimal] = None,
        amount_to: Optional[Decimal] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """
        Search journals with filters
        Migrated from gl420.cbl JOURNAL-SEARCH
        """
        try:
            query = self.db.query(JournalHeader)
            
            # Apply filters
            if from_date:
                query = query.filter(JournalHeader.journal_date >= from_date)
            
            if to_date:
                query = query.filter(JournalHeader.journal_date <= to_date)
            
            if journal_type:
                query = query.filter(JournalHeader.journal_type == journal_type)
            
            if source_module:
                query = query.filter(JournalHeader.source_module == source_module)
            
            if posting_status:
                query = query.filter(JournalHeader.posting_status == posting_status)
            
            if reference:
                query = query.filter(JournalHeader.reference.ilike(f"%{reference}%"))
            
            if description:
                query = query.filter(JournalHeader.description.ilike(f"%{description}%"))
            
            if amount_from:
                query = query.filter(JournalHeader.total_debits >= amount_from)
            
            if amount_to:
                query = query.filter(JournalHeader.total_debits <= amount_to)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            journals = query.order_by(
                JournalHeader.journal_date.desc(),
                JournalHeader.journal_number.desc()
            ).offset((page - 1) * page_size).limit(page_size).all()
            
            return {
                "journals": [
                    {
                        "id": j.id,
                        "journal_number": j.journal_number,
                        "journal_date": j.journal_date,
                        "journal_type": j.journal_type.value,
                        "description": j.description,
                        "reference": j.reference,
                        "source_module": j.source_module,
                        "posting_status": j.posting_status.value,
                        "total_debits": j.total_debits,
                        "total_credits": j.total_credits,
                        "period": f"{j.period_number}/{j.year_number}"
                    }
                    for j in journals
                ],
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error searching journals: {str(e)}"
            )
    
    def get_period_summary(
        self,
        period_id: int,
        account_type: Optional[AccountType] = None
    ) -> Dict:
        """
        Get period summary with totals
        Migrated from gl420.cbl PERIOD-SUMMARY
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
            
            # Base query for account balances
            query = self.db.query(
                AccountBalance.account_id,
                ChartOfAccounts.account_code,
                ChartOfAccounts.account_name,
                ChartOfAccounts.account_type,
                func.sum(AccountBalance.opening_balance).label("total_opening"),
                func.sum(AccountBalance.period_debits).label("total_debits"),
                func.sum(AccountBalance.period_credits).label("total_credits"),
                func.sum(AccountBalance.closing_balance).label("total_closing")
            ).join(
                ChartOfAccounts,
                ChartOfAccounts.id == AccountBalance.account_id
            ).filter(
                AccountBalance.period_id == period_id
            )
            
            if account_type:
                query = query.filter(ChartOfAccounts.account_type == account_type)
            
            query = query.group_by(
                AccountBalance.account_id,
                ChartOfAccounts.account_code,
                ChartOfAccounts.account_name,
                ChartOfAccounts.account_type
            ).order_by(ChartOfAccounts.account_code)
            
            results = query.all()
            
            # Calculate totals by account type
            type_totals = {}
            for result in results:
                acc_type = result.account_type.value
                if acc_type not in type_totals:
                    type_totals[acc_type] = {
                        "opening_balance": Decimal("0"),
                        "period_debits": Decimal("0"),
                        "period_credits": Decimal("0"),
                        "closing_balance": Decimal("0"),
                        "net_movement": Decimal("0"),
                        "account_count": 0
                    }
                
                type_totals[acc_type]["opening_balance"] += result.total_opening or Decimal("0")
                type_totals[acc_type]["period_debits"] += result.total_debits or Decimal("0")
                type_totals[acc_type]["period_credits"] += result.total_credits or Decimal("0")
                type_totals[acc_type]["closing_balance"] += result.total_closing or Decimal("0")
                type_totals[acc_type]["net_movement"] += (
                    (result.total_debits or Decimal("0")) - 
                    (result.total_credits or Decimal("0"))
                )
                type_totals[acc_type]["account_count"] += 1
            
            # Get journal statistics
            journal_stats = self.db.query(
                func.count(JournalHeader.id).label("journal_count"),
                func.sum(JournalHeader.total_debits).label("total_debits"),
                func.sum(JournalHeader.line_count).label("total_lines")
            ).filter(
                and_(
                    JournalHeader.period_id == period_id,
                    JournalHeader.posting_status == PostingStatus.POSTED
                )
            ).first()
            
            return {
                "period": {
                    "period_id": period.id,
                    "period_number": period.period_number,
                    "year_number": period.year_number,
                    "start_date": period.start_date,
                    "end_date": period.end_date,
                    "is_open": period.is_open,
                    "is_current": period.is_current
                },
                "account_type_totals": type_totals,
                "journal_statistics": {
                    "journal_count": journal_stats.journal_count or 0,
                    "total_amount": journal_stats.total_debits or Decimal("0"),
                    "total_lines": journal_stats.total_lines or 0
                },
                "account_details": [
                    {
                        "account_code": r.account_code,
                        "account_name": r.account_name,
                        "account_type": r.account_type.value,
                        "opening_balance": r.total_opening or Decimal("0"),
                        "period_debits": r.total_debits or Decimal("0"),
                        "period_credits": r.total_credits or Decimal("0"),
                        "closing_balance": r.total_closing or Decimal("0"),
                        "net_movement": (
                            (r.total_debits or Decimal("0")) - 
                            (r.total_credits or Decimal("0"))
                        )
                    }
                    for r in results
                ]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating period summary: {str(e)}"
            )
    
    def get_account_history(
        self,
        account_code: str,
        year_number: int,
        include_balances: bool = True
    ) -> Dict:
        """
        Get account history for entire year
        Migrated from gl420.cbl ACCOUNT-HISTORY
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
            
            # Get all periods for year
            periods = self.db.query(CompanyPeriod).filter(
                CompanyPeriod.year_number == year_number
            ).order_by(CompanyPeriod.period_number).all()
            
            # Get balances for all periods
            balances = []
            if include_balances:
                period_ids = [p.id for p in periods]
                balance_records = self.db.query(AccountBalance).filter(
                    and_(
                        AccountBalance.account_id == account.id,
                        AccountBalance.period_id.in_(period_ids)
                    )
                ).order_by(AccountBalance.period_id).all()
                
                balance_map = {b.period_id: b for b in balance_records}
                
                running_balance = Decimal("0")
                for period in periods:
                    balance = balance_map.get(period.id)
                    if balance:
                        balances.append({
                            "period_number": period.period_number,
                            "period_name": f"{period.period_number}/{period.year_number}",
                            "opening_balance": balance.opening_balance,
                            "period_debits": balance.period_debits,
                            "period_credits": balance.period_credits,
                            "closing_balance": balance.closing_balance,
                            "net_movement": balance.period_debits - balance.period_credits
                        })
                        running_balance = balance.closing_balance
                    else:
                        balances.append({
                            "period_number": period.period_number,
                            "period_name": f"{period.period_number}/{period.year_number}",
                            "opening_balance": running_balance,
                            "period_debits": Decimal("0"),
                            "period_credits": Decimal("0"),
                            "closing_balance": running_balance,
                            "net_movement": Decimal("0")
                        })
            
            # Calculate year totals
            year_debits = sum(b["period_debits"] for b in balances)
            year_credits = sum(b["period_credits"] for b in balances)
            net_movement = year_debits - year_credits
            
            return {
                "account": {
                    "account_code": account.account_code,
                    "account_name": account.account_name,
                    "account_type": account.account_type.value
                },
                "year_number": year_number,
                "year_totals": {
                    "total_debits": year_debits,
                    "total_credits": year_credits,
                    "net_movement": net_movement,
                    "opening_balance": balances[0]["opening_balance"] if balances else Decimal("0"),
                    "closing_balance": balances[-1]["closing_balance"] if balances else Decimal("0")
                },
                "period_balances": balances
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving account history: {str(e)}"
            )
    
    def _get_ytd_totals(self, account_id: int, year_number: int) -> Dict:
        """Get YTD totals for account"""
        try:
            result = self.db.query(
                func.sum(AccountBalance.period_debits).label("ytd_debits"),
                func.sum(AccountBalance.period_credits).label("ytd_credits")
            ).join(CompanyPeriod).filter(
                and_(
                    AccountBalance.account_id == account_id,
                    CompanyPeriod.year_number == year_number
                )
            ).first()
            
            ytd_debits = result.ytd_debits or Decimal("0")
            ytd_credits = result.ytd_credits or Decimal("0")
            
            return {
                "ytd_debits": ytd_debits,
                "ytd_credits": ytd_credits,
                "ytd_net_movement": ytd_debits - ytd_credits
            }
            
        except Exception:
            return {
                "ytd_debits": Decimal("0"),
                "ytd_credits": Decimal("0"),
                "ytd_net_movement": Decimal("0")
            }