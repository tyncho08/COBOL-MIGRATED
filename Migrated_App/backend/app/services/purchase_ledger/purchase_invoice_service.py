"""
Purchase Invoice Service
Migrated from COBOL pl910.cbl, pl920.cbl, pl930.cbl
Handles purchase invoice processing, matching, and posting
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status

from app.models.purchase_transactions import (
    PurchaseInvoice, PurchaseInvoiceLine,
    PurchaseOrder, PurchaseOrderLine,
    GoodsReceipt, GoodsReceiptLine
)
from app.models.suppliers import Supplier
from app.models.stock import StockItem
from app.models.control_tables import NumberSequence
from app.models.system import AuditTrail, CompanyPeriod
from app.models.general_ledger import JournalHeader, JournalLine, JournalType, PostingStatus
from app.core.calculations.vat_calculator import VATCalculator
from app.core.calculations.discount_calculator import DiscountCalculator
from app.services.base import BaseService


class PurchaseInvoiceService(BaseService):
    """Purchase invoice processing service"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.vat_calculator = VATCalculator()
        self.discount_calculator = DiscountCalculator()
    
    def create_purchase_invoice(
        self,
        supplier_code: str,
        supplier_invoice_no: str,
        invoice_date: date,
        invoice_lines: List[Dict],
        payment_terms: Optional[int] = None,
        purchase_order_id: Optional[int] = None,
        goods_receipt_id: Optional[int] = None,
        notes: Optional[str] = None,
        user_id: int = None
    ) -> PurchaseInvoice:
        """
        Create purchase invoice
        Migrated from pl910.cbl CREATE-PURCHASE-INVOICE
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
            
            # Check for duplicate invoice
            existing = self.db.query(PurchaseInvoice).filter(
                and_(
                    PurchaseInvoice.supplier_id == supplier.id,
                    PurchaseInvoice.supplier_invoice_no == supplier_invoice_no
                )
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Duplicate invoice {supplier_invoice_no} for supplier {supplier_code}"
                )
            
            # Generate invoice number
            invoice_number = self._get_next_invoice_number()
            
            # Get current period
            period = self._get_current_period()
            
            # Calculate due date
            payment_terms = payment_terms or supplier.payment_terms or 30
            due_date = invoice_date + timedelta(days=payment_terms)
            
            # Create invoice header
            invoice = PurchaseInvoice(
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                invoice_type="INVOICE",
                supplier_id=supplier.id,
                supplier_invoice_no=supplier_invoice_no,
                purchase_order_id=purchase_order_id,
                goods_receipt_id=goods_receipt_id,
                currency_code=supplier.currency_code or "USD",
                exchange_rate=Decimal("1.0"),
                payment_terms=payment_terms,
                due_date=due_date,
                settlement_discount=supplier.settlement_discount or Decimal("0"),
                settlement_days=supplier.settlement_days or 0,
                period_number=period.period_number,
                notes=notes,
                created_by=str(user_id) if user_id else None
            )
            
            self.db.add(invoice)
            self.db.flush()
            
            # Process invoice lines
            line_number = 0
            goods_total = Decimal("0")
            discount_total = Decimal("0")
            vat_total = Decimal("0")
            
            for line_data in invoice_lines:
                line_number += 10
                
                # Get stock item if specified
                stock_item = None
                if line_data.get("stock_code"):
                    stock_item = self.db.query(StockItem).filter(
                        StockItem.stock_code == line_data["stock_code"]
                    ).first()
                
                # Calculate amounts
                quantity = Decimal(str(line_data["quantity"]))
                unit_price = Decimal(str(line_data["unit_price"]))
                line_total = quantity * unit_price
                
                # Apply discount
                discount_percent = Decimal(str(line_data.get("discount_percent", "0")))
                if discount_percent > 0:
                    discount_amount = self.discount_calculator.calculate_discount(
                        line_total, discount_percent
                    )
                else:
                    discount_amount = Decimal("0")
                
                net_amount = line_total - discount_amount
                
                # Calculate VAT
                vat_code = line_data.get("vat_code", "S")
                vat_amount, _, vat_rate = self.vat_calculator.calculate_vat(
                    net_amount, vat_code, invoice_date
                )
                
                # Create invoice line
                invoice_line = PurchaseInvoiceLine(
                    invoice_id=invoice.id,
                    line_number=line_number,
                    po_line_id=line_data.get("po_line_id"),
                    receipt_line_id=line_data.get("receipt_line_id"),
                    stock_id=stock_item.id if stock_item else None,
                    stock_code=stock_item.stock_code if stock_item else line_data.get("stock_code"),
                    description=line_data["description"],
                    quantity=quantity,
                    unit_price=unit_price,
                    discount_percent=discount_percent,
                    discount_amount=discount_amount,
                    net_amount=net_amount,
                    vat_code=vat_code,
                    vat_rate=vat_rate,
                    vat_amount=vat_amount,
                    gl_account=line_data.get("gl_account"),
                    analysis_code1=line_data.get("analysis_code1"),
                    analysis_code2=line_data.get("analysis_code2"),
                    analysis_code3=line_data.get("analysis_code3")
                )
                
                invoice.invoice_lines.append(invoice_line)
                
                # Update totals
                goods_total += line_total
                discount_total += discount_amount
                vat_total += vat_amount
                
                # Calculate variances if linked to PO
                if line_data.get("po_line_id"):
                    self._calculate_price_variance(invoice_line, line_data["po_line_id"])
            
            # Update invoice totals
            invoice.goods_total = goods_total
            invoice.discount_total = discount_total
            invoice.net_total = goods_total - discount_total
            invoice.vat_total = vat_total
            invoice.gross_total = invoice.net_total + vat_total
            invoice.balance = invoice.gross_total
            
            self.db.commit()
            self.db.refresh(invoice)
            
            # Auto-match if linked to receipt
            if goods_receipt_id:
                self.match_invoice_to_receipt(invoice.id, goods_receipt_id, user_id)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="purchase_invoices",
                record_id=str(invoice.id),
                operation="CREATE",
                user_id=user_id,
                details=f"Created purchase invoice {invoice_number}"
            )
            
            return invoice
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating purchase invoice: {str(e)}"
            )
    
    def create_purchase_credit_note(
        self,
        supplier_code: str,
        supplier_credit_no: str,
        credit_date: date,
        original_invoice_id: Optional[int] = None,
        credit_lines: List[Dict] = None,
        reason: Optional[str] = None,
        user_id: int = None
    ) -> PurchaseInvoice:
        """
        Create purchase credit note
        Migrated from pl920.cbl CREATE-CREDIT-NOTE
        """
        try:
            # Create as negative invoice
            credit_note = self.create_purchase_invoice(
                supplier_code=supplier_code,
                supplier_invoice_no=supplier_credit_no,
                invoice_date=credit_date,
                invoice_lines=credit_lines,
                notes=f"Credit Note: {reason}" if reason else "Credit Note",
                user_id=user_id
            )
            
            # Update type and make amounts negative
            credit_note.invoice_type = "CREDIT_NOTE"
            credit_note.goods_total = -abs(credit_note.goods_total)
            credit_note.discount_total = -abs(credit_note.discount_total)
            credit_note.net_total = -abs(credit_note.net_total)
            credit_note.vat_total = -abs(credit_note.vat_total)
            credit_note.gross_total = -abs(credit_note.gross_total)
            credit_note.balance = credit_note.gross_total
            
            # Link to original invoice if provided
            if original_invoice_id:
                original = self.db.query(PurchaseInvoice).filter(
                    PurchaseInvoice.id == original_invoice_id
                ).first()
                if original:
                    credit_note.notes = f"{credit_note.notes}\nOriginal invoice: {original.invoice_number}"
            
            self.db.commit()
            self.db.refresh(credit_note)
            
            return credit_note
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating credit note: {str(e)}"
            )
    
    def match_invoice_to_receipt(
        self,
        invoice_id: int,
        receipt_id: int,
        user_id: int
    ) -> PurchaseInvoice:
        """
        Match invoice to goods receipt
        Migrated from pl920.cbl MATCH-INVOICE
        """
        try:
            # Get invoice and receipt
            invoice = self.db.query(PurchaseInvoice).filter(
                PurchaseInvoice.id == invoice_id
            ).first()
            if not invoice:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Purchase invoice not found"
                )
            
            receipt = self.db.query(GoodsReceipt).filter(
                GoodsReceipt.id == receipt_id
            ).first()
            if not receipt:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Goods receipt not found"
                )
            
            # Validate matching
            if invoice.supplier_id != receipt.supplier_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invoice and receipt have different suppliers"
                )
            
            # Match lines
            total_variance = Decimal("0")
            matched_lines = 0
            
            for inv_line in invoice.invoice_lines:
                # Find matching receipt line
                for rec_line in receipt.receipt_lines:
                    if (inv_line.stock_code == rec_line.stock_code and
                        inv_line.quantity == rec_line.quantity_accepted):
                        inv_line.receipt_line_id = rec_line.id
                        matched_lines += 1
                        break
            
            # Calculate any price variances
            if invoice.purchase_order_id:
                total_variance = self._calculate_total_variance(invoice)
            
            # Update invoice
            invoice.goods_receipt_id = receipt_id
            invoice.is_matched = matched_lines == len(invoice.invoice_lines)
            invoice.matched_amount = invoice.gross_total
            invoice.variance_amount = total_variance
            invoice.matched_date = datetime.now()
            invoice.matched_by = str(user_id)
            
            # Update receipt
            receipt.invoice_matched = True
            
            self.db.commit()
            self.db.refresh(invoice)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="purchase_invoices",
                record_id=str(invoice.id),
                operation="MATCH",
                user_id=user_id,
                details=f"Matched invoice {invoice.invoice_number} to GRN {receipt.receipt_number}"
            )
            
            return invoice
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error matching invoice: {str(e)}"
            )
    
    def post_invoice_to_gl(
        self,
        invoice_id: int,
        user_id: int
    ) -> JournalHeader:
        """
        Post purchase invoice to General Ledger
        Migrated from pl930.cbl POST-TO-GL
        """
        try:
            # Get invoice
            invoice = self.db.query(PurchaseInvoice).filter(
                PurchaseInvoice.id == invoice_id
            ).first()
            if not invoice:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Purchase invoice not found"
                )
            
            if invoice.gl_posted:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invoice already posted to GL"
                )
            
            # Get period
            period = self._get_period_for_date(invoice.invoice_date)
            if not period.is_open:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Period is closed for posting"
                )
            
            # Create journal header
            journal = JournalHeader(
                journal_number=self._get_next_journal_number(),
                journal_date=datetime.now(),
                journal_type=JournalType.PURCHASE,
                period_id=period.id,
                period_number=period.period_number,
                year_number=period.year_number,
                description=f"Purchase Invoice {invoice.invoice_number}",
                reference=invoice.supplier_invoice_no,
                source_module="PL",
                source_reference=invoice.invoice_number,
                posting_status=PostingStatus.DRAFT,
                created_by=str(user_id)
            )
            
            self.db.add(journal)
            self.db.flush()
            
            # Create journal lines
            line_number = 0
            
            # Credit: Creditors Control Account
            line_number += 10
            control_line = JournalLine(
                journal_id=journal.id,
                line_number=line_number,
                account_code="2100.0000",  # Creditors Control
                debit_amount=Decimal("0"),
                credit_amount=invoice.gross_total,
                description=f"Supplier: {invoice.supplier.supplier_name}",
                reference=invoice.supplier_invoice_no
            )
            journal.journal_lines.append(control_line)
            
            # Debit: Expense/Asset accounts from invoice lines
            for inv_line in invoice.invoice_lines:
                line_number += 10
                
                # Determine GL account
                gl_account = inv_line.gl_account
                if not gl_account:
                    if inv_line.stock_id:
                        # Stock item - use stock control account
                        gl_account = "1400.0000"  # Stock Control
                    else:
                        # Default expense account
                        gl_account = "5000.0000"  # Purchases
                
                expense_line = JournalLine(
                    journal_id=journal.id,
                    line_number=line_number,
                    account_code=gl_account,
                    debit_amount=inv_line.net_amount,
                    credit_amount=Decimal("0"),
                    description=inv_line.description,
                    analysis_code1=inv_line.analysis_code1,
                    analysis_code2=inv_line.analysis_code2,
                    analysis_code3=inv_line.analysis_code3
                )
                journal.journal_lines.append(expense_line)
            
            # Debit: VAT account
            if invoice.vat_total > 0:
                line_number += 10
                vat_line = JournalLine(
                    journal_id=journal.id,
                    line_number=line_number,
                    account_code="1300.0000",  # VAT Control
                    debit_amount=invoice.vat_total,
                    credit_amount=Decimal("0"),
                    description="Input VAT"
                )
                journal.journal_lines.append(vat_line)
            
            # Update journal totals
            journal.total_debits = sum(l.debit_amount for l in journal.journal_lines)
            journal.total_credits = sum(l.credit_amount for l in journal.journal_lines)
            journal.line_count = len(journal.journal_lines)
            
            # Post journal
            journal.posting_status = PostingStatus.POSTED
            journal.posted_date = datetime.now()
            journal.posted_by = str(user_id)
            
            # Update invoice
            invoice.gl_posted = True
            invoice.gl_batch_number = journal.journal_number
            
            self.db.commit()
            self.db.refresh(journal)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="purchase_invoices",
                record_id=str(invoice.id),
                operation="POST_GL",
                user_id=user_id,
                details=f"Posted invoice {invoice.invoice_number} to GL"
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
    
    def approve_for_payment(
        self,
        invoice_id: int,
        approver_id: int
    ) -> PurchaseInvoice:
        """
        Approve invoice for payment
        Migrated from pl930.cbl APPROVE-FOR-PAYMENT
        """
        try:
            invoice = self.db.query(PurchaseInvoice).filter(
                PurchaseInvoice.id == invoice_id
            ).first()
            if not invoice:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Purchase invoice not found"
                )
            
            if invoice.approved_for_payment:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invoice already approved for payment"
                )
            
            if invoice.on_hold:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot approve invoice on hold"
                )
            
            if invoice.dispute_flag:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot approve disputed invoice"
                )
            
            # Update invoice
            invoice.approved_for_payment = True
            invoice.approved_by = str(approver_id)
            invoice.approved_date = datetime.now()
            
            self.db.commit()
            self.db.refresh(invoice)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="purchase_invoices",
                record_id=str(invoice.id),
                operation="APPROVE",
                user_id=approver_id,
                details=f"Approved invoice {invoice.invoice_number} for payment"
            )
            
            return invoice
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error approving invoice: {str(e)}"
            )
    
    def _get_next_invoice_number(self) -> str:
        """Generate next purchase invoice number"""
        sequence = self.db.query(NumberSequence).filter(
            NumberSequence.sequence_type == "PURCHASE_INVOICE"
        ).with_for_update().first()
        
        if not sequence:
            sequence = NumberSequence(
                sequence_type="PURCHASE_INVOICE",
                prefix="PI",
                current_number=1,
                min_digits=6
            )
            self.db.add(sequence)
        
        sequence.current_number += 1
        number_str = str(sequence.current_number).zfill(sequence.min_digits)
        invoice_number = f"{sequence.prefix}{number_str}"
        
        self.db.commit()
        return invoice_number
    
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
    
    def _calculate_price_variance(
        self,
        invoice_line: PurchaseInvoiceLine,
        po_line_id: int
    ):
        """Calculate price variance between PO and invoice"""
        po_line = self.db.query(PurchaseOrderLine).filter(
            PurchaseOrderLine.id == po_line_id
        ).first()
        
        if po_line:
            invoice_line.po_price = po_line.unit_price
            invoice_line.price_variance = (
                invoice_line.unit_price - po_line.unit_price
            ) * invoice_line.quantity
            invoice_line.quantity_variance = (
                invoice_line.quantity - po_line.quantity_ordered
            )
    
    def _calculate_total_variance(self, invoice: PurchaseInvoice) -> Decimal:
        """Calculate total price variance for invoice"""
        total_variance = Decimal("0")
        
        for line in invoice.invoice_lines:
            if line.price_variance:
                total_variance += line.price_variance
        
        return total_variance