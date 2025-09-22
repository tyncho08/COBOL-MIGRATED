"""
Supplier Payment Service
Migrated from COBOL pl120.cbl, pl125.cbl, pl130.cbl
Handles supplier payment processing and allocation
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status

from app.models.purchase_transactions import (
    SupplierPayment, SupplierPaymentAllocation,
    PurchaseInvoice
)
from app.models.suppliers import Supplier
from app.models.control_tables import NumberSequence
from app.models.system import AuditTrail, CompanyPeriod
from app.models.general_ledger import JournalHeader, JournalLine, JournalType, PostingStatus
from app.services.base import BaseService


class SupplierPaymentService(BaseService):
    """Supplier payment processing service"""
    
    def create_payment(
        self,
        supplier_code: str,
        payment_amount: Decimal,
        payment_method: str,
        payment_date: Optional[date] = None,
        bank_account: Optional[str] = None,
        check_number: Optional[str] = None,
        bank_reference: Optional[str] = None,
        allocations: Optional[List[Dict]] = None,
        user_id: int = None
    ) -> SupplierPayment:
        """
        Create supplier payment
        Migrated from pl120.cbl CREATE-PAYMENT
        """
        try:
            # Validate supplier
            supplier = self.db.query(Supplier).filter(
                Supplier.supplier_code == supplier_code
            ).first()
            if not supplier:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Supplier {supplier_code} not found"
                )
            
            # Validate payment method
            if payment_method not in ["CHECK", "TRANSFER", "CASH"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid payment method"
                )
            
            # Generate payment number
            payment_number = self._get_next_payment_number()
            
            # Get current period
            period = self._get_current_period()
            
            # Create payment
            payment = SupplierPayment(
                payment_number=payment_number,
                payment_date=payment_date or datetime.now().date(),
                supplier_id=supplier.id,
                supplier_code=supplier_code,
                payment_method=payment_method,
                bank_account=bank_account,
                check_number=check_number,
                currency_code=supplier.currency_code or "USD",
                payment_amount=payment_amount,
                allocated_amount=Decimal("0"),
                unallocated_amount=payment_amount,
                bank_reference=bank_reference,
                period_number=period.period_number,
                created_by=str(user_id) if user_id else None
            )
            
            self.db.add(payment)
            self.db.flush()
            
            # Process allocations if provided
            if allocations:
                allocated_total = self._process_allocations(
                    payment, allocations, user_id
                )
                payment.allocated_amount = allocated_total
                payment.unallocated_amount = payment_amount - allocated_total
                payment.is_allocated = payment.unallocated_amount == 0
            
            self.db.commit()
            self.db.refresh(payment)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="supplier_payments",
                record_id=str(payment.id),
                operation="CREATE",
                user_id=user_id,
                details=f"Created payment {payment_number} for {supplier_code}"
            )
            
            return payment
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating payment: {str(e)}"
            )
    
    def allocate_payment(
        self,
        payment_id: int,
        allocations: List[Dict],
        user_id: int
    ) -> SupplierPayment:
        """
        Allocate payment to invoices
        Migrated from pl125.cbl ALLOCATE-PAYMENT
        """
        try:
            # Get payment
            payment = self.db.query(SupplierPayment).filter(
                SupplierPayment.id == payment_id
            ).first()
            if not payment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found"
                )
            
            if payment.is_cancelled:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot allocate cancelled payment"
                )
            
            # Process allocations
            allocated_total = self._process_allocations(
                payment, allocations, user_id
            )
            
            # Update payment
            payment.allocated_amount += allocated_total
            payment.unallocated_amount = payment.payment_amount - payment.allocated_amount
            payment.is_allocated = payment.unallocated_amount == 0
            payment.updated_at = datetime.now()
            payment.updated_by = str(user_id)
            
            self.db.commit()
            self.db.refresh(payment)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="supplier_payments",
                record_id=str(payment.id),
                operation="ALLOCATE",
                user_id=user_id,
                details=f"Allocated payment {payment.payment_number}"
            )
            
            return payment
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error allocating payment: {str(e)}"
            )
    
    def create_payment_run(
        self,
        supplier_codes: Optional[List[str]] = None,
        due_date_cutoff: Optional[date] = None,
        minimum_amount: Optional[Decimal] = None,
        payment_method: str = "TRANSFER",
        user_id: int = None
    ) -> List[SupplierPayment]:
        """
        Create payment run for multiple suppliers
        Migrated from pl130.cbl PAYMENT-RUN
        """
        try:
            # Get payment run number
            run_number = self._get_next_payment_run_number()
            
            # Query approved invoices
            query = self.db.query(PurchaseInvoice).filter(
                and_(
                    PurchaseInvoice.approved_for_payment == True,
                    PurchaseInvoice.balance > 0,
                    PurchaseInvoice.on_hold == False,
                    PurchaseInvoice.dispute_flag == False
                )
            )
            
            if supplier_codes:
                query = query.join(Supplier).filter(
                    Supplier.supplier_code.in_(supplier_codes)
                )
            
            if due_date_cutoff:
                query = query.filter(PurchaseInvoice.due_date <= due_date_cutoff)
            
            # Group by supplier
            invoices_by_supplier = {}
            for invoice in query.all():
                if invoice.supplier_id not in invoices_by_supplier:
                    invoices_by_supplier[invoice.supplier_id] = []
                invoices_by_supplier[invoice.supplier_id].append(invoice)
            
            # Create payments
            payments = []
            
            for supplier_id, invoices in invoices_by_supplier.items():
                # Calculate total to pay
                total_amount = sum(inv.balance for inv in invoices)
                
                # Apply settlement discount if applicable
                discount_amount = Decimal("0")
                allocations = []
                
                for invoice in invoices:
                    allocation_amount = invoice.balance
                    discount_taken = Decimal("0")
                    
                    # Check settlement discount
                    if invoice.settlement_discount > 0:
                        days_since_invoice = (datetime.now().date() - invoice.invoice_date.date()).days
                        if days_since_invoice <= invoice.settlement_days:
                            discount_taken = (
                                allocation_amount * invoice.settlement_discount / 100
                            ).quantize(Decimal("0.01"))
                            discount_amount += discount_taken
                    
                    allocations.append({
                        "invoice_id": invoice.id,
                        "amount": allocation_amount,
                        "discount": discount_taken
                    })
                
                # Apply minimum amount filter
                net_amount = total_amount - discount_amount
                if minimum_amount and net_amount < minimum_amount:
                    continue
                
                # Get supplier
                supplier = self.db.query(Supplier).filter(
                    Supplier.id == supplier_id
                ).first()
                
                # Create payment
                payment = self.create_payment(
                    supplier_code=supplier.supplier_code,
                    payment_amount=net_amount,
                    payment_method=payment_method,
                    bank_account=supplier.bank_account_no,
                    allocations=allocations,
                    user_id=user_id
                )
                
                payment.payment_run_number = run_number
                payments.append(payment)
            
            self.db.commit()
            
            # Create audit trail
            self._create_audit_trail(
                table_name="supplier_payments",
                record_id=run_number,
                operation="PAYMENT_RUN",
                user_id=user_id,
                details=f"Created payment run {run_number} with {len(payments)} payments"
            )
            
            return payments
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating payment run: {str(e)}"
            )
    
    def post_payment_to_gl(
        self,
        payment_id: int,
        user_id: int
    ) -> JournalHeader:
        """
        Post payment to General Ledger
        Migrated from pl130.cbl POST-PAYMENT-GL
        """
        try:
            # Get payment
            payment = self.db.query(SupplierPayment).filter(
                SupplierPayment.id == payment_id
            ).first()
            if not payment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found"
                )
            
            if payment.gl_posted:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment already posted to GL"
                )
            
            # Get period
            period = self._get_period_for_date(payment.payment_date)
            if not period.is_open:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Period is closed for posting"
                )
            
            # Create journal header
            journal = JournalHeader(
                journal_number=self._get_next_journal_number(),
                journal_date=datetime.now(),
                journal_type=JournalType.CASH_PAYMENT,
                period_id=period.id,
                period_number=period.period_number,
                year_number=period.year_number,
                description=f"Supplier Payment {payment.payment_number}",
                reference=payment.check_number or payment.bank_reference,
                source_module="PL",
                source_reference=payment.payment_number,
                posting_status=PostingStatus.DRAFT,
                created_by=str(user_id)
            )
            
            self.db.add(journal)
            self.db.flush()
            
            # Create journal lines
            line_number = 0
            
            # Debit: Creditors Control Account
            line_number += 10
            control_line = JournalLine(
                journal_id=journal.id,
                line_number=line_number,
                account_code="2100.0000",  # Creditors Control
                debit_amount=payment.payment_amount,
                credit_amount=Decimal("0"),
                description=f"Payment to: {payment.supplier.supplier_name}",
                reference=payment.payment_number
            )
            journal.journal_lines.append(control_line)
            
            # Credit: Bank/Cash Account
            line_number += 10
            bank_account_code = self._get_bank_account_code(payment.payment_method, payment.bank_account)
            bank_line = JournalLine(
                journal_id=journal.id,
                line_number=line_number,
                account_code=bank_account_code,
                debit_amount=Decimal("0"),
                credit_amount=payment.payment_amount,
                description=f"{payment.payment_method} payment",
                reference=payment.check_number or payment.bank_reference
            )
            journal.journal_lines.append(bank_line)
            
            # Settlement discount if any
            total_discount = sum(
                alloc.discount_taken for alloc in payment.allocations
            )
            if total_discount > 0:
                line_number += 10
                discount_line = JournalLine(
                    journal_id=journal.id,
                    line_number=line_number,
                    account_code="4100.0000",  # Discount Received
                    debit_amount=Decimal("0"),
                    credit_amount=total_discount,
                    description="Settlement discount"
                )
                journal.journal_lines.append(discount_line)
                
                # Adjust control account
                control_line.debit_amount += total_discount
            
            # Update journal totals
            journal.total_debits = sum(l.debit_amount for l in journal.journal_lines)
            journal.total_credits = sum(l.credit_amount for l in journal.journal_lines)
            journal.line_count = len(journal.journal_lines)
            
            # Post journal
            journal.posting_status = PostingStatus.POSTED
            journal.posted_date = datetime.now()
            journal.posted_by = str(user_id)
            
            # Update payment
            payment.gl_posted = True
            payment.gl_batch_number = journal.journal_number
            
            self.db.commit()
            self.db.refresh(journal)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="supplier_payments",
                record_id=str(payment.id),
                operation="POST_GL",
                user_id=user_id,
                details=f"Posted payment {payment.payment_number} to GL"
            )
            
            return journal
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error posting to GL: {str(e)}"
            )
    
    def cancel_payment(
        self,
        payment_id: int,
        reason: str,
        user_id: int
    ) -> SupplierPayment:
        """
        Cancel payment
        Migrated from pl120.cbl CANCEL-PAYMENT
        """
        try:
            payment = self.db.query(SupplierPayment).filter(
                SupplierPayment.id == payment_id
            ).first()
            if not payment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found"
                )
            
            if payment.gl_posted:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot cancel posted payment"
                )
            
            if payment.is_printed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot cancel printed check"
                )
            
            # Reverse allocations
            for allocation in payment.allocations:
                invoice = allocation.invoice
                invoice.amount_paid -= allocation.allocated_amount
                invoice.balance += allocation.allocated_amount
                if allocation.discount_taken > 0:
                    invoice.balance += allocation.discount_taken
                invoice.is_paid = False
                
                self.db.delete(allocation)
            
            # Update payment
            payment.is_cancelled = True
            payment.notes = f"{payment.notes}\nCANCELLED: {reason}" if payment.notes else f"CANCELLED: {reason}"
            payment.updated_at = datetime.now()
            payment.updated_by = str(user_id)
            
            self.db.commit()
            self.db.refresh(payment)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="supplier_payments",
                record_id=str(payment.id),
                operation="CANCEL",
                user_id=user_id,
                details=f"Cancelled payment {payment.payment_number}: {reason}"
            )
            
            return payment
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error cancelling payment: {str(e)}"
            )
    
    def _process_allocations(
        self,
        payment: SupplierPayment,
        allocations: List[Dict],
        user_id: int
    ) -> Decimal:
        """Process payment allocations to invoices"""
        total_allocated = Decimal("0")
        
        for alloc_data in allocations:
            # Get invoice
            invoice = self.db.query(PurchaseInvoice).filter(
                PurchaseInvoice.id == alloc_data["invoice_id"]
            ).first()
            if not invoice:
                continue
            
            # Validate supplier
            if invoice.supplier_id != payment.supplier_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invoice {invoice.invoice_number} belongs to different supplier"
                )
            
            # Calculate allocation amount
            amount_to_allocate = min(
                Decimal(str(alloc_data["amount"])),
                invoice.balance
            )
            discount_taken = Decimal(str(alloc_data.get("discount", "0")))
            
            if amount_to_allocate <= 0:
                continue
            
            # Create allocation
            allocation = SupplierPaymentAllocation(
                payment_id=payment.id,
                invoice_id=invoice.id,
                allocation_date=datetime.now(),
                allocated_amount=amount_to_allocate,
                discount_taken=discount_taken,
                created_by=str(user_id) if user_id else None
            )
            
            payment.allocations.append(allocation)
            
            # Update invoice
            invoice.amount_paid += amount_to_allocate
            invoice.balance = invoice.gross_total - invoice.amount_paid
            if discount_taken > 0:
                invoice.balance -= discount_taken
            invoice.is_paid = invoice.balance <= 0
            
            total_allocated += amount_to_allocate + discount_taken
        
        return total_allocated
    
    def _get_next_payment_number(self) -> str:
        """Generate next payment number"""
        sequence = self.db.query(NumberSequence).filter(
            NumberSequence.sequence_type == "SUPPLIER_PAYMENT"
        ).with_for_update().first()
        
        if not sequence:
            sequence = NumberSequence(
                sequence_type="SUPPLIER_PAYMENT",
                prefix="SP",
                current_number=1,
                min_digits=6
            )
            self.db.add(sequence)
        
        sequence.current_number += 1
        number_str = str(sequence.current_number).zfill(sequence.min_digits)
        payment_number = f"{sequence.prefix}{number_str}"
        
        self.db.commit()
        return payment_number
    
    def _get_next_payment_run_number(self) -> str:
        """Generate next payment run number"""
        sequence = self.db.query(NumberSequence).filter(
            NumberSequence.sequence_type == "PAYMENT_RUN"
        ).with_for_update().first()
        
        if not sequence:
            sequence = NumberSequence(
                sequence_type="PAYMENT_RUN",
                prefix="PR",
                current_number=1,
                min_digits=4
            )
            self.db.add(sequence)
        
        sequence.current_number += 1
        number_str = str(sequence.current_number).zfill(sequence.min_digits)
        run_number = f"{sequence.prefix}{number_str}"
        
        self.db.commit()
        return run_number
    
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
    
    def _get_bank_account_code(self, payment_method: str, bank_account: str) -> str:
        """Get GL account code for bank/cash"""
        # In a real system, this would look up the bank account mapping
        if payment_method == "CASH":
            return "1100.0000"  # Cash Account
        else:
            return "1200.0000"  # Bank Account