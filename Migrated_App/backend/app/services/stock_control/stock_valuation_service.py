"""
Stock Valuation Service
Migrated from COBOL st200.cbl, st210.cbl, st220.cbl
Handles stock valuation and costing
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status

from app.models.stock import StockItem, StockMovement, StockValuation
from app.models.purchase_transactions import PurchaseInvoiceLine
from app.models.system import CompanyPeriod
from app.config.settings import settings
from app.services.base import BaseService


class StockValuationService(BaseService):
    """Stock valuation and costing service"""
    
    def calculate_stock_value(
        self,
        stock_id: Optional[int] = None,
        location_code: Optional[str] = None,
        category_code: Optional[str] = None,
        as_at_date: Optional[date] = None
    ) -> Dict:
        """
        Calculate stock value
        Migrated from st200.cbl CALCULATE-STOCK-VALUE
        """
        try:
            # Build query
            query = self.db.query(StockItem)
            
            if stock_id:
                query = query.filter(StockItem.id == stock_id)
            
            if location_code:
                query = query.filter(StockItem.location == location_code)
            
            if category_code:
                query = query.filter(StockItem.category_code == category_code)
            
            stock_items = query.all()
            
            # Calculate values
            total_quantity = Decimal("0")
            total_value_cost = Decimal("0")
            total_value_sell = Decimal("0")
            
            item_values = []
            
            for item in stock_items:
                if as_at_date:
                    # Calculate historical quantity
                    quantity = self._get_quantity_as_at(item.id, as_at_date)
                else:
                    quantity = item.quantity_on_hand
                
                if quantity <= 0:
                    continue
                
                # Get valuation
                cost_price = self._get_item_cost(item, quantity, as_at_date)
                sell_price = item.sell_price or Decimal("0")
                
                value_cost = quantity * cost_price
                value_sell = quantity * sell_price
                
                item_values.append({
                    "stock_id": item.id,
                    "stock_code": item.stock_code,
                    "description": item.description,
                    "quantity": quantity,
                    "cost_price": cost_price,
                    "sell_price": sell_price,
                    "value_cost": value_cost,
                    "value_sell": value_sell,
                    "margin": value_sell - value_cost,
                    "margin_percent": (
                        ((value_sell - value_cost) / value_cost * 100)
                        if value_cost > 0 else Decimal("0")
                    )
                })
                
                total_quantity += quantity
                total_value_cost += value_cost
                total_value_sell += value_sell
            
            return {
                "as_at_date": as_at_date or date.today(),
                "item_count": len(item_values),
                "total_quantity": total_quantity,
                "total_value_cost": total_value_cost,
                "total_value_sell": total_value_sell,
                "total_margin": total_value_sell - total_value_cost,
                "average_margin_percent": (
                    ((total_value_sell - total_value_cost) / total_value_cost * 100)
                    if total_value_cost > 0 else Decimal("0")
                ),
                "items": item_values
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error calculating stock value: {str(e)}"
            )
    
    def revalue_stock(
        self,
        stock_id: int,
        new_cost_price: Decimal,
        reason: str,
        effective_date: Optional[date] = None,
        user_id: int = None
    ) -> StockItem:
        """
        Revalue stock item
        Migrated from st210.cbl REVALUE-STOCK
        """
        try:
            # Get stock item
            stock_item = self.db.query(StockItem).filter(
                StockItem.id == stock_id
            ).first()
            if not stock_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stock item not found"
                )
            
            # Calculate revaluation amount
            old_cost = stock_item.unit_cost or Decimal("0")
            quantity = stock_item.quantity_on_hand
            old_value = quantity * old_cost
            new_value = quantity * new_cost_price
            adjustment = new_value - old_value
            
            # Update stock item
            stock_item.unit_cost = new_cost_price
            stock_item.last_cost = old_cost
            stock_item.updated_at = datetime.now()
            stock_item.updated_by = str(user_id) if user_id else None
            
            # Create stock movement for audit
            from app.services.stock_control.stock_movement_service import StockMovementService
            movement_service = StockMovementService(self.db)
            
            movement = movement_service.create_stock_movement(
                stock_id=stock_id,
                movement_type="ADJUSTMENT",
                quantity=Decimal("0"),  # No quantity change
                reference_type="REVALUATION",
                cost_price=new_cost_price,
                notes=f"Stock revaluation: {reason}. Old cost: {old_cost}, New cost: {new_cost_price}",
                user_id=user_id
            )
            
            # Create audit trail
            self._create_audit_trail(
                table_name="stock_items",
                record_id=str(stock_id),
                operation="REVALUE",
                user_id=user_id,
                details=f"Revalued stock from {old_cost} to {new_cost_price}. Adjustment: {adjustment}",
                changes={
                    "unit_cost": {"old": str(old_cost), "new": str(new_cost_price)},
                    "stock_value": {"old": str(old_value), "new": str(new_value)}
                }
            )
            
            self.db.commit()
            self.db.refresh(stock_item)
            
            return stock_item
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error revaluing stock: {str(e)}"
            )
    
    def change_valuation_method(
        self,
        stock_id: int,
        new_method: str,
        user_id: int
    ) -> StockItem:
        """
        Change stock valuation method
        Migrated from st220.cbl CHANGE-VALUATION-METHOD
        """
        try:
            # Validate method
            valid_methods = ["FIFO", "LIFO", "AVERAGE", "STANDARD"]
            if new_method not in valid_methods:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid valuation method: {new_method}"
                )
            
            # Get stock item
            stock_item = self.db.query(StockItem).filter(
                StockItem.id == stock_id
            ).first()
            if not stock_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stock item not found"
                )
            
            old_method = stock_item.valuation_method or settings.STOCK_VALUATION_METHOD
            
            if old_method == new_method:
                return stock_item
            
            # Calculate current value with old method
            current_value = self._get_item_cost(
                stock_item,
                stock_item.quantity_on_hand
            ) * stock_item.quantity_on_hand
            
            # Update method
            stock_item.valuation_method = new_method
            
            # If changing to AVERAGE, calculate new average cost
            if new_method == "AVERAGE":
                if stock_item.quantity_on_hand > 0:
                    stock_item.unit_cost = (
                        current_value / stock_item.quantity_on_hand
                    ).quantize(Decimal("0.0001"))
            
            # If changing from AVERAGE to FIFO/LIFO, create initial valuation
            elif old_method == "AVERAGE" and new_method in ["FIFO", "LIFO"]:
                if stock_item.quantity_on_hand > 0:
                    valuation = StockValuation(
                        stock_id=stock_id,
                        receipt_date=datetime.now(),
                        quantity_received=stock_item.quantity_on_hand,
                        quantity_remaining=stock_item.quantity_on_hand,
                        cost_price=stock_item.unit_cost or Decimal("0"),
                        total_cost=current_value
                    )
                    self.db.add(valuation)
            
            stock_item.updated_at = datetime.now()
            stock_item.updated_by = str(user_id)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="stock_items",
                record_id=str(stock_id),
                operation="CHANGE_VALUATION",
                user_id=user_id,
                details=f"Changed valuation method from {old_method} to {new_method}"
            )
            
            self.db.commit()
            self.db.refresh(stock_item)
            
            return stock_item
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error changing valuation method: {str(e)}"
            )
    
    def get_stock_aging(
        self,
        stock_id: Optional[int] = None,
        location_code: Optional[str] = None,
        days_brackets: List[int] = None
    ) -> Dict:
        """
        Get stock aging analysis
        Migrated from st220.cbl STOCK-AGING
        """
        try:
            if not days_brackets:
                days_brackets = [30, 60, 90, 180, 365]
            
            # Build query
            query = self.db.query(StockValuation).filter(
                StockValuation.quantity_remaining > 0
            )
            
            if stock_id:
                query = query.filter(StockValuation.stock_id == stock_id)
            
            valuations = query.all()
            
            # Group by age brackets
            aging = {}
            total_quantity = Decimal("0")
            total_value = Decimal("0")
            
            for bracket in days_brackets:
                aging[f"0-{bracket}"] = {
                    "quantity": Decimal("0"),
                    "value": Decimal("0"),
                    "items": []
                }
            
            aging["over_" + str(max(days_brackets))] = {
                "quantity": Decimal("0"),
                "value": Decimal("0"),
                "items": []
            }
            
            today = date.today()
            
            for val in valuations:
                days_old = (today - val.receipt_date.date()).days
                quantity = val.quantity_remaining
                value = quantity * val.cost_price
                
                # Find appropriate bracket
                bracket_found = False
                for bracket in sorted(days_brackets):
                    if days_old <= bracket:
                        key = f"0-{bracket}"
                        aging[key]["quantity"] += quantity
                        aging[key]["value"] += value
                        aging[key]["items"].append({
                            "stock_id": val.stock_id,
                            "receipt_date": val.receipt_date,
                            "days_old": days_old,
                            "quantity": quantity,
                            "cost_price": val.cost_price,
                            "value": value
                        })
                        bracket_found = True
                        break
                
                if not bracket_found:
                    key = "over_" + str(max(days_brackets))
                    aging[key]["quantity"] += quantity
                    aging[key]["value"] += value
                    aging[key]["items"].append({
                        "stock_id": val.stock_id,
                        "receipt_date": val.receipt_date,
                        "days_old": days_old,
                        "quantity": quantity,
                        "cost_price": val.cost_price,
                        "value": value
                    })
                
                total_quantity += quantity
                total_value += value
            
            return {
                "as_at_date": today,
                "total_quantity": total_quantity,
                "total_value": total_value,
                "aging_brackets": aging,
                "summary": {
                    bracket: {
                        "quantity": data["quantity"],
                        "value": data["value"],
                        "quantity_percent": (
                            (data["quantity"] / total_quantity * 100)
                            if total_quantity > 0 else Decimal("0")
                        ),
                        "value_percent": (
                            (data["value"] / total_value * 100)
                            if total_value > 0 else Decimal("0")
                        )
                    }
                    for bracket, data in aging.items()
                }
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error calculating stock aging: {str(e)}"
            )
    
    def process_period_end_valuation(
        self,
        period_id: int,
        user_id: int
    ) -> Dict:
        """
        Process period end stock valuation
        Migrated from st220.cbl PERIOD-END-VALUATION
        """
        try:
            # Get period
            period = self.db.query(CompanyPeriod).filter(
                CompanyPeriod.id == period_id
            ).first()
            if not period:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Period not found"
                )
            
            # Get all stock items
            stock_items = self.db.query(StockItem).filter(
                StockItem.is_active == True
            ).all()
            
            results = []
            total_value = Decimal("0")
            
            for item in stock_items:
                # Calculate period-end quantity
                quantity = self._get_quantity_as_at(item.id, period.end_date.date())
                
                if quantity <= 0:
                    continue
                
                # Calculate value
                cost_price = self._get_item_cost(item, quantity, period.end_date.date())
                value = quantity * cost_price
                
                results.append({
                    "stock_id": item.id,
                    "stock_code": item.stock_code,
                    "description": item.description,
                    "quantity": quantity,
                    "cost_price": cost_price,
                    "total_value": value
                })
                
                total_value += value
                
                # Update period-end snapshot (would store in separate table)
                # For now, just audit
                self._create_audit_trail(
                    table_name="stock_period_end",
                    record_id=f"{period_id}_{item.id}",
                    operation="PERIOD_END",
                    user_id=user_id,
                    details=f"Period {period.period_number} closing stock: {quantity} @ {cost_price} = {value}"
                )
            
            return {
                "period": period.period_number,
                "year": period.year_number,
                "end_date": period.end_date,
                "item_count": len(results),
                "total_value": total_value,
                "items": results
            }
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing period-end valuation: {str(e)}"
            )
    
    def _get_quantity_as_at(
        self,
        stock_id: int,
        as_at_date: date
    ) -> Decimal:
        """Calculate stock quantity as at specific date"""
        # Get current quantity
        stock_item = self.db.query(StockItem).filter(
            StockItem.id == stock_id
        ).first()
        if not stock_item:
            return Decimal("0")
        
        current_quantity = stock_item.quantity_on_hand
        
        # Get movements after the date
        movements_after = self.db.query(StockMovement).filter(
            and_(
                StockMovement.stock_id == stock_id,
                StockMovement.movement_date > as_at_date
            )
        ).all()
        
        # Reverse the movements
        for movement in movements_after:
            if movement.is_inward:
                current_quantity -= movement.quantity
            else:
                current_quantity += movement.quantity
        
        return max(current_quantity, Decimal("0"))
    
    def _get_item_cost(
        self,
        stock_item: StockItem,
        quantity: Decimal,
        as_at_date: Optional[date] = None
    ) -> Decimal:
        """Get item cost based on valuation method"""
        valuation_method = stock_item.valuation_method or settings.STOCK_VALUATION_METHOD
        
        if valuation_method == "STANDARD":
            return stock_item.standard_cost or stock_item.unit_cost or Decimal("0")
        
        elif valuation_method == "AVERAGE":
            return stock_item.unit_cost or Decimal("0")
        
        elif valuation_method in ["FIFO", "LIFO"]:
            # Get valuations
            query = self.db.query(StockValuation).filter(
                and_(
                    StockValuation.stock_id == stock_item.id,
                    StockValuation.quantity_remaining > 0
                )
            )
            
            if as_at_date:
                query = query.filter(StockValuation.receipt_date <= as_at_date)
            
            if valuation_method == "FIFO":
                valuations = query.order_by(StockValuation.receipt_date).all()
            else:  # LIFO
                valuations = query.order_by(desc(StockValuation.receipt_date)).all()
            
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
        
        return stock_item.unit_cost or Decimal("0")