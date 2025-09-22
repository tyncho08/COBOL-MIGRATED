"""
Sales Report Service
Implementation of sales reporting from COBOL sl900, sl940, sl960, sl970
"""
from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models import (
    Customer, SalesInvoice, SalesInvoiceLine,
    CustomerPayment, PaymentAllocation
)
from app.schemas.sales import (
    CustomerStatementRequest, AgedDebtorsRequest, SalesAnalysisRequest
)


class SalesReportService:
    """
    Sales reporting service implementing COBOL report logic
    Generates statements, aged debtors, sales analysis, and VAT reports
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_customer_statement(
        self,
        request: CustomerStatementRequest
    ) -> Dict:
        """
        Generate customer statement
        Implements COBOL sl900.cbl statement generation
        """
        # Get customer
        customer = self.db.query(Customer).filter_by(id=request.customer_id).first()
        if not customer:
            return {"error": "Customer not found"}
        
        # Build query for transactions
        query = self.db.query(SalesInvoice).filter(
            SalesInvoice.customer_id == request.customer_id
        )
        
        # Date filtering
        if request.from_date:
            query = query.filter(SalesInvoice.invoice_date >= request.from_date)
        if request.to_date:
            query = query.filter(SalesInvoice.invoice_date <= request.to_date)
        
        # Include paid filter
        if not request.include_paid:
            query = query.filter(SalesInvoice.is_paid == False)
        
        # Get invoices
        invoices = query.order_by(SalesInvoice.invoice_date).all()
        
        # Get payments in the same period
        payment_query = self.db.query(CustomerPayment).filter(
            CustomerPayment.customer_id == request.customer_id
        )
        
        if request.from_date:
            payment_query = payment_query.filter(CustomerPayment.payment_date >= request.from_date)
        if request.to_date:
            payment_query = payment_query.filter(CustomerPayment.payment_date <= request.to_date)
        
        payments = payment_query.order_by(CustomerPayment.payment_date).all()
        
        # Build statement lines
        statement_lines = []
        running_balance = Decimal("0.00")
        
        # Opening balance (if from_date specified)
        if request.from_date:
            opening_balance = self._calculate_opening_balance(
                request.customer_id, request.from_date
            )
            running_balance = opening_balance
            statement_lines.append({
                "date": request.from_date,
                "type": "BALANCE",
                "reference": "Opening Balance",
                "debit": opening_balance if opening_balance > 0 else None,
                "credit": abs(opening_balance) if opening_balance < 0 else None,
                "balance": running_balance
            })
        
        # Process transactions chronologically
        transactions = []
        
        # Add invoices
        for invoice in invoices:
            transactions.append({
                "date": invoice.invoice_date,
                "type": "INVOICE" if invoice.invoice_type == "INVOICE" else "CREDIT",
                "reference": invoice.invoice_number,
                "amount": invoice.gross_total if invoice.invoice_type == "INVOICE" else -invoice.gross_total,
                "description": f"Invoice {invoice.invoice_number}"
            })
        
        # Add payments
        for payment in payments:
            transactions.append({
                "date": payment.payment_date,
                "type": "PAYMENT",
                "reference": payment.payment_number,
                "amount": -payment.payment_amount,
                "description": f"Payment {payment.reference or ''}"
            })
        
        # Sort by date
        transactions.sort(key=lambda x: x["date"])
        
        # Build statement lines
        for trans in transactions:
            running_balance += trans["amount"]
            statement_lines.append({
                "date": trans["date"],
                "type": trans["type"],
                "reference": trans["reference"],
                "description": trans["description"],
                "debit": trans["amount"] if trans["amount"] > 0 else None,
                "credit": abs(trans["amount"]) if trans["amount"] < 0 else None,
                "balance": running_balance
            })
        
        return {
            "customer": {
                "customer_code": customer.customer_code,
                "customer_name": customer.customer_name,
                "address": [
                    customer.address_line1,
                    customer.address_line2,
                    customer.address_line3,
                    customer.postcode
                ]
            },
            "statement_date": date.today(),
            "from_date": request.from_date,
            "to_date": request.to_date,
            "opening_balance": opening_balance if request.from_date else Decimal("0.00"),
            "closing_balance": running_balance,
            "statement_lines": statement_lines,
            "current_balance": customer.balance,
            "credit_limit": customer.credit_limit
        }
    
    def generate_aged_debtors(
        self,
        request: AgedDebtorsRequest
    ) -> Dict:
        """
        Generate aged debtors report
        Implements COBOL sl940.cbl aged analysis
        """
        as_of_date = request.as_of_date or date.today()
        
        # Get all customers with outstanding balances
        query = self.db.query(Customer)
        
        if not request.include_zero_balance:
            query = query.filter(Customer.balance != 0)
        
        if request.analysis_code:
            query = query.filter(Customer.analysis_code1 == request.analysis_code)
        
        customers = query.all()
        
        # Aging buckets
        aging_periods = request.aging_periods or [30, 60, 90, 120]
        buckets = {f"current": Decimal("0.00")}
        for period in aging_periods:
            buckets[f"over_{period}"] = Decimal("0.00")
        buckets["older"] = Decimal("0.00")
        
        # Customer details
        customer_aging = []
        total_outstanding = Decimal("0.00")
        
        for customer in customers:
            if customer.balance <= 0 and not request.include_zero_balance:
                continue
            
            # Get unpaid invoices
            invoices = self.db.query(SalesInvoice).filter(
                and_(
                    SalesInvoice.customer_id == customer.id,
                    SalesInvoice.is_paid == False,
                    SalesInvoice.invoice_date <= as_of_date
                )
            ).all()
            
            customer_buckets = {f"current": Decimal("0.00")}
            for period in aging_periods:
                customer_buckets[f"over_{period}"] = Decimal("0.00")
            customer_buckets["older"] = Decimal("0.00")
            
            for invoice in invoices:
                days_old = (as_of_date - invoice.invoice_date.date()).days
                
                # Allocate to appropriate bucket
                allocated = False
                if days_old <= 0:
                    customer_buckets["current"] += invoice.balance
                    buckets["current"] += invoice.balance
                else:
                    for i, period in enumerate(aging_periods):
                        if days_old <= period:
                            if i == 0:
                                customer_buckets[f"over_{period}"] += invoice.balance
                                buckets[f"over_{period}"] += invoice.balance
                            else:
                                prev_period = aging_periods[i-1]
                                if days_old > prev_period:
                                    customer_buckets[f"over_{period}"] += invoice.balance
                                    buckets[f"over_{period}"] += invoice.balance
                            allocated = True
                            break
                    
                    if not allocated:
                        customer_buckets["older"] += invoice.balance
                        buckets["older"] += invoice.balance
            
            if customer.balance > 0 or request.include_zero_balance:
                customer_aging.append({
                    "customer_code": customer.customer_code,
                    "customer_name": customer.customer_name,
                    "credit_limit": customer.credit_limit,
                    "total_balance": customer.balance,
                    "aging": customer_buckets,
                    "on_hold": customer.on_hold,
                    "payment_terms": customer.payment_terms
                })
                total_outstanding += customer.balance
        
        return {
            "report_date": date.today(),
            "as_of_date": as_of_date,
            "total_outstanding": total_outstanding,
            "aging_summary": buckets,
            "customer_count": len(customer_aging),
            "customers": customer_aging
        }
    
    def generate_sales_analysis(
        self,
        request: SalesAnalysisRequest
    ) -> Dict:
        """
        Generate sales analysis report
        Implements COBOL sl960.cbl sales analysis
        """
        # Base query for invoices in period
        query = self.db.query(
            SalesInvoice, SalesInvoiceLine
        ).join(
            SalesInvoiceLine,
            SalesInvoice.id == SalesInvoiceLine.invoice_id
        ).filter(
            and_(
                SalesInvoice.invoice_date >= request.from_date,
                SalesInvoice.invoice_date <= request.to_date,
                SalesInvoice.invoice_type == "INVOICE"  # Exclude credit notes
            )
        )
        
        results = query.all()
        
        # Group data based on request
        analysis_data = {}
        
        for invoice, line in results:
            # Determine grouping key
            if request.group_by == "customer":
                key = invoice.customer_code
                name = invoice.customer_name
            elif request.group_by == "product":
                key = line.stock_code or "MISC"
                name = line.description
            elif request.group_by == "analysis1":
                key = line.analysis_code1 or "NONE"
                name = f"Analysis Code 1: {key}"
            elif request.group_by == "analysis2":
                key = line.analysis_code2 or "NONE"
                name = f"Analysis Code 2: {key}"
            else:
                key = line.analysis_code3 or "NONE"
                name = f"Analysis Code 3: {key}"
            
            if key not in analysis_data:
                analysis_data[key] = {
                    "code": key,
                    "name": name,
                    "quantity": Decimal("0.00"),
                    "net_sales": Decimal("0.00"),
                    "vat_amount": Decimal("0.00"),
                    "gross_sales": Decimal("0.00"),
                    "transaction_count": 0,
                    "line_count": 0
                }
            
            analysis_data[key]["quantity"] += line.quantity
            analysis_data[key]["net_sales"] += line.net_amount
            analysis_data[key]["vat_amount"] += line.vat_amount
            analysis_data[key]["gross_sales"] += (line.net_amount + line.vat_amount)
            analysis_data[key]["line_count"] += 1
        
        # Calculate totals
        total_net = sum(item["net_sales"] for item in analysis_data.values())
        total_vat = sum(item["vat_amount"] for item in analysis_data.values())
        total_gross = sum(item["gross_sales"] for item in analysis_data.values())
        
        # Sort by gross sales descending
        sorted_data = sorted(
            analysis_data.values(),
            key=lambda x: x["gross_sales"],
            reverse=True
        )
        
        return {
            "report_date": date.today(),
            "from_date": request.from_date,
            "to_date": request.to_date,
            "group_by": request.group_by,
            "summary": {
                "total_net_sales": total_net,
                "total_vat": total_vat,
                "total_gross_sales": total_gross,
                "item_count": len(analysis_data)
            },
            "details": sorted_data[:50] if not request.include_details else sorted_data
        }
    
    def generate_vat_report(
        self,
        from_date: date,
        to_date: date
    ) -> Dict:
        """
        Generate VAT report
        Implements COBOL sl970.cbl VAT reporting
        """
        # Get all invoices in period
        invoices = self.db.query(SalesInvoice).filter(
            and_(
                SalesInvoice.invoice_date >= from_date,
                SalesInvoice.invoice_date <= to_date,
                SalesInvoice.gl_posted == True  # Only posted invoices
            )
        ).all()
        
        # VAT summary by code
        vat_summary = {
            "S": {"net": Decimal("0.00"), "vat": Decimal("0.00"), "count": 0},
            "R": {"net": Decimal("0.00"), "vat": Decimal("0.00"), "count": 0},
            "Z": {"net": Decimal("0.00"), "vat": Decimal("0.00"), "count": 0},
            "E": {"net": Decimal("0.00"), "vat": Decimal("0.00"), "count": 0},
        }
        
        # Process invoices
        for invoice in invoices:
            # Get invoice lines
            lines = self.db.query(SalesInvoiceLine).filter_by(
                invoice_id=invoice.id
            ).all()
            
            for line in lines:
                vat_code = line.vat_code
                if vat_code in vat_summary:
                    if invoice.invoice_type == "INVOICE":
                        vat_summary[vat_code]["net"] += line.net_amount
                        vat_summary[vat_code]["vat"] += line.vat_amount
                    else:  # Credit note
                        vat_summary[vat_code]["net"] -= line.net_amount
                        vat_summary[vat_code]["vat"] -= line.vat_amount
                    vat_summary[vat_code]["count"] += 1
        
        # Calculate totals
        total_net = sum(item["net"] for item in vat_summary.values())
        total_vat = sum(item["vat"] for item in vat_summary.values())
        
        return {
            "report_date": date.today(),
            "from_date": from_date,
            "to_date": to_date,
            "vat_summary": vat_summary,
            "totals": {
                "total_net": total_net,
                "total_vat": total_vat,
                "total_gross": total_net + total_vat
            },
            "invoice_count": len(invoices)
        }
    
    def _calculate_opening_balance(
        self,
        customer_id: int,
        as_of_date: date
    ) -> Decimal:
        """Calculate customer balance as of specific date"""
        # Sum invoices before date
        invoice_total = self.db.query(
            func.coalesce(func.sum(SalesInvoice.gross_total), 0)
        ).filter(
            and_(
                SalesInvoice.customer_id == customer_id,
                SalesInvoice.invoice_date < as_of_date,
                SalesInvoice.invoice_type == "INVOICE"
            )
        ).scalar()
        
        # Subtract credit notes
        credit_total = self.db.query(
            func.coalesce(func.sum(SalesInvoice.gross_total), 0)
        ).filter(
            and_(
                SalesInvoice.customer_id == customer_id,
                SalesInvoice.invoice_date < as_of_date,
                SalesInvoice.invoice_type == "CREDIT_NOTE"
            )
        ).scalar()
        
        # Subtract payments
        payment_total = self.db.query(
            func.coalesce(func.sum(CustomerPayment.payment_amount), 0)
        ).filter(
            and_(
                CustomerPayment.customer_id == customer_id,
                CustomerPayment.payment_date < as_of_date,
                CustomerPayment.is_reversed == False
            )
        ).scalar()
        
        return Decimal(str(invoice_total)) - Decimal(str(credit_total)) - Decimal(str(payment_total))