"""
Purchase Order Service
Migrated from COBOL pl800.cbl, pl810.cbl, pl900.cbl
Handles purchase order creation, modification, and processing
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status

from app.models.purchase_transactions import (
    PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus
)
from app.models.suppliers import Supplier
from app.models.stock import StockItem
from app.models.control_tables import NumberSequence, BackOrder
from app.models.system import AuditTrail, CompanyPeriod
from app.core.calculations.vat_calculator import VATCalculator
from app.core.calculations.discount_calculator import DiscountCalculator
from app.services.base import BaseService


class PurchaseOrderService(BaseService):
    """Purchase Order processing service"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.vat_calculator = VATCalculator()
        self.discount_calculator = DiscountCalculator()
    
    def create_purchase_order(
        self,
        supplier_code: str,
        order_lines: List[Dict],
        delivery_date: Optional[date] = None,
        buyer_code: Optional[str] = None,
        notes: Optional[str] = None,
        user_id: int = None
    ) -> PurchaseOrder:
        """
        Create new purchase order
        Migrated from pl800.cbl CREATE-NEW-ORDER
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
            
            if not supplier.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Supplier {supplier_code} is inactive"
                )
            
            # Get next order number
            order_number = self._get_next_order_number()
            
            # Create order header
            order = PurchaseOrder(
                order_number=order_number,
                order_date=datetime.now(),
                supplier_id=supplier.id,
                buyer_code=buyer_code,
                expected_date=delivery_date,
                currency_code=supplier.currency_code or "USD",
                exchange_rate=Decimal("1.0"),
                order_status=PurchaseOrderStatus.DRAFT,
                notes=notes,
                created_by=str(user_id) if user_id else None
            )
            
            # Process order lines
            line_number = 0
            goods_total = Decimal("0.00")
            discount_total = Decimal("0.00")
            vat_total = Decimal("0.00")
            
            for line_data in order_lines:
                line_number += 10
                
                # Validate stock item
                stock_item = None
                if line_data.get("stock_code"):
                    stock_item = self.db.query(StockItem).filter(
                        StockItem.stock_code == line_data["stock_code"]
                    ).first()
                    if not stock_item:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Stock item {line_data['stock_code']} not found"
                        )
                
                # Calculate line amounts
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
                    discount_amount = Decimal("0.00")
                
                net_amount = line_total - discount_amount
                
                # Calculate VAT
                vat_code = line_data.get("vat_code", "S")
                vat_amount, _, vat_rate = self.vat_calculator.calculate_vat(
                    net_amount, vat_code, datetime.now().date()
                )
                
                # Create order line
                order_line = PurchaseOrderLine(
                    order_id=order.id,
                    line_number=line_number,
                    stock_id=stock_item.id if stock_item else None,
                    stock_code=stock_item.stock_code if stock_item else line_data.get("stock_code"),
                    description=line_data["description"],
                    quantity_ordered=quantity,
                    quantity_outstanding=quantity,
                    unit_price=unit_price,
                    discount_percent=discount_percent,
                    discount_amount=discount_amount,
                    net_amount=net_amount,
                    vat_code=vat_code,
                    vat_rate=vat_rate,
                    vat_amount=vat_amount,
                    expected_date=delivery_date,
                    gl_account=line_data.get("gl_account"),
                    analysis_code1=line_data.get("analysis_code1"),
                    line_status="OPEN"
                )
                
                order.order_lines.append(order_line)
                
                # Update totals
                goods_total += line_total
                discount_total += discount_amount
                vat_total += vat_amount
            
            # Update order totals
            order.goods_total = goods_total
            order.discount_total = discount_total
            order.net_total = goods_total - discount_total
            order.vat_total = vat_total
            order.gross_total = order.net_total + vat_total
            
            # Save order
            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="purchase_orders",
                record_id=str(order.id),
                operation="CREATE",
                user_id=user_id,
                details=f"Created PO {order_number}"
            )
            
            return order
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating purchase order: {str(e)}"
            )
    
    def update_purchase_order(
        self,
        order_id: int,
        updates: Dict,
        user_id: int = None
    ) -> PurchaseOrder:
        """
        Update purchase order
        Migrated from pl810.cbl UPDATE-ORDER
        """
        try:
            # Get order
            order = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.id == order_id
            ).first()
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Purchase order not found"
                )
            
            # Check if order can be modified
            if order.order_status in [PurchaseOrderStatus.COMPLETE, PurchaseOrderStatus.CANCELLED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot modify {order.order_status.value} order"
                )
            
            # Track changes for audit
            changes = {}
            
            # Update header fields
            updatable_fields = [
                "supplier_reference", "buyer_code", "department",
                "delivery_address1", "delivery_address2", "delivery_address3",
                "delivery_postcode", "expected_date", "notes"
            ]
            
            for field in updatable_fields:
                if field in updates and getattr(order, field) != updates[field]:
                    changes[field] = {
                        "old": getattr(order, field),
                        "new": updates[field]
                    }
                    setattr(order, field, updates[field])
            
            # Update status if provided
            if "status" in updates:
                new_status = PurchaseOrderStatus(updates["status"])
                if self._validate_status_change(order.order_status, new_status):
                    changes["status"] = {
                        "old": order.order_status.value,
                        "new": new_status.value
                    }
                    order.order_status = new_status
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid status change from {order.order_status.value} to {new_status.value}"
                    )
            
            order.updated_at = datetime.now()
            order.updated_by = str(user_id) if user_id else None
            
            self.db.commit()
            self.db.refresh(order)
            
            # Create audit trail
            if changes:
                self._create_audit_trail(
                    table_name="purchase_orders",
                    record_id=str(order.id),
                    operation="UPDATE",
                    user_id=user_id,
                    details=f"Updated PO {order.order_number}",
                    changes=changes
                )
            
            return order
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating purchase order: {str(e)}"
            )
    
    def approve_purchase_order(
        self,
        order_id: int,
        approver_id: int
    ) -> PurchaseOrder:
        """
        Approve purchase order
        Migrated from pl900.cbl APPROVE-ORDER
        """
        try:
            # Get order
            order = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.id == order_id
            ).first()
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Purchase order not found"
                )
            
            # Check current status
            if order.order_status != PurchaseOrderStatus.SUBMITTED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot approve {order.order_status.value} order"
                )
            
            # Check approval limit (would check user's approval limit here)
            # For now, assume all users can approve
            
            # Update order
            order.order_status = PurchaseOrderStatus.APPROVED
            order.approved_by = str(approver_id)
            order.approved_date = datetime.now()
            order.updated_at = datetime.now()
            order.updated_by = str(approver_id)
            
            self.db.commit()
            self.db.refresh(order)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="purchase_orders",
                record_id=str(order.id),
                operation="APPROVE",
                user_id=approver_id,
                details=f"Approved PO {order.order_number}"
            )
            
            return order
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error approving purchase order: {str(e)}"
            )
    
    def cancel_purchase_order(
        self,
        order_id: int,
        reason: str,
        user_id: int
    ) -> PurchaseOrder:
        """
        Cancel purchase order
        Migrated from pl900.cbl CANCEL-ORDER
        """
        try:
            # Get order
            order = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.id == order_id
            ).first()
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Purchase order not found"
                )
            
            # Check if order can be cancelled
            if order.order_status == PurchaseOrderStatus.COMPLETE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot cancel completed order"
                )
            
            if order.has_receipts:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot cancel order with goods receipts"
                )
            
            # Update order
            order.order_status = PurchaseOrderStatus.CANCELLED
            order.notes = f"{order.notes}\nCANCELLED: {reason}" if order.notes else f"CANCELLED: {reason}"
            order.updated_at = datetime.now()
            order.updated_by = str(user_id)
            
            # Update all open lines
            for line in order.order_lines:
                if line.line_status == "OPEN":
                    line.line_status = "CANCELLED"
                    line.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(order)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="purchase_orders",
                record_id=str(order.id),
                operation="CANCEL",
                user_id=user_id,
                details=f"Cancelled PO {order.order_number}: {reason}"
            )
            
            return order
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error cancelling purchase order: {str(e)}"
            )
    
    def get_purchase_orders(
        self,
        supplier_code: Optional[str] = None,
        status: Optional[PurchaseOrderStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        buyer_code: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """
        Get purchase orders with filtering and pagination
        Migrated from pl900.cbl LIST-ORDERS
        """
        try:
            query = self.db.query(PurchaseOrder)
            
            # Apply filters
            if supplier_code:
                query = query.join(Supplier).filter(
                    Supplier.supplier_code == supplier_code
                )
            
            if status:
                query = query.filter(PurchaseOrder.order_status == status)
            
            if from_date:
                query = query.filter(PurchaseOrder.order_date >= from_date)
            
            if to_date:
                query = query.filter(PurchaseOrder.order_date <= to_date)
            
            if buyer_code:
                query = query.filter(PurchaseOrder.buyer_code == buyer_code)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            orders = query.order_by(desc(PurchaseOrder.order_date))\
                         .offset((page - 1) * page_size)\
                         .limit(page_size)\
                         .all()
            
            return {
                "orders": orders,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving purchase orders: {str(e)}"
            )
    
    def check_order_completion(self, order_id: int) -> bool:
        """
        Check if order is complete based on receipts
        Migrated from pl900.cbl CHECK-ORDER-COMPLETE
        """
        try:
            order = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.id == order_id
            ).first()
            if not order:
                return False
            
            # Check all lines
            for line in order.order_lines:
                if line.quantity_outstanding > 0 and line.line_status != "CANCELLED":
                    return False
            
            # Update order status if complete
            if order.order_status != PurchaseOrderStatus.COMPLETE:
                order.order_status = PurchaseOrderStatus.COMPLETE
                order.is_complete = True
                order.updated_at = datetime.now()
                self.db.commit()
            
            return True
            
        except Exception:
            return False
    
    def _get_next_order_number(self) -> str:
        """Generate next purchase order number"""
        sequence = self.db.query(NumberSequence).filter(
            NumberSequence.sequence_type == "PURCHASE_ORDER"
        ).with_for_update().first()
        
        if not sequence:
            # Create sequence if not exists
            sequence = NumberSequence(
                sequence_type="PURCHASE_ORDER",
                prefix="PO",
                current_number=1,
                min_digits=6
            )
            self.db.add(sequence)
        
        sequence.current_number += 1
        number_str = str(sequence.current_number).zfill(sequence.min_digits)
        order_number = f"{sequence.prefix}{number_str}"
        
        self.db.commit()
        return order_number
    
    def _validate_status_change(
        self,
        current_status: PurchaseOrderStatus,
        new_status: PurchaseOrderStatus
    ) -> bool:
        """Validate if status change is allowed"""
        allowed_transitions = {
            PurchaseOrderStatus.DRAFT: [PurchaseOrderStatus.SUBMITTED, PurchaseOrderStatus.CANCELLED],
            PurchaseOrderStatus.SUBMITTED: [PurchaseOrderStatus.APPROVED, PurchaseOrderStatus.CANCELLED],
            PurchaseOrderStatus.APPROVED: [PurchaseOrderStatus.PARTIAL, PurchaseOrderStatus.COMPLETE, PurchaseOrderStatus.CANCELLED],
            PurchaseOrderStatus.PARTIAL: [PurchaseOrderStatus.COMPLETE, PurchaseOrderStatus.CANCELLED],
            PurchaseOrderStatus.COMPLETE: [],
            PurchaseOrderStatus.CANCELLED: []
        }
        
        return new_status in allowed_transitions.get(current_status, [])