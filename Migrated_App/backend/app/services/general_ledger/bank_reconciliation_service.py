"""
Bank Reconciliation Service
Migrated from COBOL gl500.cbl, gl510.cbl, gl520.cbl
Handles bank reconciliation processing
"""
from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from app.models.general_ledger import (
    BankReconciliation, ChartOfAccounts, JournalLine, JournalHeader
)
from app.models.system import CompanyPeriod
from app.services.base import BaseService


class BankReconciliationService(BaseService):
    """Bank reconciliation processing service"""
    
    def create_reconciliation(
        self,
        bank_account_code: str,
        reconciliation_date: date,
        statement_balance: Decimal,
        statement_reference: Optional[str] = None,
        user_id: int = None
    ) -> BankReconciliation:
        """
        Create bank reconciliation
        Migrated from gl500.cbl CREATE-RECONCILIATION
        """
        try:
            # Get bank account
            bank_account = self.db.query(ChartOfAccounts).filter(
                ChartOfAccounts.account_code == bank_account_code
            ).first()
            if not bank_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Bank account {bank_account_code} not found"
                )
            
            # Check for existing reconciliation
            existing = self.db.query(BankReconciliation).filter(
                and_(
                    BankReconciliation.bank_account_id == bank_account.id,
                    BankReconciliation.reconciliation_date == reconciliation_date,
                    BankReconciliation.is_completed == False
                )
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Open reconciliation already exists for {reconciliation_date}"
                )
            
            # Get book balance
            book_balance = self._get_book_balance(bank_account.id, reconciliation_date)
            
            # Create reconciliation
            reconciliation = BankReconciliation(
                bank_account_id=bank_account.id,
                reconciliation_date=reconciliation_date,
                statement_balance=statement_balance,
                book_balance=book_balance,
                difference=statement_balance - book_balance,
                statement_reference=statement_reference,
                is_completed=False,
                outstanding_deposits=Decimal("0"),
                outstanding_payments=Decimal("0"),
                journal_adjustments=Decimal("0"),
                created_by=str(user_id) if user_id else None
            )
            
            self.db.add(reconciliation)
            self.db.commit()
            self.db.refresh(reconciliation)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="bank_reconciliations",
                record_id=str(reconciliation.id),
                operation="CREATE",
                user_id=user_id,
                details=f"Created bank reconciliation for {bank_account_code}"
            )
            
            return reconciliation
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating reconciliation: {str(e)}"
            )
    
    def add_outstanding_item(
        self,
        reconciliation_id: int,
        transaction_type: str,  # DEPOSIT, PAYMENT
        transaction_date: date,
        amount: Decimal,
        description: str,
        reference: Optional[str] = None,
        journal_line_id: Optional[int] = None,
        user_id: int = None
    ) -> Dict:
        """
        Add outstanding item to reconciliation
        Migrated from gl510.cbl ADD-OUTSTANDING
        """
        try:
            # Get reconciliation
            reconciliation = self.db.query(BankReconciliation).filter(
                BankReconciliation.id == reconciliation_id
            ).first()
            if not reconciliation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reconciliation not found"
                )
            
            if reconciliation.is_completed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot modify completed reconciliation"
                )
            
            # Validate transaction type and amount
            if transaction_type not in ["DEPOSIT", "PAYMENT"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transaction type must be DEPOSIT or PAYMENT"
                )
            
            if amount <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Amount must be positive"
                )
            
            # Create outstanding item entry
            outstanding_item = {
                "reconciliation_id": reconciliation_id,
                "transaction_type": transaction_type,
                "transaction_date": transaction_date,
                "amount": amount,
                "description": description,
                "reference": reference,
                "journal_line_id": journal_line_id,
                "created_date": datetime.now(),
                "created_by": str(user_id) if user_id else None
            }
            
            # Update reconciliation totals
            if transaction_type == "DEPOSIT":
                reconciliation.outstanding_deposits += amount
            else:  # PAYMENT
                reconciliation.outstanding_payments += amount
            
            # Recalculate difference
            adjusted_book_balance = (
                reconciliation.book_balance +
                reconciliation.outstanding_deposits -
                reconciliation.outstanding_payments +
                reconciliation.journal_adjustments
            )
            reconciliation.difference = reconciliation.statement_balance - adjusted_book_balance
            
            self.db.commit()
            
            # Create audit trail
            self._create_audit_trail(
                table_name="bank_reconciliations",
                record_id=str(reconciliation.id),
                operation="ADD_OUTSTANDING",
                user_id=user_id,
                details=f"Added outstanding {transaction_type.lower()}: {amount}",
                changes=outstanding_item
            )
            
            return outstanding_item
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error adding outstanding item: {str(e)}"
            )
    
    def create_adjustment_journal(
        self,
        reconciliation_id: int,
        adjustment_type: str,  # BANK_CHARGE, INTEREST, ERROR_CORRECTION
        amount: Decimal,
        description: str,
        contra_account_code: str,
        reference: Optional[str] = None,
        user_id: int = None
    ) -> int:
        """
        Create adjustment journal entry
        Migrated from gl510.cbl CREATE-ADJUSTMENT
        """
        try:
            # Get reconciliation
            reconciliation = self.db.query(BankReconciliation).filter(
                BankReconciliation.id == reconciliation_id
            ).first()
            if not reconciliation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reconciliation not found"
                )
            
            # Get bank account
            bank_account = reconciliation.bank_account
            
            # Get contra account
            contra_account = self.db.query(ChartOfAccounts).filter(
                ChartOfAccounts.account_code == contra_account_code
            ).first()
            if not contra_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Contra account {contra_account_code} not found"
                )
            
            # Create journal entry
            from app.services.general_ledger.journal_entry_service import JournalEntryService
            journal_service = JournalEntryService(self.db)
            
            # Determine debit/credit based on adjustment type
            if adjustment_type in ["BANK_CHARGE", "ERROR_CORRECTION"]:
                # Bank charge - credit bank, debit expense
                journal_lines = [
                    {
                        "account_code": bank_account.account_code,
                        "debit_amount": "0",
                        "credit_amount": str(amount),
                        "description": description,
                        "reference": reference
                    },
                    {
                        "account_code": contra_account_code,
                        "debit_amount": str(amount),
                        "credit_amount": "0",
                        "description": description,
                        "reference": reference
                    }
                ]
            else:  # INTEREST
                # Interest earned - debit bank, credit income
                journal_lines = [
                    {
                        "account_code": bank_account.account_code,
                        "debit_amount": str(amount),
                        "credit_amount": "0",
                        "description": description,
                        "reference": reference
                    },
                    {
                        "account_code": contra_account_code,
                        "debit_amount": "0",
                        "credit_amount": str(amount),
                        "description": description,
                        "reference": reference
                    }
                ]
            
            journal = journal_service.create_journal_entry(
                journal_date=reconciliation.reconciliation_date,
                journal_type="ADJUSTMENT",
                description=f"Bank reconciliation adjustment: {description}",
                reference=reference,
                journal_lines=journal_lines,
                source_module="BANK_REC",
                source_reference=str(reconciliation_id),
                auto_post=True,
                user_id=user_id
            )
            
            # Update reconciliation
            if adjustment_type in ["BANK_CHARGE"]:
                reconciliation.journal_adjustments -= amount
            else:  # INTEREST, ERROR_CORRECTION
                reconciliation.journal_adjustments += amount
            
            # Recalculate difference
            adjusted_book_balance = (
                reconciliation.book_balance +
                reconciliation.outstanding_deposits -
                reconciliation.outstanding_payments +
                reconciliation.journal_adjustments
            )
            reconciliation.difference = reconciliation.statement_balance - adjusted_book_balance
            
            self.db.commit()
            
            return journal.id
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating adjustment journal: {str(e)}"
            )
    
    def complete_reconciliation(
        self,
        reconciliation_id: int,
        user_id: int,
        force_complete: bool = False
    ) -> BankReconciliation:
        """
        Complete bank reconciliation
        Migrated from gl520.cbl COMPLETE-RECONCILIATION
        """
        try:
            # Get reconciliation
            reconciliation = self.db.query(BankReconciliation).filter(
                BankReconciliation.id == reconciliation_id
            ).first()
            if not reconciliation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reconciliation not found"
                )
            
            if reconciliation.is_completed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reconciliation already completed"
                )
            
            # Check if balanced
            if not force_complete and reconciliation.difference != 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Reconciliation not balanced. Difference: {reconciliation.difference}"
                )
            
            # Complete reconciliation
            reconciliation.is_completed = True
            reconciliation.completed_date = datetime.now()
            reconciliation.completed_by = str(user_id)
            
            # If forced complete with difference, create suspense entry
            if force_complete and reconciliation.difference != 0:
                # Create suspense journal entry
                suspense_account = "9999.0001"  # Suspense account
                
                self.create_adjustment_journal(
                    reconciliation_id=reconciliation_id,
                    adjustment_type="ERROR_CORRECTION",
                    amount=abs(reconciliation.difference),
                    description=f"Reconciliation difference - suspense",
                    contra_account_code=suspense_account,
                    reference=f"REC{reconciliation.id}",
                    user_id=user_id
                )
            
            self.db.commit()
            self.db.refresh(reconciliation)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="bank_reconciliations",
                record_id=str(reconciliation.id),
                operation="COMPLETE",
                user_id=user_id,
                details=f"Completed bank reconciliation with difference: {reconciliation.difference}"
            )
            
            return reconciliation
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error completing reconciliation: {str(e)}"
            )
    
    def get_unreconciled_items(
        self,
        bank_account_code: str,
        up_to_date: date,
        transaction_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get unreconciled bank transactions
        Migrated from gl520.cbl GET-UNRECONCILED
        """
        try:
            # Get bank account
            bank_account = self.db.query(ChartOfAccounts).filter(
                ChartOfAccounts.account_code == bank_account_code
            ).first()
            if not bank_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Bank account {bank_account_code} not found"
                )
            
            # Get unreconciled journal lines
            query = self.db.query(
                JournalLine,
                JournalHeader
            ).join(
                JournalHeader,
                JournalHeader.id == JournalLine.journal_id
            ).filter(
                and_(
                    JournalLine.account_id == bank_account.id,
                    JournalHeader.journal_date <= up_to_date,
                    JournalHeader.posting_status == "POSTED",
                    JournalLine.is_reconciled == False
                )
            )
            
            if transaction_type == "DEPOSITS":
                query = query.filter(JournalLine.debit_amount > 0)
            elif transaction_type == "PAYMENTS":
                query = query.filter(JournalLine.credit_amount > 0)
            
            results = query.order_by(
                JournalHeader.journal_date,
                JournalHeader.journal_number
            ).all()
            
            unreconciled_items = []
            for line, header in results:
                amount = line.debit_amount if line.debit_amount > 0 else line.credit_amount
                trans_type = "DEPOSIT" if line.debit_amount > 0 else "PAYMENT"
                
                unreconciled_items.append({
                    "journal_line_id": line.id,
                    "journal_number": header.journal_number,
                    "journal_date": header.journal_date,
                    "transaction_type": trans_type,
                    "amount": amount,
                    "description": line.description or header.description,
                    "reference": line.reference or header.reference,
                    "source_module": header.source_module
                })
            
            return unreconciled_items
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting unreconciled items: {str(e)}"
            )
    
    def get_reconciliation_report(
        self,
        reconciliation_id: int
    ) -> Dict:
        """
        Generate reconciliation report
        Migrated from gl520.cbl RECONCILIATION-REPORT
        """
        try:
            # Get reconciliation
            reconciliation = self.db.query(BankReconciliation).filter(
                BankReconciliation.id == reconciliation_id
            ).first()
            if not reconciliation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reconciliation not found"
                )
            
            # Get bank account
            bank_account = reconciliation.bank_account
            
            # Get outstanding items (from audit trail)
            # In a full implementation, would store these in separate table
            outstanding_deposits = []
            outstanding_payments = []
            
            # Calculate reconciliation
            book_balance = reconciliation.book_balance
            statement_balance = reconciliation.statement_balance
            
            # Add deposits in transit
            add_deposits = reconciliation.outstanding_deposits
            
            # Less outstanding payments
            less_payments = reconciliation.outstanding_payments
            
            # Add/subtract journal adjustments
            adjustments = reconciliation.journal_adjustments
            
            # Calculate reconciled balance
            reconciled_balance = (
                book_balance + 
                add_deposits - 
                less_payments + 
                adjustments
            )
            
            difference = statement_balance - reconciled_balance
            
            return {
                "reconciliation": {
                    "id": reconciliation.id,
                    "bank_account": {
                        "account_code": bank_account.account_code,
                        "account_name": bank_account.account_name
                    },
                    "reconciliation_date": reconciliation.reconciliation_date,
                    "statement_reference": reconciliation.statement_reference,
                    "is_completed": reconciliation.is_completed,
                    "completed_date": reconciliation.completed_date
                },
                "balances": {
                    "statement_balance": statement_balance,
                    "book_balance": book_balance,
                    "reconciled_balance": reconciled_balance,
                    "difference": difference
                },
                "reconciling_items": {
                    "outstanding_deposits": {
                        "count": len(outstanding_deposits),
                        "total": add_deposits,
                        "items": outstanding_deposits
                    },
                    "outstanding_payments": {
                        "count": len(outstanding_payments),
                        "total": less_payments,
                        "items": outstanding_payments
                    },
                    "journal_adjustments": adjustments
                },
                "is_balanced": difference == 0
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating reconciliation report: {str(e)}"
            )
    
    def _get_book_balance(self, bank_account_id: int, as_of_date: date) -> Decimal:
        """Get book balance as of date"""
        try:
            # Get all posted journal lines up to date
            result = self.db.query(
                func.sum(JournalLine.debit_amount - JournalLine.credit_amount)
            ).join(
                JournalHeader,
                JournalHeader.id == JournalLine.journal_id
            ).filter(
                and_(
                    JournalLine.account_id == bank_account_id,
                    JournalHeader.journal_date <= as_of_date,
                    JournalHeader.posting_status == "POSTED"
                )
            ).scalar()
            
            return result or Decimal("0")
            
        except Exception:
            return Decimal("0")