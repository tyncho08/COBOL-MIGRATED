"""
Customer Service
Implementation of customer management business logic from COBOL
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from fastapi import HTTPException, status
from datetime import datetime
import re

from app.models import Customer, CustomerContact, CustomerCreditHistory
from app.schemas.sales import CustomerCreate, CustomerUpdate, CustomerResponse
from app.core.audit.audit_service import AuditService


class CustomerService:
    """
    Customer management service implementing COBOL business logic
    Handles customer creation, updates, credit control, and validation
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)
    
    def generate_customer_code(self, customer_name: str) -> str:
        """
        Generate customer code with check digit (COBOL logic)
        Format: 6 characters + 1 check digit = 7 total
        """
        # Extract initials or first characters
        name_parts = customer_name.upper().split()
        base = ""
        
        # Use first 3 letters of each word up to 2 words
        for i, part in enumerate(name_parts[:2]):
            clean_part = re.sub(r'[^A-Z0-9]', '', part)
            if i == 0:
                base += clean_part[:3].ljust(3, '0')
            else:
                base += clean_part[:3].ljust(3, '0')
        
        # Ensure we have 6 characters
        base = base[:6].ljust(6, '0')
        
        # Calculate check digit using modulo 11 (COBOL method)
        weights = [7, 6, 5, 4, 3, 2]
        total = sum(int(base[i] if base[i].isdigit() else ord(base[i]) - ord('A') + 10) * weights[i] 
                   for i in range(6))
        
        remainder = total % 11
        check_digit = 'X' if remainder == 10 else str(remainder)
        
        return base + check_digit
    
    def validate_customer_code(self, customer_code: str) -> bool:
        """
        Validate customer code check digit
        """
        if len(customer_code) != 7:
            return False
        
        base = customer_code[:6]
        check = customer_code[6]
        
        # Recalculate check digit
        weights = [7, 6, 5, 4, 3, 2]
        total = sum(int(base[i] if base[i].isdigit() else ord(base[i]) - ord('A') + 10) * weights[i] 
                   for i in range(6))
        
        remainder = total % 11
        expected_check = 'X' if remainder == 10 else str(remainder)
        
        return check == expected_check
    
    def list_customers(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        on_hold: Optional[bool] = None,
        analysis_code1: Optional[str] = None
    ) -> List[Customer]:
        """
        List customers with filtering
        Implements COBOL sl020.cbl customer listing logic
        """
        query = self.db.query(Customer)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    Customer.customer_code.ilike(f"%{search}%"),
                    Customer.customer_name.ilike(f"%{search}%"),
                    Customer.postcode.ilike(f"%{search}%"),
                    Customer.phone_number.ilike(f"%{search}%")
                )
            )
        
        if is_active is not None:
            query = query.filter(Customer.is_active == is_active)
        
        if on_hold is not None:
            query = query.filter(Customer.on_hold == on_hold)
        
        if analysis_code1:
            query = query.filter(Customer.analysis_code1 == analysis_code1)
        
        # Order by customer code
        query = query.order_by(Customer.customer_code)
        
        # Pagination
        customers = query.offset(skip).limit(limit).all()
        
        return customers
    
    def get_customer(self, customer_id: int) -> Customer:
        """Get customer by ID"""
        customer = self.db.query(Customer).filter_by(id=customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        return customer
    
    def get_customer_by_code(self, customer_code: str) -> Customer:
        """Get customer by customer code"""
        customer = self.db.query(Customer).filter_by(customer_code=customer_code).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with code {customer_code} not found"
            )
        return customer
    
    def create_customer(self, customer_data: CustomerCreate, user_id: int) -> Customer:
        """
        Create new customer
        Implements COBOL sl010.cbl customer creation logic
        """
        # Validate customer code or generate if not provided
        if customer_data.customer_code:
            if not self.validate_customer_code(customer_data.customer_code):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid customer code - check digit validation failed"
                )
            
            # Check if code already exists
            existing = self.db.query(Customer).filter_by(
                customer_code=customer_data.customer_code
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Customer code {customer_data.customer_code} already exists"
                )
        else:
            # Generate customer code
            customer_data.customer_code = self.generate_customer_code(customer_data.customer_name)
            
            # Ensure unique
            counter = 1
            while self.db.query(Customer).filter_by(customer_code=customer_data.customer_code).first():
                base = customer_data.customer_code[:5] + str(counter)
                # Recalculate check digit
                weights = [7, 6, 5, 4, 3, 2]
                total = sum(int(base[i] if base[i].isdigit() else ord(base[i]) - ord('A') + 10) * weights[i] 
                           for i in range(6))
                remainder = total % 11
                check_digit = 'X' if remainder == 10 else str(remainder)
                customer_data.customer_code = base + check_digit
                counter += 1
        
        # Validate VAT number if provided
        if customer_data.vat_registration:
            # Basic VAT validation - could be enhanced
            customer_data.vat_registration = customer_data.vat_registration.upper().replace(' ', '')
        
        # Create customer record
        customer = Customer(
            **customer_data.dict(),
            created_by=str(user_id),
            updated_by=str(user_id)
        )
        
        self.db.add(customer)
        
        # Create audit trail
        self.audit.create_audit_entry(
            table_name="customers",
            record_id=customer.customer_code,
            operation="INSERT",
            user_id=user_id,
            after_data=customer_data.dict()
        )
        
        # Create initial credit history entry if credit limit > 0
        if customer.credit_limit > 0:
            credit_history = CustomerCreditHistory(
                customer_id=customer.id,
                change_date=datetime.now(),
                old_limit=0,
                new_limit=customer.credit_limit,
                old_rating="A",
                new_rating=customer.credit_rating,
                reason="Initial credit limit",
                approved_by=str(user_id),
                created_by=str(user_id)
            )
            self.db.add(credit_history)
        
        self.db.commit()
        self.db.refresh(customer)
        
        return customer
    
    def update_customer(
        self,
        customer_id: int,
        customer_data: CustomerUpdate,
        user_id: int
    ) -> Customer:
        """
        Update customer information
        Implements COBOL sl010.cbl customer maintenance logic
        """
        customer = self.get_customer(customer_id)
        
        # Capture before state for audit
        before_data = {
            "customer_name": customer.customer_name,
            "credit_limit": str(customer.credit_limit),
            "on_hold": customer.on_hold,
            "is_active": customer.is_active
        }
        
        # Track credit limit changes
        old_credit_limit = customer.credit_limit
        old_credit_rating = customer.credit_rating
        
        # Update fields
        update_data = customer_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)
        
        customer.updated_by = str(user_id)
        customer.updated_at = datetime.now()
        
        # Handle credit limit change
        if customer_data.credit_limit is not None and customer_data.credit_limit != old_credit_limit:
            # Create credit history entry
            credit_history = CustomerCreditHistory(
                customer_id=customer.id,
                change_date=datetime.now(),
                old_limit=old_credit_limit,
                new_limit=customer_data.credit_limit,
                old_rating=old_credit_rating,
                new_rating=customer.credit_rating,
                reason="Credit limit update",
                approved_by=str(user_id),
                created_by=str(user_id)
            )
            self.db.add(credit_history)
        
        # Create audit trail
        self.audit.create_audit_entry(
            table_name="customers",
            record_id=customer.customer_code,
            operation="UPDATE",
            user_id=user_id,
            before_data=before_data,
            after_data=update_data
        )
        
        self.db.commit()
        self.db.refresh(customer)
        
        return customer
    
    def check_credit_status(self, customer: Customer, new_order_amount: float) -> dict:
        """
        Check customer credit status
        Implements COBOL credit control logic
        """
        # Calculate available credit
        available_credit = customer.credit_limit - customer.balance
        
        # Check if new order would exceed limit
        would_exceed = (customer.balance + new_order_amount) > customer.credit_limit
        
        # Calculate days overdue
        overdue_days = 0
        if customer.last_invoice_date and customer.balance > 0:
            days_since_invoice = (datetime.now() - customer.last_invoice_date).days
            if days_since_invoice > customer.payment_terms:
                overdue_days = days_since_invoice - customer.payment_terms
        
        # Determine credit status
        status = "OK"
        messages = []
        
        if customer.on_hold:
            status = "HOLD"
            messages.append("Customer account is on hold")
        
        if customer.cash_only:
            status = "CASH_ONLY"
            messages.append("Customer is cash only")
        
        if would_exceed:
            status = "EXCEED_LIMIT"
            messages.append(f"Order would exceed credit limit by {new_order_amount - available_credit:.2f}")
        
        if overdue_days > 0:
            if overdue_days > 60:
                status = "SERIOUSLY_OVERDUE"
                messages.append(f"Account is {overdue_days} days overdue")
            elif overdue_days > 30:
                status = "OVERDUE"
                messages.append(f"Account is {overdue_days} days overdue")
        
        return {
            "status": status,
            "credit_limit": customer.credit_limit,
            "current_balance": customer.balance,
            "available_credit": available_credit,
            "would_exceed": would_exceed,
            "overdue_days": overdue_days,
            "messages": messages
        }
    
    def update_customer_balance(
        self,
        customer_id: int,
        amount: float,
        transaction_type: str,
        user_id: int
    ):
        """
        Update customer balance
        transaction_type: INVOICE, CREDIT_NOTE, PAYMENT
        """
        customer = self.get_customer(customer_id)
        
        if transaction_type == "INVOICE":
            customer.balance += amount
            customer.turnover_ytd += amount
            customer.last_invoice_date = datetime.now()
        elif transaction_type == "CREDIT_NOTE":
            customer.balance -= amount
            customer.turnover_ytd -= amount
        elif transaction_type == "PAYMENT":
            customer.balance -= amount
            customer.last_payment_date = datetime.now()
        
        customer.updated_by = str(user_id)
        customer.updated_at = datetime.now()
        
        self.db.commit()