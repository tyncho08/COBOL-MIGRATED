"""
Invoice Service
Implementation of COBOL sl910.cbl - Invoice Generation (555 procedures)
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import (
    Customer, StockItem, SalesInvoice, SalesInvoiceLine,
    SalesOrder, SalesOrderLine, SystemConfig, AuditTrail
)
from app.core.calculations.vat_calculator import VATCalculator, VATCode
from app.core.calculations.discount_calculator import DiscountCalculator, DiscountType
from app.schemas.sales import InvoiceCreate, InvoiceLineCreate
from app.core.audit.audit_service import AuditService


class InvoiceService:
    """
    Invoice generation service implementing COBOL sl910 logic
    Handles complex invoice calculations, back orders, and GL posting
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.vat_calc = VATCalculator()
        self.discount_calc = DiscountCalculator()
        self.audit = AuditService(db)
        self._load_system_config()
    
    def _load_system_config(self):
        """Load system configuration"""
        self.config = self.db.query(SystemConfig).first()
        if not self.config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="System configuration not found"
            )
    
    def generate_invoice(
        self,
        invoice_data: InvoiceCreate,
        user_id: int,
        auto_post: bool = True
    ) -> SalesInvoice:
        """
        Generate invoice implementing COBOL sl910 logic
        
        This implements the complex 555-procedure COBOL program logic including:
        - Multi-line invoice processing
        - Back order handling
        - VAT calculations with multiple rates
        - Discount hierarchies
        - Credit limit checking
        - Stock allocation
        - GL posting preparation
        """
        
        # 1. Validate customer and credit
        customer = self._validate_customer(invoice_data.customer_id)
        
        # 2. Get next invoice number (COBOL: PERFORM GET-NEXT-INVOICE-NO)
        invoice_number = self._get_next_invoice_number()
        
        # 3. Initialize invoice totals
        invoice_totals = {
            "goods_total": Decimal("0.00"),
            "discount_total": Decimal("0.00"),
            "net_total": Decimal("0.00"),
            "vat_total": Decimal("0.00"),
            "gross_total": Decimal("0.00"),
            "vat_breakdown": {}
        }
        
        # 4. Create invoice header
        invoice = SalesInvoice(
            invoice_number=invoice_number,
            invoice_date=invoice_data.invoice_date or datetime.now(),
            invoice_type=invoice_data.invoice_type,
            customer_id=customer.id,
            customer_code=customer.customer_code,
            customer_name=customer.customer_name,
            delivery_name=invoice_data.delivery_name or customer.customer_name,
            delivery_address1=invoice_data.delivery_address1 or customer.address_line1,
            delivery_address2=invoice_data.delivery_address2 or customer.address_line2,
            delivery_address3=invoice_data.delivery_address3 or customer.address_line3,
            delivery_postcode=invoice_data.delivery_postcode or customer.postcode,
            customer_reference=invoice_data.customer_reference,
            order_number=invoice_data.order_number,
            delivery_note=invoice_data.delivery_note,
            currency_code=customer.currency_code,
            exchange_rate=Decimal("1.000000"),  # TODO: Get from exchange rate service
            payment_terms=customer.payment_terms,
            settlement_discount=customer.settlement_discount,
            settlement_days=customer.settlement_days,
            created_by=str(user_id),
            updated_by=str(user_id)
        )
        
        # Calculate due date
        invoice.due_date = invoice.invoice_date + timedelta(days=customer.payment_terms)
        
        # 5. Process invoice lines (COBOL: PERFORM PROCESS-INVOICE-LINES)
        invoice_lines = []
        back_orders = []
        
        for line_no, line_data in enumerate(invoice_data.lines, 1):
            line_result = self._process_invoice_line(
                line_data, line_no, customer, invoice_totals
            )
            
            if line_result["line"]:
                invoice_lines.append(line_result["line"])
            
            if line_result["back_order"]:
                back_orders.append(line_result["back_order"])
        
        # 6. Apply header-level discount if any
        if invoice_data.header_discount_pct and invoice_data.header_discount_pct > 0:
            self._apply_header_discount(invoice_totals, invoice_data.header_discount_pct)
        
        # 7. Add extra charges (COBOL: ADD-EXTRA-CHARGES)
        if invoice_data.extra_charges:
            self._add_extra_charges(invoice_totals, invoice_data.extra_charges)
        
        # 8. Add shipping/carriage (COBOL: ADD-CARRIAGE)
        if invoice_data.shipping_charge:
            self._add_shipping(invoice_totals, invoice_data.shipping_charge)
        
        # 9. Calculate final totals
        invoice.goods_total = invoice_totals["goods_total"]
        invoice.discount_total = invoice_totals["discount_total"]
        invoice.net_total = invoice_totals["net_total"]
        invoice.vat_total = invoice_totals["vat_total"]
        invoice.gross_total = invoice_totals["gross_total"]
        invoice.balance = invoice.gross_total  # Initially unpaid
        
        # 10. Credit limit check for account invoices
        if invoice_data.invoice_type == "INVOICE" and not invoice_data.cash_sale:
            self._check_credit_limit(customer, invoice.gross_total)
        
        # 11. Save invoice and lines
        self.db.add(invoice)
        self.db.flush()  # Get invoice ID
        
        for line in invoice_lines:
            line.invoice_id = invoice.id
            self.db.add(line)
        
        # 12. Update stock quantities (COBOL: UPDATE-STOCK-QUANTITIES)
        for line in invoice_lines:
            if line.stock_id:
                self._update_stock_quantity(line.stock_id, line.quantity)
        
        # 13. Update customer balance
        self._update_customer_balance(customer, invoice)
        
        # 14. Create back orders if any
        if back_orders:
            self._create_back_orders(back_orders, customer, invoice)
        
        # 15. Create audit trail
        self.audit.create_audit_entry(
            table_name="sales_invoices",
            record_id=str(invoice.id),
            operation="CREATE",
            user_id=user_id,
            after_data={"invoice_number": invoice.invoice_number}
        )
        
        # 16. Prepare GL posting if auto-post
        if auto_post and self.config.auto_generate_gl_postings:
            self._prepare_gl_posting(invoice)
        
        # Commit transaction
        self.db.commit()
        
        return invoice
    
    def _validate_customer(self, customer_id: int) -> Customer:
        """Validate customer exists and is active"""
        customer = self.db.query(Customer).filter_by(id=customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        if not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer account is inactive"
            )
        
        if customer.on_hold:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer account is on hold"
            )
        
        return customer
    
    def _get_next_invoice_number(self) -> str:
        """Get next invoice number and increment counter"""
        # Lock the config record to prevent concurrent updates
        config = self.db.query(SystemConfig).with_for_update().first()
        
        # Format invoice number (8 digits as per COBOL)
        invoice_number = str(config.next_invoice_number).zfill(8)
        
        # Increment counter
        config.next_invoice_number += 1
        
        return invoice_number
    
    def _process_invoice_line(
        self,
        line_data: InvoiceLineCreate,
        line_number: int,
        customer: Customer,
        invoice_totals: Dict
    ) -> Dict:
        """
        Process individual invoice line with COBOL business logic
        """
        result = {"line": None, "back_order": None}
        
        # Get stock item if stock code provided
        stock_item = None
        if line_data.stock_code:
            stock_item = self.db.query(StockItem).filter_by(
                stock_code=line_data.stock_code
            ).first()
            
            if not stock_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Stock item {line_data.stock_code} not found"
                )
        
        # Create invoice line
        invoice_line = SalesInvoiceLine(
            line_number=line_number,
            stock_id=stock_item.id if stock_item else None,
            stock_code=line_data.stock_code,
            description=line_data.description or (stock_item.description if stock_item else ""),
            quantity=line_data.quantity,
            unit_price=line_data.unit_price or (stock_item.selling_price1 if stock_item else Decimal("0.00")),
            discount_percent=line_data.discount_percent or customer.discount_percentage,
            vat_code=line_data.vat_code or (stock_item.vat_code if stock_item else "S"),
            gl_account=line_data.gl_account,
            analysis_code1=line_data.analysis_code1 or customer.analysis_code1,
            analysis_code2=line_data.analysis_code2 or customer.analysis_code2,
            analysis_code3=line_data.analysis_code3 or customer.analysis_code3
        )
        
        # Check stock availability for physical items
        available_qty = Decimal("999999.999")  # Unlimited for non-stock items
        if stock_item and stock_item.is_stocked:
            available_qty = stock_item.quantity_on_hand - stock_item.quantity_allocated
            
            if available_qty < line_data.quantity:
                # Handle back order situation
                if customer.allow_partial_shipment:
                    # Ship what we have, back order the rest
                    back_order_qty = line_data.quantity - available_qty
                    invoice_line.quantity = available_qty
                    
                    if back_order_qty > 0:
                        result["back_order"] = {
                            "stock_code": stock_item.stock_code,
                            "quantity": back_order_qty,
                            "unit_price": invoice_line.unit_price,
                            "description": stock_item.description
                        }
                else:
                    # Cannot ship partial - back order everything
                    result["back_order"] = {
                        "stock_code": stock_item.stock_code,
                        "quantity": line_data.quantity,
                        "unit_price": invoice_line.unit_price,
                        "description": stock_item.description
                    }
                    return result  # Skip this line on invoice
        
        # Calculate line amounts (COBOL calculation sequence)
        # 1. Gross amount
        gross_amount = invoice_line.quantity * invoice_line.unit_price
        
        # 2. Apply discount
        discount_amount, net_amount = self.discount_calc.calculate_trade_discount(
            gross_amount, invoice_line.discount_percent
        )
        
        invoice_line.discount_amount = discount_amount
        invoice_line.net_amount = net_amount
        
        # 3. Calculate VAT
        vat_amount, _, vat_rate = self.vat_calc.calculate_vat(
            net_amount, invoice_line.vat_code
        )
        
        invoice_line.vat_rate = vat_rate
        invoice_line.vat_amount = vat_amount
        
        # 4. Update invoice totals
        invoice_totals["goods_total"] += gross_amount
        invoice_totals["discount_total"] += discount_amount
        invoice_totals["net_total"] += net_amount
        invoice_totals["vat_total"] += vat_amount
        
        # Track VAT breakdown by code
        if invoice_line.vat_code not in invoice_totals["vat_breakdown"]:
            invoice_totals["vat_breakdown"][invoice_line.vat_code] = {
                "net": Decimal("0.00"),
                "vat": Decimal("0.00"),
                "rate": vat_rate
            }
        invoice_totals["vat_breakdown"][invoice_line.vat_code]["net"] += net_amount
        invoice_totals["vat_breakdown"][invoice_line.vat_code]["vat"] += vat_amount
        
        result["line"] = invoice_line
        return result
    
    def _apply_header_discount(self, invoice_totals: Dict, discount_pct: Decimal):
        """Apply header-level discount to all lines proportionally"""
        # This is a simplified version - COBOL applies to each line
        header_discount = (invoice_totals["net_total"] * discount_pct / Decimal("100")).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )
        
        invoice_totals["discount_total"] += header_discount
        invoice_totals["net_total"] -= header_discount
        
        # Recalculate VAT on new net total
        # In practice, this would be done per VAT code
        invoice_totals["vat_total"] = Decimal("0.00")
        for vat_code, breakdown in invoice_totals["vat_breakdown"].items():
            # Proportionally reduce net amount
            proportion = breakdown["net"] / (invoice_totals["net_total"] + header_discount)
            new_net = invoice_totals["net_total"] * proportion
            new_vat, _, _ = self.vat_calc.calculate_vat(new_net, vat_code)
            invoice_totals["vat_total"] += new_vat
            breakdown["net"] = new_net
            breakdown["vat"] = new_vat
    
    def _add_extra_charges(self, invoice_totals: Dict, extra_charges: Decimal):
        """Add extra charges with standard VAT"""
        extra_charges = Decimal(str(extra_charges))
        vat_on_extras, _, _ = self.vat_calc.calculate_vat(extra_charges, VATCode.STANDARD)
        
        invoice_totals["net_total"] += extra_charges
        invoice_totals["vat_total"] += vat_on_extras
        
        # Update VAT breakdown
        if VATCode.STANDARD not in invoice_totals["vat_breakdown"]:
            invoice_totals["vat_breakdown"][VATCode.STANDARD] = {
                "net": Decimal("0.00"),
                "vat": Decimal("0.00"),
                "rate": self.vat_calc.VAT_RATES[VATCode.STANDARD]
            }
        invoice_totals["vat_breakdown"][VATCode.STANDARD]["net"] += extra_charges
        invoice_totals["vat_breakdown"][VATCode.STANDARD]["vat"] += vat_on_extras
    
    def _add_shipping(self, invoice_totals: Dict, shipping_charge: Decimal):
        """Add shipping/carriage with standard VAT (COBOL rule)"""
        shipping_charge = Decimal(str(shipping_charge))
        vat_on_shipping, _, _ = self.vat_calc.calculate_vat(shipping_charge, VATCode.STANDARD)
        
        invoice_totals["net_total"] += shipping_charge
        invoice_totals["vat_total"] += vat_on_shipping
        
        # Update VAT breakdown
        if VATCode.STANDARD not in invoice_totals["vat_breakdown"]:
            invoice_totals["vat_breakdown"][VATCode.STANDARD] = {
                "net": Decimal("0.00"),
                "vat": Decimal("0.00"),
                "rate": self.vat_calc.VAT_RATES[VATCode.STANDARD]
            }
        invoice_totals["vat_breakdown"][VATCode.STANDARD]["net"] += shipping_charge
        invoice_totals["vat_breakdown"][VATCode.STANDARD]["vat"] += vat_on_shipping
    
    def _check_credit_limit(self, customer: Customer, invoice_amount: Decimal):
        """Check if invoice would exceed credit limit"""
        if not self.config.force_credit_limit:
            return
        
        # Calculate new balance
        new_balance = customer.balance + invoice_amount
        
        if new_balance > customer.credit_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invoice would exceed credit limit. Current balance: {customer.balance}, "
                       f"Invoice amount: {invoice_amount}, Credit limit: {customer.credit_limit}"
            )
    
    def _update_stock_quantity(self, stock_id: int, quantity: Decimal):
        """Update stock quantities after invoicing"""
        stock = self.db.query(StockItem).filter_by(id=stock_id).with_for_update().first()
        if stock and stock.is_stocked:
            # Reduce on-hand quantity
            stock.quantity_on_hand -= quantity
            stock.ytd_issues += quantity
            stock.last_issue_date = datetime.now()
            
            # Check for negative stock
            if stock.quantity_on_hand < 0 and not stock.allow_negative_stock:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for {stock.stock_code}"
                )
    
    def _update_customer_balance(self, customer: Customer, invoice: SalesInvoice):
        """Update customer balance and turnover"""
        if invoice.invoice_type == "INVOICE":
            customer.balance += invoice.gross_total
            customer.turnover_ytd += invoice.gross_total
            
            # Update quarterly turnover
            quarter = (invoice.invoice_date.month - 1) // 3 + 1
            if quarter == 1:
                customer.turnover_q1 += invoice.gross_total
            elif quarter == 2:
                customer.turnover_q2 += invoice.gross_total
            elif quarter == 3:
                customer.turnover_q3 += invoice.gross_total
            else:
                customer.turnover_q4 += invoice.gross_total
                
        elif invoice.invoice_type == "CREDIT_NOTE":
            customer.balance -= invoice.gross_total
            customer.turnover_ytd -= invoice.gross_total
        
        customer.last_invoice_date = invoice.invoice_date
    
    def _create_back_orders(self, back_orders: List[Dict], customer: Customer, invoice: SalesInvoice):
        """Create back order records for out-of-stock items"""
        # This would create entries in a back_orders table
        # For now, we'll log them
        for bo in back_orders:
            print(f"Back order created: {bo['stock_code']} qty {bo['quantity']} for invoice {invoice.invoice_number}")
    
    def _prepare_gl_posting(self, invoice: SalesInvoice):
        """Prepare General Ledger posting entries"""
        # This would create GL journal entries
        # Simplified version - actual implementation would be more complex
        
        # Debit: Customer Control Account
        # Credit: Sales Account(s) by analysis code
        # Credit: VAT Account(s) by VAT code
        
        pass  # TODO: Implement GL posting logic