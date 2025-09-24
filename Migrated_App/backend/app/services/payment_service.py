"""
Payment Service
Implementation of payment processing from COBOL sl100, sl110
"""
from decimal import Decimal
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import (
    Customer, CustomerPayment, PaymentAllocation,
    SalesInvoice, SystemConfig
)
from app.schemas.sales import PaymentCreate, PaymentAllocationCreate
from app.core.audit.audit_service import AuditService
from app.core.calculations.discount_calculator import DiscountCalculator


class PaymentService:
    """
    Payment processing service implementing COBOL payment logic
    Handles cash receipts, allocations, and settlement discounts
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)
        self.discount_calc = DiscountCalculator()
        self._load_system_config()
    
    def _load_system_config(self):
        """Load system configuration"""
        self.config = self.db.query(SystemConfig).first()
        if not self.config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="System configuration not found"
            )
    
    def _get_next_payment_number(self) -> str:
        """Get next payment number and increment counter"""
        config = self.db.query(SystemConfig).with_for_update().first()
        payment_number = f"PAY{str(config.next_payment_number).zfill(7)}"
        config.next_payment_number += 1
        return payment_number
    
    def create_payment(
        self,
        payment_data: PaymentCreate,
        user_id: int
    ) -> CustomerPayment:
        """
        Create customer payment/receipt
        Implements COBOL sl100.cbl cash receipt logic
        """
        # Validate customer
        customer = self.db.query(Customer).filter_by(id=payment_data.customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Get payment number
        payment_number = self._get_next_payment_number()
        
        # Create payment record
        payment = CustomerPayment(
            payment_number=payment_number,
            payment_date=payment_data.payment_date or datetime.now(),
            customer_id=customer.id,
            customer_code=customer.customer_code,
            payment_method=payment_data.payment_method,
            payment_amount=payment_data.payment_amount,
            allocated_amount=Decimal("0.00"),
            unallocated_amount=payment_data.payment_amount,
            reference=payment_data.reference,
            bank_reference=payment_data.bank_reference,
            currency_code=customer.currency_code,
            notes=payment_data.notes,
            created_by=str(user_id),
            updated_by=str(user_id)
        )
        
        self.db.add(payment)
        
        # Create audit trail
        self.audit.create_audit_entry(
            table_name="customer_payments",
            record_id=payment_number,
            operation="INSERT",
            user_id=user_id,
            after_data={
                "payment_number": payment_number,
                "customer_code": customer.customer_code,
                "payment_amount": str(payment_data.payment_amount),
                "payment_method": payment_data.payment_method
            }
        )
        
        self.db.commit()
        self.db.refresh(payment)
        
        return payment
    
    def allocate_payment(
        self,
        payment_id: int,
        allocations: List[PaymentAllocationCreate],
        user_id: int
    ) -> Dict:
        """
        Allocate payment to invoices
        Implements COBOL sl110.cbl payment allocation logic
        """
        # Get payment with lock
        payment = self.db.query(CustomerPayment).filter_by(
            id=payment_id
        ).with_for_update().first()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        if payment.is_reversed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot allocate reversed payment"
            )
        
        # Track allocation results
        allocation_results = []
        total_allocated = Decimal("0.00")
        total_discount = Decimal("0.00")
        
        for alloc_data in allocations:
            # Get invoice with lock
            invoice = self.db.query(SalesInvoice).filter_by(
                id=alloc_data.invoice_id
            ).with_for_update().first()
            
            if not invoice:
                allocation_results.append({
                    "invoice_id": alloc_data.invoice_id,
                    "status": "NOT_FOUND",
                    "message": "Invoice not found"
                })
                continue
            
            # Validate customer matches
            if invoice.customer_id != payment.customer_id:
                allocation_results.append({
                    "invoice_id": alloc_data.invoice_id,
                    "status": "WRONG_CUSTOMER",
                    "message": "Invoice belongs to different customer"
                })
                continue
            
            # Check if already fully paid
            if invoice.is_paid:
                allocation_results.append({
                    "invoice_id": alloc_data.invoice_id,
                    "status": "ALREADY_PAID",
                    "message": "Invoice is already fully paid"
                })
                continue
            
            # Calculate settlement discount if applicable
            discount_taken = Decimal("0.00")
            if alloc_data.discount_taken and alloc_data.discount_taken > 0:
                # Validate settlement discount eligibility
                days_to_payment = (payment.payment_date - invoice.invoice_date).days
                if days_to_payment <= invoice.settlement_days:
                    # Calculate maximum allowed discount
                    max_discount = (invoice.balance * invoice.settlement_discount / Decimal("100")).quantize(
                        Decimal("0.01")
                    )
                    discount_taken = min(alloc_data.discount_taken, max_discount)
                else:
                    allocation_results.append({
                        "invoice_id": alloc_data.invoice_id,
                        "status": "DISCOUNT_NOT_ALLOWED",
                        "message": f"Settlement discount period expired ({invoice.settlement_days} days)"
                    })
                    discount_taken = Decimal("0.00")
            
            # Calculate allocation amount
            allocation_amount = min(
                alloc_data.allocated_amount,
                invoice.balance - discount_taken,
                payment.unallocated_amount
            )
            
            if allocation_amount <= 0:
                allocation_results.append({
                    "invoice_id": alloc_data.invoice_id,
                    "status": "NO_AMOUNT",
                    "message": "No amount to allocate"
                })
                continue
            
            # Create allocation record
            allocation = PaymentAllocation(
                payment_id=payment.id,
                invoice_id=invoice.id,
                allocation_date=datetime.now(),
                allocated_amount=allocation_amount,
                discount_taken=discount_taken,
                created_by=str(user_id)
            )
            self.db.add(allocation)
            
            # Update invoice
            invoice.amount_paid += allocation_amount + discount_taken
            invoice.balance = invoice.gross_total - invoice.amount_paid
            invoice.is_paid = invoice.balance <= Decimal("0.01")  # Allow small rounding differences
            
            # Update payment
            total_allocated += allocation_amount
            total_discount += discount_taken
            
            allocation_results.append({
                "invoice_id": alloc_data.invoice_id,
                "invoice_number": invoice.invoice_number,
                "status": "SUCCESS",
                "allocated_amount": allocation_amount,
                "discount_taken": discount_taken,
                "remaining_balance": invoice.balance
            })
        
        # Update payment totals
        payment.allocated_amount += total_allocated
        payment.unallocated_amount = payment.payment_amount - payment.allocated_amount
        payment.is_allocated = payment.unallocated_amount <= Decimal("0.01")
        
        # Update customer balance
        customer = self.db.query(Customer).filter_by(id=payment.customer_id).first()
        customer.balance -= (total_allocated + total_discount)
        customer.last_payment_date = payment.payment_date
        
        # Create audit trail
        self.audit.create_audit_entry(
            table_name="payment_allocations",
            record_id=payment.payment_number,
            operation="UPDATE",
            user_id=user_id,
            after_data={
                "total_allocated": str(total_allocated),
                "total_discount": str(total_discount),
                "allocations": len(allocation_results)
            }
        )
        
        self.db.commit()
        
        return {
            "payment_id": payment.id,
            "payment_number": payment.payment_number,
            "total_allocated": total_allocated,
            "total_discount": total_discount,
            "unallocated_amount": payment.unallocated_amount,
            "allocations": allocation_results
        }
    
    def reverse_payment(
        self,
        payment_id: int,
        reason: str,
        user_id: int
    ) -> Dict:
        """
        Reverse a payment and its allocations
        """
        payment = self.db.query(CustomerPayment).filter_by(
            id=payment_id
        ).with_for_update().first()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        if payment.is_reversed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment is already reversed"
            )
        
        # Reverse all allocations
        allocations = self.db.query(PaymentAllocation).filter_by(
            payment_id=payment.id
        ).all()
        
        for allocation in allocations:
            # Update invoice
            invoice = self.db.query(SalesInvoice).filter_by(
                id=allocation.invoice_id
            ).with_for_update().first()
            
            invoice.amount_paid -= (allocation.allocated_amount + allocation.discount_taken)
            invoice.balance = invoice.gross_total - invoice.amount_paid
            invoice.is_paid = False
        
        # Update customer balance
        customer = self.db.query(Customer).filter_by(id=payment.customer_id).first()
        customer.balance += payment.payment_amount
        
        # Mark payment as reversed
        payment.is_reversed = True
        payment.notes = f"REVERSED: {reason} (by user {user_id} on {datetime.now()})"
        
        # Create audit trail
        self.audit.create_audit_entry(
            table_name="customer_payments",
            record_id=payment.payment_number,
            operation="REVERSE",
            user_id=user_id,
            before_data={"is_reversed": False},
            after_data={"is_reversed": True, "reason": reason}
        )
        
        self.db.commit()
        
        return {
            "payment_id": payment.id,
            "payment_number": payment.payment_number,
            "status": "REVERSED",
            "reason": reason
        }
    
    def list_payments(
        self,
        skip: int = 0,
        limit: int = 20,
        customer_id: Optional[int] = None,
        payment_method: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        is_allocated: Optional[bool] = None
    ) -> List[CustomerPayment]:
        """List customer payments with filtering and pagination"""
        query = self.db.query(CustomerPayment)
        
        # Apply filters
        if customer_id:
            query = query.filter(CustomerPayment.customer_id == customer_id)
        
        if payment_method:
            query = query.filter(CustomerPayment.payment_method == payment_method)
        
        if from_date:
            query = query.filter(CustomerPayment.payment_date >= from_date)
        
        if to_date:
            query = query.filter(CustomerPayment.payment_date <= to_date)
        
        if is_allocated is not None:
            query = query.filter(CustomerPayment.is_allocated == is_allocated)
        
        # Apply pagination and return results
        return query.order_by(CustomerPayment.payment_date.desc())\
                    .offset(skip)\
                    .limit(limit)\
                    .all()
    
    def get_payment(self, payment_id: int) -> Optional[CustomerPayment]:
        """Get payment by ID"""
        return self.db.query(CustomerPayment).filter(CustomerPayment.id == payment_id).first()
    
    def update_payment(self, payment_id: int, payment_data, user_id: int) -> CustomerPayment:
        """Update payment"""
        payment = self.get_payment(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # Update payment fields
        for field, value in payment_data.dict(exclude_unset=True).items():
            setattr(payment, field, value)
        
        payment.updated_by = str(user_id)
        payment.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(payment)
        
        return payment
    
    def remove_allocation(self, payment_id: int, allocation_id: int, user_id: int) -> Dict[str, Any]:
        """Remove payment allocation"""
        allocation = self.db.query(PaymentAllocation).filter(
            PaymentAllocation.id == allocation_id,
            PaymentAllocation.payment_id == payment_id
        ).first()
        
        if not allocation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Allocation not found"
            )
        
        # Update invoice
        invoice = self.db.query(SalesInvoice).filter_by(id=allocation.invoice_id).first()
        if invoice:
            invoice.amount_paid -= (allocation.allocated_amount + allocation.discount_taken)
            invoice.balance = invoice.gross_total - invoice.amount_paid
            invoice.is_paid = False
        
        # Update payment
        payment = self.db.query(CustomerPayment).filter_by(id=payment_id).first()
        if payment:
            payment.allocated_amount -= allocation.allocated_amount
            payment.unallocated_amount = payment.payment_amount - payment.allocated_amount
            payment.is_allocated = False
        
        # Delete allocation
        self.db.delete(allocation)
        self.db.commit()
        
        return {"message": "Allocation removed successfully", "allocation_id": allocation_id}
    
    def get_allocations(self, payment_id: int) -> List[PaymentAllocation]:
        """Get payment allocations"""
        return self.db.query(PaymentAllocation).filter(
            PaymentAllocation.payment_id == payment_id
        ).all()
    
    def search_payments(
        self,
        customer_code: Optional[str] = None,
        payment_number: Optional[str] = None,
        reference: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Search customer payments"""
        query = self.db.query(CustomerPayment)
        
        if customer_code:
            query = query.filter(CustomerPayment.customer_code.ilike(f"%{customer_code}%"))
        
        if payment_number:
            query = query.filter(CustomerPayment.payment_number.ilike(f"%{payment_number}%"))
        
        if reference:
            query = query.filter(CustomerPayment.reference.ilike(f"%{reference}%"))
        
        total_count = query.count()
        
        payments = query.order_by(CustomerPayment.payment_date.desc())\
                        .offset((page - 1) * page_size)\
                        .limit(page_size)\
                        .all()
        
        return {
            "payments": payments,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    
    def get_statistics(
        self, 
        from_date: Optional[date], 
        to_date: Optional[date], 
        customer_id: Optional[int],
        payment_method: Optional[str]
    ) -> Dict[str, Any]:
        """Get payment statistics"""
        query = self.db.query(CustomerPayment)
        
        if from_date:
            query = query.filter(CustomerPayment.payment_date >= from_date)
        
        if to_date:
            query = query.filter(CustomerPayment.payment_date <= to_date)
        
        if customer_id:
            query = query.filter(CustomerPayment.customer_id == customer_id)
        
        if payment_method:
            query = query.filter(CustomerPayment.payment_method == payment_method)
        
        from sqlalchemy import func
        
        stats = query.with_entities(
            func.count(CustomerPayment.id).label('total_payments'),
            func.sum(CustomerPayment.payment_amount).label('total_amount'),
            func.sum(CustomerPayment.allocated_amount).label('allocated_amount'),
            func.sum(CustomerPayment.unallocated_amount).label('unallocated_amount')
        ).first()
        
        return {
            "total_payments": stats.total_payments or 0,
            "total_amount": float(stats.total_amount or 0),
            "allocated_amount": float(stats.allocated_amount or 0),
            "unallocated_amount": float(stats.unallocated_amount or 0),
            "average_payment_value": float(stats.total_amount or 0) / max(stats.total_payments or 1, 1)
        }
    
    def get_unallocated_payments(self, customer_id: Optional[int] = None) -> List[CustomerPayment]:
        """Get unallocated payments"""
        query = self.db.query(CustomerPayment).filter(
            CustomerPayment.is_allocated == False,
            CustomerPayment.unallocated_amount > 0
        )
        
        if customer_id:
            query = query.filter(CustomerPayment.customer_id == customer_id)
        
        return query.order_by(CustomerPayment.payment_date).all()
    
    def auto_allocate_payments(self, customer_id: Optional[int], user_id: int) -> Dict[str, Any]:
        """Auto-allocate payments to oldest invoices"""
        # Get unallocated payments
        payments = self.get_unallocated_payments(customer_id)
        
        results = {
            "payments_processed": 0,
            "invoices_paid": 0,
            "total_allocated": Decimal("0.00")
        }
        
        for payment in payments:
            # Get unpaid invoices for customer
            invoices = self.db.query(SalesInvoice).filter(
                SalesInvoice.customer_id == payment.customer_id,
                SalesInvoice.is_paid == False,
                SalesInvoice.balance > 0
            ).order_by(SalesInvoice.invoice_date).all()
            
            allocations = []
            remaining = payment.unallocated_amount
            
            for invoice in invoices:
                if remaining <= 0:
                    break
                
                allocation_amount = min(remaining, invoice.balance)
                allocations.append(PaymentAllocationCreate(
                    invoice_id=invoice.id,
                    allocated_amount=allocation_amount,
                    discount_taken=Decimal("0.00")
                ))
                
                remaining -= allocation_amount
            
            if allocations:
                result = self.allocate_payment(payment.id, allocations, user_id)
                results["payments_processed"] += 1
                results["invoices_paid"] += len(result["allocations"])
                results["total_allocated"] += result["total_allocated"]
        
        return results
    
    def get_cash_receipts_journal(self, from_date: date, to_date: date) -> Dict[str, Any]:
        """Get cash receipts journal report"""
        payments = self.db.query(CustomerPayment).filter(
            CustomerPayment.payment_date >= from_date,
            CustomerPayment.payment_date <= to_date,
            CustomerPayment.is_reversed == False
        ).order_by(CustomerPayment.payment_date, CustomerPayment.payment_number).all()
        
        journal_entries = []
        total_amount = Decimal("0.00")
        
        for payment in payments:
            # Get customer details
            customer = self.db.query(Customer).filter_by(id=payment.customer_id).first()
            
            journal_entries.append({
                "payment_date": payment.payment_date.isoformat(),
                "payment_number": payment.payment_number,
                "customer_code": payment.customer_code,
                "customer_name": customer.customer_name if customer else "",
                "payment_method": payment.payment_method,
                "reference": payment.reference,
                "payment_amount": float(payment.payment_amount),
                "allocated_amount": float(payment.allocated_amount),
                "unallocated_amount": float(payment.unallocated_amount)
            })
            
            total_amount += payment.payment_amount
        
        return {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "journal_entries": journal_entries,
            "total_count": len(journal_entries),
            "total_amount": float(total_amount)
        }