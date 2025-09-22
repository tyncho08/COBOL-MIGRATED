"""
Stock Movement Service
Migrated from COBOL st100.cbl, st110.cbl, st120.cbl
Handles all stock movements and inventory tracking
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status
import enum

from app.models.stock import StockItem, StockMovement, StockValuation
from app.models.control_tables import NumberSequence
from app.models.system import AuditTrail, CompanyPeriod
from app.config.settings import settings
from app.services.base import BaseService


class MovementType(str, enum.Enum):
    """Stock movement types"""
    GOODS_RECEIPT = "GOODS_RECEIPT"
    SALES_ISSUE = "SALES_ISSUE"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"
    STOCK_TAKE = "STOCK_TAKE"
    RETURN_TO_SUPPLIER = "RETURN_TO_SUPPLIER"
    CUSTOMER_RETURN = "CUSTOMER_RETURN"
    WRITE_OFF = "WRITE_OFF"
    PRODUCTION_IN = "PRODUCTION_IN"
    PRODUCTION_OUT = "PRODUCTION_OUT"


class StockMovementService(BaseService):
    """Stock movement processing service"""
    
    def create_stock_movement(
        self,
        stock_id: int,
        movement_type: str,
        quantity: Decimal,
        reference_type: Optional[str] = None,
        reference_number: Optional[str] = None,
        location_code: Optional[str] = None,
        batch_number: Optional[str] = None,
        cost_price: Optional[Decimal] = None,
        sell_price: Optional[Decimal] = None,
        reason_code: Optional[str] = None,
        notes: Optional[str] = None,
        user_id: int = None
    ) -> StockMovement:
        """
        Create stock movement
        Migrated from st100.cbl CREATE-MOVEMENT
        """
        try:
            # Validate stock item
            stock_item = self.db.query(StockItem).filter(
                StockItem.id == stock_id
            ).with_for_update().first()
            if not stock_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stock item not found"
                )
            
            # Validate movement type
            if movement_type not in [mt.value for mt in MovementType]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid movement type: {movement_type}"
                )
            
            # Determine if inward or outward movement
            is_inward = movement_type in [
                MovementType.GOODS_RECEIPT,
                MovementType.CUSTOMER_RETURN,
                MovementType.PRODUCTION_IN,
                MovementType.ADJUSTMENT  # Can be both
            ]
            
            # For adjustments, quantity determines direction
            if movement_type == MovementType.ADJUSTMENT:
                is_inward = quantity > 0
                quantity = abs(quantity)
            
            # Calculate new quantity
            if is_inward:
                new_quantity = stock_item.quantity_on_hand + quantity
            else:
                new_quantity = stock_item.quantity_on_hand - quantity
                
                # Check if sufficient stock
                if not settings.ALLOW_NEGATIVE_STOCK and new_quantity < 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient stock. Available: {stock_item.quantity_on_hand}, Required: {quantity}"
                    )
            
            # Get movement number
            movement_number = self._get_next_movement_number()
            
            # Determine cost price
            if not cost_price:
                if is_inward:
                    cost_price = stock_item.unit_cost or Decimal("0")
                else:
                    cost_price = self._calculate_cost_price(stock_item, quantity)
            
            # Create movement
            movement = StockMovement(
                movement_number=movement_number,
                movement_date=datetime.now(),
                stock_id=stock_id,
                movement_type=movement_type,
                quantity=quantity,
                is_inward=is_inward,
                location_code=location_code or stock_item.location,
                batch_number=batch_number,
                reference_type=reference_type,
                reference_number=reference_number,
                quantity_before=stock_item.quantity_on_hand,
                quantity_after=new_quantity,
                cost_price=cost_price,
                sell_price=sell_price,
                total_cost=quantity * cost_price,
                reason_code=reason_code,
                notes=notes,
                created_by=str(user_id) if user_id else None
            )
            
            self.db.add(movement)
            
            # Update stock item
            stock_item.quantity_on_hand = new_quantity
            
            # Update stock value if inward movement
            if is_inward and cost_price > 0:
                self._update_stock_value(stock_item, quantity, cost_price)
            
            # Update last movement date
            stock_item.last_movement_date = datetime.now()
            if movement_type == MovementType.SALES_ISSUE:
                stock_item.last_sale_date = datetime.now()
            elif movement_type == MovementType.GOODS_RECEIPT:
                stock_item.last_purchase_date = datetime.now()
            
            # Check reorder level
            if stock_item.reorder_point and new_quantity <= stock_item.reorder_point:
                self._create_reorder_alert(stock_item)
            
            self.db.commit()
            self.db.refresh(movement)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="stock_movements",
                record_id=str(movement.id),
                operation="CREATE",
                user_id=user_id,
                details=f"Stock movement {movement_number}: {movement_type} {quantity} units"
            )
            
            return movement
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating stock movement: {str(e)}"
            )
    
    def transfer_stock(
        self,
        stock_id: int,
        from_location: str,
        to_location: str,
        quantity: Decimal,
        reason: Optional[str] = None,
        user_id: int = None
    ) -> Tuple[StockMovement, StockMovement]:
        """
        Transfer stock between locations
        Migrated from st110.cbl TRANSFER-STOCK
        """
        try:
            # Create outward movement from source location
            out_movement = self.create_stock_movement(
                stock_id=stock_id,
                movement_type=MovementType.TRANSFER,
                quantity=-quantity,  # Negative for outward
                location_code=from_location,
                reference_type="TRANSFER",
                reason_code="TRANSFER_OUT",
                notes=f"Transfer to {to_location}: {reason}" if reason else f"Transfer to {to_location}",
                user_id=user_id
            )
            
            # Create inward movement to destination location
            in_movement = self.create_stock_movement(
                stock_id=stock_id,
                movement_type=MovementType.TRANSFER,
                quantity=quantity,  # Positive for inward
                location_code=to_location,
                reference_type="TRANSFER",
                reference_number=out_movement.movement_number,
                reason_code="TRANSFER_IN",
                notes=f"Transfer from {from_location}: {reason}" if reason else f"Transfer from {from_location}",
                cost_price=out_movement.cost_price,
                user_id=user_id
            )
            
            # Link the movements
            out_movement.reference_number = in_movement.movement_number
            self.db.commit()
            
            return out_movement, in_movement
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error transferring stock: {str(e)}"
            )
    
    def adjust_stock(
        self,
        stock_id: int,
        adjustment_quantity: Decimal,
        reason_code: str,
        notes: str,
        user_id: int
    ) -> StockMovement:
        """
        Adjust stock quantity
        Migrated from st120.cbl ADJUST-STOCK
        """
        try:
            # Validate reason code
            valid_reasons = [
                "DAMAGED", "LOST", "FOUND", "CORRECTION", 
                "STOCK_TAKE", "WRITE_OFF", "OTHER"
            ]
            if reason_code not in valid_reasons:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid reason code: {reason_code}"
                )
            
            # Create adjustment movement
            movement = self.create_stock_movement(
                stock_id=stock_id,
                movement_type=MovementType.ADJUSTMENT,
                quantity=adjustment_quantity,
                reference_type="ADJUSTMENT",
                reason_code=reason_code,
                notes=notes,
                user_id=user_id
            )
            
            # Create audit trail for adjustment
            self._create_audit_trail(
                table_name="stock_adjustments",
                record_id=str(movement.id),
                operation="ADJUST",
                user_id=user_id,
                details=f"Stock adjustment: {adjustment_quantity} units, Reason: {reason_code}"
            )
            
            return movement
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error adjusting stock: {str(e)}"
            )
    
    def get_stock_movements(
        self,
        stock_id: Optional[int] = None,
        movement_type: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        location_code: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """
        Get stock movements with filtering
        Migrated from st120.cbl LIST-MOVEMENTS
        """
        try:
            query = self.db.query(StockMovement)
            
            # Apply filters
            if stock_id:
                query = query.filter(StockMovement.stock_id == stock_id)
            
            if movement_type:
                query = query.filter(StockMovement.movement_type == movement_type)
            
            if from_date:
                query = query.filter(StockMovement.movement_date >= from_date)
            
            if to_date:
                query = query.filter(StockMovement.movement_date <= to_date)
            
            if location_code:
                query = query.filter(StockMovement.location_code == location_code)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            movements = query.order_by(desc(StockMovement.movement_date))\
                           .offset((page - 1) * page_size)\
                           .limit(page_size)\
                           .all()
            
            return {
                "movements": movements,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving movements: {str(e)}"
            )
    
    def get_stock_history(
        self,
        stock_id: int,
        days: int = 365
    ) -> Dict:
        """
        Get stock movement history and statistics
        Migrated from st120.cbl STOCK-HISTORY
        """
        try:
            from_date = datetime.now() - timedelta(days=days)
            
            # Get movements
            movements = self.db.query(StockMovement).filter(
                and_(
                    StockMovement.stock_id == stock_id,
                    StockMovement.movement_date >= from_date
                )
            ).order_by(StockMovement.movement_date).all()
            
            # Calculate statistics
            total_in = sum(m.quantity for m in movements if m.is_inward)
            total_out = sum(m.quantity for m in movements if not m.is_inward)
            
            # Group by type
            movements_by_type = {}
            for movement in movements:
                if movement.movement_type not in movements_by_type:
                    movements_by_type[movement.movement_type] = {
                        "count": 0,
                        "quantity_in": Decimal("0"),
                        "quantity_out": Decimal("0"),
                        "value_in": Decimal("0"),
                        "value_out": Decimal("0")
                    }
                
                type_stats = movements_by_type[movement.movement_type]
                type_stats["count"] += 1
                
                if movement.is_inward:
                    type_stats["quantity_in"] += movement.quantity
                    type_stats["value_in"] += movement.total_cost or Decimal("0")
                else:
                    type_stats["quantity_out"] += movement.quantity
                    type_stats["value_out"] += movement.total_cost or Decimal("0")
            
            return {
                "movements": movements,
                "statistics": {
                    "total_movements": len(movements),
                    "total_quantity_in": total_in,
                    "total_quantity_out": total_out,
                    "net_movement": total_in - total_out,
                    "by_type": movements_by_type
                }
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving history: {str(e)}"
            )
    
    def _get_next_movement_number(self) -> str:
        """Generate next movement number"""
        sequence = self.db.query(NumberSequence).filter(
            NumberSequence.sequence_type == "STOCK_MOVEMENT"
        ).with_for_update().first()
        
        if not sequence:
            sequence = NumberSequence(
                sequence_type="STOCK_MOVEMENT",
                prefix="SM",
                current_number=1,
                min_digits=8
            )
            self.db.add(sequence)
        
        sequence.current_number += 1
        number_str = str(sequence.current_number).zfill(sequence.min_digits)
        movement_number = f"{sequence.prefix}{number_str}"
        
        self.db.commit()
        return movement_number
    
    def _calculate_cost_price(
        self,
        stock_item: StockItem,
        quantity: Decimal
    ) -> Decimal:
        """Calculate cost price based on valuation method"""
        valuation_method = stock_item.valuation_method or settings.STOCK_VALUATION_METHOD
        
        if valuation_method == "AVERAGE":
            return stock_item.unit_cost or Decimal("0")
        
        elif valuation_method == "FIFO":
            # Get oldest stock valuations
            valuations = self.db.query(StockValuation).filter(
                and_(
                    StockValuation.stock_id == stock_item.id,
                    StockValuation.quantity_remaining > 0
                )
            ).order_by(StockValuation.receipt_date).all()
            
            total_cost = Decimal("0")
            remaining_qty = quantity
            
            for val in valuations:
                if remaining_qty <= 0:
                    break
                
                qty_from_batch = min(val.quantity_remaining, remaining_qty)
                total_cost += qty_from_batch * val.cost_price
                remaining_qty -= qty_from_batch
            
            if quantity > 0:
                return (total_cost / quantity).quantize(Decimal("0.0001"))
            
        elif valuation_method == "LIFO":
            # Get newest stock valuations
            valuations = self.db.query(StockValuation).filter(
                and_(
                    StockValuation.stock_id == stock_item.id,
                    StockValuation.quantity_remaining > 0
                )
            ).order_by(desc(StockValuation.receipt_date)).all()
            
            total_cost = Decimal("0")
            remaining_qty = quantity
            
            for val in valuations:
                if remaining_qty <= 0:
                    break
                
                qty_from_batch = min(val.quantity_remaining, remaining_qty)
                total_cost += qty_from_batch * val.cost_price
                remaining_qty -= qty_from_batch
            
            if quantity > 0:
                return (total_cost / quantity).quantize(Decimal("0.0001"))
        
        # Default to current unit cost
        return stock_item.unit_cost or Decimal("0")
    
    def _update_stock_value(
        self,
        stock_item: StockItem,
        quantity: Decimal,
        cost_price: Decimal
    ):
        """Update stock value based on valuation method"""
        valuation_method = stock_item.valuation_method or settings.STOCK_VALUATION_METHOD
        
        if valuation_method == "AVERAGE":
            # Calculate new average cost
            current_value = stock_item.quantity_on_hand * (stock_item.unit_cost or Decimal("0"))
            new_value = quantity * cost_price
            total_quantity = stock_item.quantity_on_hand + quantity
            
            if total_quantity > 0:
                stock_item.unit_cost = (
                    (current_value + new_value) / total_quantity
                ).quantize(Decimal("0.0001"))
        
        elif valuation_method in ["FIFO", "LIFO"]:
            # Create new valuation record
            valuation = StockValuation(
                stock_id=stock_item.id,
                receipt_date=datetime.now(),
                quantity_received=quantity,
                quantity_remaining=quantity,
                cost_price=cost_price,
                total_cost=quantity * cost_price
            )
            self.db.add(valuation)
    
    def _create_reorder_alert(self, stock_item: StockItem):
        """Create reorder alert when stock falls below reorder point"""
        # In a real system, this would create an alert/notification
        # For now, we'll just log it in audit trail
        self._create_audit_trail(
            table_name="stock_alerts",
            record_id=str(stock_item.id),
            operation="REORDER_ALERT",
            user_id=None,
            details=f"Stock {stock_item.stock_code} below reorder point. Current: {stock_item.quantity_on_hand}, Reorder: {stock_item.reorder_point}"
        )