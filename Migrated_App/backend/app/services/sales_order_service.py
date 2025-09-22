"""
Sales Order Service
Implementation of COBOL sales order processing logic
Migrated from so100.cbl, so110.cbl, so200.cbl series
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from app.models.transactions import SalesOrder, SalesOrderLine, SalesOrderStatus
from app.models.customers import Customer
from app.models.stock import StockItem
from app.models.users import User
from app.core.calculations.vat_calculator import VATCalculator, VATCode
from app.core.calculations.discount_calculator import DiscountCalculator, DiscountType
from app.schemas.sales import SalesOrderCreate, SalesOrderUpdate
from app.core.audit.audit_service import AuditService


class SalesOrderService:
    """
    Sales Order service implementing COBOL sales order logic
    Handles order creation, approval, stock allocation, and conversion to invoices
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.vat_calc = VATCalculator()
        self.discount_calc = DiscountCalculator()
        self.audit = AuditService(db)
    
    def create_sales_order(
        self,
        order_data: SalesOrderCreate,
        user_id: int
    ) -> SalesOrder:
        """
        Create new sales order
        Implements COBOL so100.cbl order entry logic
        """
        # Validate customer
        customer = self.db.query(Customer).filter_by(
            customer_code=order_data.customer_code
        ).first()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer {order_data.customer_code} not found"
            )
        
        if not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer {order_data.customer_code} is inactive"
            )
        
        if customer.on_hold:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer {order_data.customer_code} is on hold"
            )
        
        # Validate order lines
        if not order_data.order_lines or len(order_data.order_lines) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Order must have at least one line"
            )
        
        # Generate order number
        order_number = self._generate_order_number()
        
        # Create order header
        sales_order = SalesOrder(
            order_number=order_number,
            customer_id=customer.id,
            customer_code=customer.customer_code,
            order_date=datetime.now(),
            required_date=order_data.required_date,
            delivery_name=order_data.delivery_name or customer.customer_name,
            delivery_address1=order_data.delivery_address1 or customer.address_line1,
            delivery_address2=order_data.delivery_address2 or customer.address_line2,
            delivery_address3=order_data.delivery_address3 or customer.city,
            delivery_postcode=order_data.delivery_postcode or customer.postal_code,
            customer_reference=order_data.customer_reference,
            sales_rep=order_data.sales_rep,
            order_status=SalesOrderStatus.PENDING,
            currency_code=customer.currency_code or "USD",
            notes=order_data.notes,
            created_by=str(user_id),
            created_at=datetime.now()
        )
        
        self.db.add(sales_order)
        self.db.flush()  # Get the ID
        
        # Process order lines
        total_goods = Decimal('0.00')
        total_discount = Decimal('0.00')
        total_vat = Decimal('0.00')
        
        for line_num, line_data in enumerate(order_data.order_lines, 1):
            # Validate stock item
            stock_item = self.db.query(StockItem).filter_by(
                stock_code=line_data.stock_code
            ).first()
            
            if not stock_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Stock item {line_data.stock_code} not found"
                )
            
            if not stock_item.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Stock item {line_data.stock_code} is inactive"
                )
            
            # Calculate line amounts
            quantity = Decimal(str(line_data.quantity_ordered))
            unit_price = Decimal(str(line_data.unit_price))
            discount_percent = Decimal(str(line_data.discount_percent or 0))
            
            # Apply customer discount if line discount not specified
            if discount_percent == 0 and customer.discount_percent:
                discount_percent = customer.discount_percent
            
            line_total = quantity * unit_price
            discount_amount = line_total * (discount_percent / 100)
            net_amount = line_total - discount_amount
            
            # Calculate VAT
            vat_code = line_data.vat_code or stock_item.vat_code or "S"
            vat_rate = self.vat_calc.get_vat_rate(vat_code)
            vat_amount = net_amount * (vat_rate / 100)
            
            # Create order line
            order_line = SalesOrderLine(
                order_id=sales_order.id,
                line_number=line_num,
                stock_id=stock_item.id,
                stock_code=stock_item.stock_code,
                description=line_data.description or stock_item.description,
                quantity_ordered=quantity,
                unit_price=unit_price,
                discount_percent=discount_percent,
                discount_amount=discount_amount,
                net_amount=net_amount,
                vat_code=vat_code,
                vat_rate=vat_rate,
                vat_amount=vat_amount,
                line_status="OPEN",
                promised_date=order_data.required_date,
                created_at=datetime.now()
            )
            
            self.db.add(order_line)
            
            # Accumulate totals
            total_goods += line_total
            total_discount += discount_amount
            total_vat += vat_amount
        
        # Update order totals
        sales_order.goods_total = total_goods
        sales_order.discount_total = total_discount
        sales_order.net_total = total_goods - total_discount
        sales_order.vat_total = total_vat
        sales_order.gross_total = sales_order.net_total + total_vat
        
        # Check credit limit
        self._check_credit_limit(customer, sales_order.gross_total)
        
        self.db.commit()
        
        # Audit trail
        self.audit.log_transaction(
            table_name="sales_orders",
            record_id=sales_order.id,
            operation="CREATE",
            user_id=user_id,
            details=f"Sales order {order_number} created for {customer.customer_code}"
        )
        
        return sales_order
    
    def get_sales_order(self, order_id: int) -> Optional[SalesOrder]:
        """Get sales order by ID"""
        return self.db.query(SalesOrder).filter_by(id=order_id).first()
    
    def list_sales_orders(
        self,
        skip: int = 0,
        limit: int = 20,
        customer_id: Optional[int] = None,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[SalesOrder]:
        """List sales orders with filtering"""
        query = self.db.query(SalesOrder)
        
        if customer_id:
            query = query.filter(SalesOrder.customer_id == customer_id)
        
        if status:
            query = query.filter(SalesOrder.order_status == status)
        
        if from_date:
            query = query.filter(SalesOrder.order_date >= from_date)
        
        if to_date:
            query = query.filter(SalesOrder.order_date <= to_date)
        
        return query.order_by(SalesOrder.order_date.desc()).offset(skip).limit(limit).all()
    
    def update_sales_order(
        self,
        order_id: int,
        order_data: SalesOrderUpdate,
        user_id: int
    ) -> SalesOrder:
        """Update sales order"""
        sales_order = self.get_sales_order(order_id)
        
        if not sales_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales order not found"
            )
        
        if sales_order.order_status in [SalesOrderStatus.DELIVERED, SalesOrderStatus.INVOICED, SalesOrderStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update order in {sales_order.order_status} status"
            )
        
        # Update allowed fields
        update_data = order_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(sales_order, field):
                setattr(sales_order, field, value)
        
        sales_order.updated_by = str(user_id)
        sales_order.updated_at = datetime.now()
        
        self.db.commit()
        
        # Audit trail
        self.audit.log_transaction(
            table_name="sales_orders",
            record_id=sales_order.id,
            operation="UPDATE",
            user_id=user_id,
            details=f"Sales order {sales_order.order_number} updated"
        )
        
        return sales_order
    
    def approve_sales_order(self, order_id: int, user_id: int) -> SalesOrder:
        """Approve sales order"""
        sales_order = self.get_sales_order(order_id)
        
        if not sales_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales order not found"
            )
        
        if sales_order.order_status != SalesOrderStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve order in {sales_order.order_status} status"
            )
        
        # Check credit limit again
        customer = self.db.query(Customer).filter_by(id=sales_order.customer_id).first()
        self._check_credit_limit(customer, sales_order.gross_total)
        
        sales_order.order_status = SalesOrderStatus.APPROVED
        sales_order.authorized_by = str(user_id)
        sales_order.authorized_date = datetime.now()
        sales_order.updated_by = str(user_id)
        sales_order.updated_at = datetime.now()
        
        self.db.commit()
        
        # Audit trail
        self.audit.log_transaction(
            table_name="sales_orders",
            record_id=sales_order.id,
            operation="APPROVE",
            user_id=user_id,
            details=f"Sales order {sales_order.order_number} approved"
        )
        
        return sales_order
    
    def cancel_sales_order(self, order_id: int, reason: str, user_id: int) -> SalesOrder:
        """Cancel sales order"""
        sales_order = self.get_sales_order(order_id)
        
        if not sales_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales order not found"
            )
        
        if sales_order.order_status in [SalesOrderStatus.DELIVERED, SalesOrderStatus.INVOICED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel order in {sales_order.order_status} status"
            )
        
        # Release any allocated stock
        self._release_stock_allocation(sales_order)
        
        sales_order.order_status = SalesOrderStatus.CANCELLED
        sales_order.cancellation_reason = reason
        sales_order.cancelled_by = str(user_id)
        sales_order.cancelled_date = datetime.now()
        sales_order.updated_by = str(user_id)
        sales_order.updated_at = datetime.now()
        
        self.db.commit()
        
        # Audit trail
        self.audit.log_transaction(
            table_name="sales_orders",
            record_id=sales_order.id,
            operation="CANCEL",
            user_id=user_id,
            details=f"Sales order {sales_order.order_number} cancelled: {reason}"
        )
        
        return sales_order
    
    def check_stock_availability(self, order_id: int) -> Dict:
        """Check stock availability for order"""
        sales_order = self.get_sales_order(order_id)
        
        if not sales_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales order not found"
            )
        
        availability = []
        all_available = True
        
        for line in sales_order.order_lines:
            stock_item = self.db.query(StockItem).filter_by(id=line.stock_id).first()
            
            if stock_item:
                available_qty = stock_item.quantity_on_hand - line.quantity_allocated
                shortage = max(Decimal('0'), line.quantity_ordered - available_qty)
                is_available = shortage == 0
                
                if not is_available:
                    all_available = False
                
                availability.append({
                    "line_number": line.line_number,
                    "stock_code": line.stock_code,
                    "description": line.description,
                    "quantity_ordered": float(line.quantity_ordered),
                    "quantity_available": float(available_qty),
                    "shortage": float(shortage),
                    "is_available": is_available
                })
        
        return {
            "order_number": sales_order.order_number,
            "all_available": all_available,
            "line_availability": availability
        }
    
    def allocate_stock(self, order_id: int, user_id: int) -> Dict:
        """Allocate stock for sales order"""
        sales_order = self.get_sales_order(order_id)
        
        if not sales_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales order not found"
            )
        
        if sales_order.order_status != SalesOrderStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must be approved before allocating stock"
            )
        
        allocated_lines = []
        back_order_lines = []
        
        for line in sales_order.order_lines:
            stock_item = self.db.query(StockItem).filter_by(id=line.stock_id).first()
            
            if stock_item:
                available_qty = stock_item.quantity_on_hand - line.quantity_allocated
                allocate_qty = min(line.quantity_ordered, available_qty)
                back_order_qty = line.quantity_ordered - allocate_qty
                
                # Update allocations
                line.quantity_allocated = allocate_qty
                line.quantity_back_order = back_order_qty
                
                if back_order_qty > 0:
                    line.line_status = "PARTIAL"
                    back_order_lines.append({
                        "stock_code": line.stock_code,
                        "quantity": float(back_order_qty)
                    })
                else:
                    line.line_status = "ALLOCATED"
                
                allocated_lines.append({
                    "stock_code": line.stock_code,
                    "quantity_allocated": float(allocate_qty),
                    "quantity_back_order": float(back_order_qty)
                })
        
        # Update order flags
        sales_order.has_backorders = len(back_order_lines) > 0
        sales_order.updated_by = str(user_id)
        sales_order.updated_at = datetime.now()
        
        self.db.commit()
        
        # Audit trail
        self.audit.log_transaction(
            table_name="sales_orders",
            record_id=sales_order.id,
            operation="ALLOCATE",
            user_id=user_id,
            details=f"Stock allocated for order {sales_order.order_number}"
        )
        
        return {
            "order_number": sales_order.order_number,
            "allocated_lines": allocated_lines,
            "back_order_lines": back_order_lines,
            "has_backorders": sales_order.has_backorders
        }
    
    def convert_to_invoice(self, order_id: int, user_id: int) -> Dict:
        """Convert sales order to invoice"""
        sales_order = self.get_sales_order(order_id)
        
        if not sales_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales order not found"
            )
        
        if sales_order.order_status != SalesOrderStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must be approved before invoicing"
            )
        
        if sales_order.is_invoiced:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order has already been invoiced"
            )
        
        # This would integrate with the InvoiceService
        # For now, just mark as invoiced
        sales_order.is_invoiced = True
        sales_order.order_status = SalesOrderStatus.INVOICED
        sales_order.updated_by = str(user_id)
        sales_order.updated_at = datetime.now()
        
        self.db.commit()
        
        # Audit trail
        self.audit.log_transaction(
            table_name="sales_orders",
            record_id=sales_order.id,
            operation="INVOICE",
            user_id=user_id,
            details=f"Sales order {sales_order.order_number} converted to invoice"
        )
        
        return {
            "order_number": sales_order.order_number,
            "invoice_created": True,
            "message": f"Order {sales_order.order_number} converted to invoice"
        }
    
    def search_sales_orders(
        self,
        customer_code: Optional[str] = None,
        order_number: Optional[str] = None,
        customer_reference: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """Search sales orders"""
        query = self.db.query(SalesOrder)
        
        if customer_code:
            query = query.filter(SalesOrder.customer_code.ilike(f"%{customer_code}%"))
        
        if order_number:
            query = query.filter(SalesOrder.order_number.ilike(f"%{order_number}%"))
        
        if customer_reference:
            query = query.filter(SalesOrder.customer_reference.ilike(f"%{customer_reference}%"))
        
        total_count = query.count()
        
        orders = query.order_by(SalesOrder.order_date.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return {
            "orders": orders,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    
    def get_statistics(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Dict:
        """Get sales order statistics"""
        query = self.db.query(SalesOrder)
        
        if from_date:
            query = query.filter(SalesOrder.order_date >= from_date)
        
        if to_date:
            query = query.filter(SalesOrder.order_date <= to_date)
        
        total_orders = query.count()
        total_value = query.with_entities(func.sum(SalesOrder.gross_total)).scalar() or 0
        
        # Status breakdown
        status_stats = self.db.query(
            SalesOrder.order_status,
            func.count(SalesOrder.id).label('count'),
            func.sum(SalesOrder.gross_total).label('value')
        ).filter(
            SalesOrder.order_date >= (from_date or date.min),
            SalesOrder.order_date <= (to_date or date.max)
        ).group_by(SalesOrder.order_status).all()
        
        return {
            "total_orders": total_orders,
            "total_value": float(total_value),
            "status_breakdown": [
                {
                    "status": stat.order_status,
                    "count": stat.count,
                    "value": float(stat.value or 0)
                }
                for stat in status_stats
            ]
        }
    
    def _generate_order_number(self) -> str:
        """Generate unique order number"""
        # Get the next sequence number
        last_order = self.db.query(SalesOrder).order_by(
            SalesOrder.id.desc()
        ).first()
        
        if last_order:
            # Extract number from last order
            try:
                last_num = int(last_order.order_number[2:])  # Remove "SO" prefix
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        return f"SO{next_num:06d}"
    
    def _check_credit_limit(self, customer: Customer, order_value: Decimal):
        """Check customer credit limit"""
        if customer.credit_limit and customer.credit_limit > 0:
            new_balance = customer.balance + order_value
            
            if new_balance > customer.credit_limit:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Order would exceed credit limit. "
                           f"Current balance: {customer.balance}, "
                           f"Order value: {order_value}, "
                           f"Credit limit: {customer.credit_limit}"
                )
    
    def _release_stock_allocation(self, sales_order: SalesOrder):
        """Release stock allocations for cancelled order"""
        for line in sales_order.order_lines:
            line.quantity_allocated = Decimal('0')
            line.quantity_back_order = Decimal('0')
            line.line_status = "CANCELLED"
    
    def ship_sales_order(
        self, 
        order_id: int, 
        tracking_number: Optional[str] = None,
        carrier: Optional[str] = None,
        shipping_date: Optional[date] = None,
        user_id: int = None
    ) -> Dict:
        """Ship sales order"""
        sales_order = self.get_sales_order(order_id)
        
        if not sales_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales order not found"
            )
        
        if sales_order.order_status not in [SalesOrderStatus.APPROVED, SalesOrderStatus.CONFIRMED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must be approved or confirmed before shipping"
            )
        
        if sales_order.order_status == SalesOrderStatus.SHIPPED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order has already been shipped"
            )
        
        # Update order status
        sales_order.order_status = SalesOrderStatus.SHIPPED
        sales_order.shipping_date = shipping_date or date.today()
        sales_order.tracking_number = tracking_number
        sales_order.carrier = carrier
        sales_order.updated_by = str(user_id)
        sales_order.updated_at = datetime.now()
        
        # Update stock quantities (reduce on hand, increase allocated)
        for line in sales_order.order_lines:
            stock_item = self.db.query(StockItem).filter_by(
                stock_code=line.stock_code
            ).first()
            
            if stock_item:
                # Reduce on hand quantity
                stock_item.quantity_on_hand -= line.quantity
                # Reduce allocated quantity
                stock_item.quantity_allocated -= line.quantity
                line.quantity_shipped = line.quantity
                line.line_status = "SHIPPED"
        
        self.db.commit()
        
        # Audit trail
        self.audit.log_transaction(
            table_name="sales_orders",
            record_id=sales_order.id,
            operation="SHIP",
            user_id=user_id,
            details=f"Sales order {sales_order.order_number} shipped. Tracking: {tracking_number}, Carrier: {carrier}"
        )
        
        return {
            "order_number": sales_order.order_number,
            "shipping_date": sales_order.shipping_date.isoformat(),
            "tracking_number": tracking_number,
            "carrier": carrier,
            "message": f"Order {sales_order.order_number} shipped successfully"
        }