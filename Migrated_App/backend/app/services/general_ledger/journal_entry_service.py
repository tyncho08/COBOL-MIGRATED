"""
Journal Entry Service
Migrated from COBOL gl050.cbl, gl060.cbl, gl070.cbl
Handles journal entry creation, posting, and reversal
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from app.models.general_ledger import (
    JournalHeader, JournalLine, JournalType, PostingStatus,
    ChartOfAccounts, AccountBalance, GLBatch
)
from app.models.system import CompanyPeriod
from app.models.control_tables import NumberSequence
from app.services.base import BaseService


class JournalEntryService(BaseService):
    """Journal entry processing service"""
    
    def create_journal_entry(
        self,
        journal_date: date,
        journal_type: JournalType,
        description: str,
        reference: Optional[str] = None,
        journal_lines: List[Dict] = None,
        source_module: Optional[str] = None,
        source_reference: Optional[str] = None,
        auto_post: bool = False,
        user_id: int = None
    ) -> JournalHeader:
        """
        Create journal entry
        Migrated from gl050.cbl CREATE-JOURNAL
        """
        try:
            # Get period for journal date
            period = self._get_period_for_date(journal_date)
            if not period:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No open period found for journal date"
                )
            
            if not period.is_open:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Period is closed for posting"
                )
            
            # Generate journal number
            journal_number = self._get_next_journal_number()
            
            # Create journal header
            journal = JournalHeader(
                journal_number=journal_number,
                journal_date=journal_date,
                journal_type=journal_type,
                period_id=period.id,
                period_number=period.period_number,
                year_number=period.year_number,
                description=description,
                reference=reference,
                source_module=source_module,
                source_reference=source_reference,
                posting_status=PostingStatus.DRAFT,
                created_by=str(user_id) if user_id else None
            )
            
            self.db.add(journal)
            self.db.flush()
            
            # Process journal lines
            if not journal_lines:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Journal must have at least two lines"
                )
            
            line_number = 0
            total_debits = Decimal("0")
            total_credits = Decimal("0")
            
            for line_data in journal_lines:
                line_number += 10
                
                # Validate account
                account_code = line_data["account_code"]
                account = self.db.query(ChartOfAccounts).filter(
                    ChartOfAccounts.account_code == account_code
                ).first()
                
                if not account:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Account {account_code} not found"
                    )
                
                if not account.allow_posting:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Account {account_code} does not allow posting"
                    )
                
                # Get amounts
                debit_amount = Decimal(str(line_data.get("debit_amount", "0")))
                credit_amount = Decimal(str(line_data.get("credit_amount", "0")))
                
                # Validate amounts
                if debit_amount < 0 or credit_amount < 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Amounts must be positive"
                    )
                
                if debit_amount == 0 and credit_amount == 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Line must have either debit or credit amount"
                    )
                
                if debit_amount > 0 and credit_amount > 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Line cannot have both debit and credit"
                    )
                
                # Create journal line
                line = JournalLine(
                    journal_id=journal.id,
                    line_number=line_number,
                    account_id=account.id,
                    account_code=account_code,
                    debit_amount=debit_amount,
                    credit_amount=credit_amount,
                    description=line_data.get("description", ""),
                    reference=line_data.get("reference", ""),
                    analysis_code1=line_data.get("analysis_code1"),
                    analysis_code2=line_data.get("analysis_code2"),
                    analysis_code3=line_data.get("analysis_code3"),
                    currency_code=line_data.get("currency_code", "USD"),
                    exchange_rate=Decimal(str(line_data.get("exchange_rate", "1")))
                )
                
                journal.journal_lines.append(line)
                
                total_debits += debit_amount
                total_credits += credit_amount
            
            # Validate journal balance
            if total_debits != total_credits:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Journal not balanced. Debits: {total_debits}, Credits: {total_credits}"
                )
            
            # Update journal totals
            journal.total_debits = total_debits
            journal.total_credits = total_credits
            journal.line_count = len(journal.journal_lines)
            
            # Auto-post if requested
            if auto_post:
                self._post_journal(journal, user_id)
            
            self.db.commit()
            self.db.refresh(journal)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="journal_headers",
                record_id=str(journal.id),
                operation="CREATE",
                user_id=user_id,
                details=f"Created journal {journal_number}"
            )
            
            return journal
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating journal: {str(e)}"
            )
    
    def post_journal(
        self,
        journal_id: int,
        user_id: int
    ) -> JournalHeader:
        """
        Post journal entry to ledger
        Migrated from gl060.cbl POST-JOURNAL
        """
        try:
            # Get journal
            journal = self.db.query(JournalHeader).filter(
                JournalHeader.id == journal_id
            ).first()
            if not journal:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Journal not found"
                )
            
            if journal.posting_status == PostingStatus.POSTED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Journal already posted"
                )
            
            if journal.posting_status == PostingStatus.REVERSED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot post reversed journal"
                )
            
            # Check if period is open
            period = journal.period
            if not period.is_open:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Period is closed for posting"
                )
            
            # Post the journal
            self._post_journal(journal, user_id)
            
            self.db.commit()
            self.db.refresh(journal)
            
            return journal
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error posting journal: {str(e)}"
            )
    
    def reverse_journal(
        self,
        journal_id: int,
        reversal_date: date,
        reversal_reason: str,
        user_id: int
    ) -> JournalHeader:
        """
        Reverse posted journal
        Migrated from gl070.cbl REVERSE-JOURNAL
        """
        try:
            # Get original journal
            original = self.db.query(JournalHeader).filter(
                JournalHeader.id == journal_id
            ).first()
            if not original:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Journal not found"
                )
            
            if original.posting_status != PostingStatus.POSTED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only posted journals can be reversed"
                )
            
            if original.is_reversal:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot reverse a reversal journal"
                )
            
            # Check if already reversed
            existing_reversal = self.db.query(JournalHeader).filter(
                JournalHeader.reversal_of_id == journal_id
            ).first()
            if existing_reversal:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Journal already reversed"
                )
            
            # Create reversal journal
            reversal_lines = []
            for line in original.journal_lines:
                reversal_lines.append({
                    "account_code": line.account_code,
                    "debit_amount": line.credit_amount,  # Swap debit/credit
                    "credit_amount": line.debit_amount,
                    "description": f"Reversal: {line.description}",
                    "reference": line.reference,
                    "analysis_code1": line.analysis_code1,
                    "analysis_code2": line.analysis_code2,
                    "analysis_code3": line.analysis_code3
                })
            
            reversal = self.create_journal_entry(
                journal_date=reversal_date,
                journal_type=JournalType.REVERSAL,
                description=f"Reversal of {original.journal_number}: {reversal_reason}",
                reference=original.journal_number,
                journal_lines=reversal_lines,
                source_module=original.source_module,
                source_reference=original.source_reference,
                auto_post=True,
                user_id=user_id
            )
            
            # Link reversal to original
            reversal.is_reversal = True
            reversal.reversal_of_id = original.id
            
            # Update original status
            original.posting_status = PostingStatus.REVERSED
            
            self.db.commit()
            self.db.refresh(reversal)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="journal_headers",
                record_id=str(original.id),
                operation="REVERSE",
                user_id=user_id,
                details=f"Reversed journal {original.journal_number}: {reversal_reason}"
            )
            
            return reversal
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reversing journal: {str(e)}"
            )
    
    def create_recurring_journal_template(
        self,
        template_name: str,
        journal_type: JournalType,
        description: str,
        journal_lines: List[Dict],
        frequency: str,  # MONTHLY, QUARTERLY, YEARLY
        next_date: date,
        user_id: int
    ) -> Dict:
        """
        Create recurring journal template
        Migrated from gl070.cbl CREATE-RECURRING
        """
        try:
            # In a real system, would save to recurring_journal_templates table
            template = {
                "template_name": template_name,
                "journal_type": journal_type,
                "description": description,
                "journal_lines": journal_lines,
                "frequency": frequency,
                "next_date": next_date,
                "created_by": str(user_id),
                "created_at": datetime.now()
            }
            
            # Create audit trail
            self._create_audit_trail(
                table_name="recurring_journals",
                record_id=template_name,
                operation="CREATE",
                user_id=user_id,
                details=f"Created recurring journal template: {template_name}"
            )
            
            return template
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating template: {str(e)}"
            )
    
    def get_journal_entries(
        self,
        period_id: Optional[int] = None,
        journal_type: Optional[JournalType] = None,
        posting_status: Optional[PostingStatus] = None,
        source_module: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """
        Get journal entries with filtering
        Migrated from gl070.cbl LIST-JOURNALS
        """
        try:
            query = self.db.query(JournalHeader)
            
            # Apply filters
            if period_id:
                query = query.filter(JournalHeader.period_id == period_id)
            
            if journal_type:
                query = query.filter(JournalHeader.journal_type == journal_type)
            
            if posting_status:
                query = query.filter(JournalHeader.posting_status == posting_status)
            
            if source_module:
                query = query.filter(JournalHeader.source_module == source_module)
            
            if from_date:
                query = query.filter(JournalHeader.journal_date >= from_date)
            
            if to_date:
                query = query.filter(JournalHeader.journal_date <= to_date)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            journals = query.order_by(JournalHeader.journal_date.desc(),
                                    JournalHeader.journal_number.desc())\
                          .offset((page - 1) * page_size)\
                          .limit(page_size)\
                          .all()
            
            return {
                "journals": journals,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving journals: {str(e)}"
            )
    
    def _post_journal(self, journal: JournalHeader, user_id: int):
        """Internal method to post journal to ledger"""
        # Update account balances
        for line in journal.journal_lines:
            # Get or create account balance for period
            balance = self.db.query(AccountBalance).filter(
                and_(
                    AccountBalance.account_id == line.account_id,
                    AccountBalance.period_id == journal.period_id
                )
            ).first()
            
            if not balance:
                # Create new balance record
                balance = AccountBalance(
                    account_id=line.account_id,
                    period_id=journal.period_id,
                    opening_balance=Decimal("0"),
                    period_debits=Decimal("0"),
                    period_credits=Decimal("0"),
                    closing_balance=Decimal("0")
                )
                self.db.add(balance)
            
            # Update balances
            balance.period_debits += line.debit_amount
            balance.period_credits += line.credit_amount
            balance.closing_balance = (
                balance.opening_balance + 
                balance.period_debits - 
                balance.period_credits
            )
            
            # Update account current balance
            account = line.account
            if account:
                account.current_balance = balance.closing_balance
                account.ytd_movement = balance.period_debits - balance.period_credits
                account.updated_at = datetime.now()
        
        # Update journal status
        journal.posting_status = PostingStatus.POSTED
        journal.posted_date = datetime.now()
        journal.posted_by = str(user_id)
        
        # Create audit trail
        self._create_audit_trail(
            table_name="journal_headers",
            record_id=str(journal.id),
            operation="POST",
            user_id=user_id,
            details=f"Posted journal {journal.journal_number}"
        )
    
    def _get_next_journal_number(self) -> str:
        """Generate next journal number"""
        sequence = self.db.query(NumberSequence).filter(
            NumberSequence.sequence_type == "JOURNAL"
        ).with_for_update().first()
        
        if not sequence:
            sequence = NumberSequence(
                sequence_type="JOURNAL",
                prefix="JNL",
                current_number=1,
                min_digits=6
            )
            self.db.add(sequence)
        
        sequence.current_number += 1
        number_str = str(sequence.current_number).zfill(sequence.min_digits)
        journal_number = f"{sequence.prefix}{number_str}"
        
        self.db.commit()
        return journal_number