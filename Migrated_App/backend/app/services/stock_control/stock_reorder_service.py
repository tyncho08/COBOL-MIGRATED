"""
Stock Reorder Service
Migrated from COBOL st400.cbl, st410.cbl, st420.cbl
Handles automatic reordering and stock replenishment
"""
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from app.models.stock import StockItem, StockMovement
from app.models.suppliers import Supplier
from app.models.purchase_transactions import PurchaseOrder, PurchaseOrderLine
from app.models.control_tables import BackOrder
from app.models.system import SystemParameter
from app.config.settings import settings
from app.services.base import BaseService
from app.services.purchase_ledger.purchase_order_service import PurchaseOrderService


class StockReorderService(BaseService):
    """Stock reordering and replenishment service"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.po_service = PurchaseOrderService(db)
    
    def check_reorder_levels(
        self,
        location_code: Optional[str] = None,
        category_code: Optional[str] = None,
        supplier_code: Optional[str] = None
    ) -> List[Dict]:
        """
        Check stock items below reorder level
        Migrated from st400.cbl CHECK-REORDER-LEVELS
        """
        try:
            # Build query
            query = self.db.query(StockItem).filter(
                and_(
                    StockItem.is_active == True,
                    StockItem.reorder_point.isnot(None),
                    StockItem.reorder_point > 0
                )
            )
            
            if location_code:
                query = query.filter(StockItem.location == location_code)
            
            if category_code:
                query = query.filter(StockItem.category_code == category_code)
            
            if supplier_code:
                query = query.join(Supplier).filter(
                    Supplier.supplier_code == supplier_code
                )
            
            stock_items = query.all()
            
            # Check reorder levels
            items_to_reorder = []
            
            for item in stock_items:
                # Calculate available quantity (including on order)
                on_order = self._get_quantity_on_order(item.id)
                available = item.quantity_on_hand + on_order
                
                if available <= item.reorder_point:
                    # Calculate reorder quantity
                    reorder_qty = self._calculate_reorder_quantity(item)
                    
                    # Get lead time and calculate required date
                    lead_time = item.lead_time_days or 7
                    required_date = date.today() + timedelta(days=lead_time)
                    
                    # Get last purchase price
                    last_price = self._get_last_purchase_price(item)
                    
                    items_to_reorder.append({
                        "stock_id": item.id,
                        "stock_code": item.stock_code,
                        "description": item.description,
                        "supplier_id": item.primary_supplier_id,
                        "supplier_code": item.supplier.supplier_code if item.supplier else None,
                        "current_quantity": item.quantity_on_hand,
                        "on_order": on_order,
                        "available": available,
                        "reorder_point": item.reorder_point,
                        "reorder_quantity": reorder_qty,
                        "economic_order_qty": item.economic_order_qty,
                        "lead_time_days": lead_time,
                        "required_date": required_date,
                        "last_price": last_price,
                        "estimated_value": reorder_qty * last_price
                    })
            
            # Sort by urgency (lowest available/reorder ratio first)
            items_to_reorder.sort(
                key=lambda x: x["available"] / x["reorder_point"] if x["reorder_point"] > 0 else 0
            )
            
            return items_to_reorder
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error checking reorder levels: {str(e)}"
            )
    
    def generate_reorder_suggestions(
        self,
        forecast_days: int = 30,
        safety_factor: Decimal = Decimal("1.2")
    ) -> List[Dict]:
        """
        Generate intelligent reorder suggestions
        Migrated from st410.cbl GENERATE-SUGGESTIONS
        """
        try:
            suggestions = []
            
            # Get active stock items with reorder settings
            stock_items = self.db.query(StockItem).filter(
                and_(
                    StockItem.is_active == True,
                    StockItem.reorder_point.isnot(None)
                )
            ).all()
            
            for item in stock_items:
                # Calculate average daily usage
                avg_daily_usage = self._calculate_average_usage(
                    item.id,
                    days=90  # Look at last 90 days
                )
                
                if avg_daily_usage <= 0:
                    continue
                
                # Calculate forecasted demand
                forecasted_demand = avg_daily_usage * forecast_days * safety_factor
                
                # Get current position
                on_hand = item.quantity_on_hand
                on_order = self._get_quantity_on_order(item.id)
                back_orders = self._get_back_order_quantity(item.id)
                
                # Calculate net requirement
                net_position = on_hand + on_order - back_orders
                net_requirement = forecasted_demand - net_position
                
                if net_requirement > 0:
                    # Round up to economic order quantity
                    if item.economic_order_qty and item.economic_order_qty > 0:
                        reorder_qty = (
                            (net_requirement // item.economic_order_qty + 1) *
                            item.economic_order_qty
                        )
                    else:
                        reorder_qty = net_requirement
                    
                    # Get supplier info
                    supplier = item.supplier
                    lead_time = item.lead_time_days or (supplier.lead_time_days if supplier else 7)
                    
                    suggestions.append({
                        "stock_id": item.id,
                        "stock_code": item.stock_code,
                        "description": item.description,
                        "supplier_code": supplier.supplier_code if supplier else None,
                        "avg_daily_usage": avg_daily_usage,
                        "forecast_days": forecast_days,
                        "forecasted_demand": forecasted_demand,
                        "on_hand": on_hand,
                        "on_order": on_order,
                        "back_orders": back_orders,
                        "net_position": net_position,
                        "suggested_quantity": reorder_qty,
                        "lead_time": lead_time,
                        "order_by_date": date.today() + timedelta(days=max(0, forecast_days - lead_time)),
                        "confidence": self._calculate_confidence_score(item, avg_daily_usage)
                    })
            
            # Sort by order-by date
            suggestions.sort(key=lambda x: x["order_by_date"])
            
            return suggestions
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating suggestions: {str(e)}"
            )
    
    def create_automatic_orders(
        self,
        items_to_order: List[Dict],
        combine_by_supplier: bool = True,
        user_id: int = None
    ) -> List[PurchaseOrder]:
        """
        Create automatic purchase orders
        Migrated from st420.cbl CREATE-AUTO-ORDERS
        """
        try:
            created_orders = []
            
            if combine_by_supplier:
                # Group items by supplier
                orders_by_supplier = {}
                
                for item in items_to_order:
                    supplier_code = item.get("supplier_code")
                    if not supplier_code:
                        continue
                    
                    if supplier_code not in orders_by_supplier:
                        orders_by_supplier[supplier_code] = []
                    
                    orders_by_supplier[supplier_code].append(item)
                
                # Create orders
                for supplier_code, order_items in orders_by_supplier.items():
                    order_lines = []
                    
                    for item in order_items:
                        order_lines.append({
                            "stock_code": item["stock_code"],
                            "description": item.get("description", ""),
                            "quantity": item["reorder_quantity"],
                            "unit_price": item.get("last_price", Decimal("0")),
                            "vat_code": "S"
                        })
                    
                    # Create purchase order
                    order = self.po_service.create_purchase_order(
                        supplier_code=supplier_code,
                        order_lines=order_lines,
                        delivery_date=max(
                            item.get("required_date", date.today() + timedelta(days=7))
                            for item in order_items
                        ),
                        notes="Automatic reorder",
                        user_id=user_id
                    )
                    
                    created_orders.append(order)
            
            else:
                # Create individual orders
                for item in items_to_order:
                    if not item.get("supplier_code"):
                        continue
                    
                    order_lines = [{
                        "stock_code": item["stock_code"],
                        "description": item.get("description", ""),
                        "quantity": item["reorder_quantity"],
                        "unit_price": item.get("last_price", Decimal("0")),
                        "vat_code": "S"
                    }]
                    
                    order = self.po_service.create_purchase_order(
                        supplier_code=item["supplier_code"],
                        order_lines=order_lines,
                        delivery_date=item.get("required_date", date.today() + timedelta(days=7)),
                        notes=f"Automatic reorder for {item['stock_code']}",
                        user_id=user_id
                    )
                    
                    created_orders.append(order)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="automatic_reorders",
                record_id=datetime.now().strftime("%Y%m%d%H%M%S"),
                operation="AUTO_ORDER",
                user_id=user_id,
                details=f"Created {len(created_orders)} automatic orders for {len(items_to_order)} items"
            )
            
            return created_orders
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating automatic orders: {str(e)}"
            )
    
    def analyze_reorder_performance(
        self,
        stock_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Dict:
        """
        Analyze reorder performance and suggest parameter adjustments
        Migrated from st420.cbl ANALYZE-PERFORMANCE
        """
        try:
            if not from_date:
                from_date = date.today() - timedelta(days=365)
            if not to_date:
                to_date = date.today()
            
            # Build query
            query = self.db.query(StockItem)
            if stock_id:
                query = query.filter(StockItem.id == stock_id)
            
            stock_items = query.all()
            
            analysis_results = []
            
            for item in stock_items:
                # Get stock out events
                stock_outs = self._get_stock_out_events(
                    item.id, from_date, to_date
                )
                
                # Get reorder history
                reorders = self._get_reorder_history(
                    item.id, from_date, to_date
                )
                
                # Calculate metrics
                avg_usage = self._calculate_average_usage(
                    item.id, (to_date - from_date).days
                )
                
                lead_time_actual = self._calculate_actual_lead_time(item.id)
                
                # Analyze reorder point effectiveness
                if item.reorder_point:
                    safety_days = (
                        item.reorder_point / avg_usage
                        if avg_usage > 0 else 0
                    )
                else:
                    safety_days = 0
                
                # Suggest new parameters
                suggested_reorder_point = None
                suggested_eoq = None
                
                if avg_usage > 0:
                    # Suggest reorder point: (avg usage * lead time) + safety stock
                    safety_factor = Decimal("1.5")  # 50% safety stock
                    suggested_reorder_point = (
                        avg_usage * (lead_time_actual or item.lead_time_days or 7) *
                        safety_factor
                    ).quantize(Decimal("1"))
                    
                    # Suggest EOQ using simplified formula
                    # EOQ = sqrt(2 * annual demand * order cost / holding cost)
                    annual_demand = avg_usage * 365
                    order_cost = Decimal("50")  # Assumed order cost
                    holding_cost_rate = Decimal("0.2")  # 20% of item cost
                    unit_cost = item.unit_cost or Decimal("1")
                    
                    if unit_cost > 0:
                        suggested_eoq = (
                            (2 * annual_demand * order_cost / 
                             (holding_cost_rate * unit_cost)) ** Decimal("0.5")
                        ).quantize(Decimal("1"))
                
                analysis_results.append({
                    "stock_id": item.id,
                    "stock_code": item.stock_code,
                    "description": item.description,
                    "analysis_period": f"{from_date} to {to_date}",
                    "metrics": {
                        "stock_out_events": len(stock_outs),
                        "total_reorders": len(reorders),
                        "avg_daily_usage": avg_usage,
                        "actual_lead_time": lead_time_actual,
                        "safety_days": float(safety_days)
                    },
                    "current_parameters": {
                        "reorder_point": item.reorder_point,
                        "economic_order_qty": item.economic_order_qty,
                        "lead_time_days": item.lead_time_days
                    },
                    "suggested_parameters": {
                        "reorder_point": suggested_reorder_point,
                        "economic_order_qty": suggested_eoq,
                        "lead_time_days": lead_time_actual
                    },
                    "recommendations": self._generate_recommendations(
                        item, stock_outs, avg_usage
                    )
                })
            
            return {
                "analysis_date": datetime.now(),
                "period": {"from": from_date, "to": to_date},
                "items_analyzed": len(analysis_results),
                "results": analysis_results,
                "summary": self._generate_analysis_summary(analysis_results)
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error analyzing performance: {str(e)}"
            )
    
    def _get_quantity_on_order(self, stock_id: int) -> Decimal:
        """Get quantity currently on order"""
        result = self.db.query(
            func.sum(PurchaseOrderLine.quantity_outstanding)
        ).join(PurchaseOrder).filter(
            and_(
                PurchaseOrderLine.stock_id == stock_id,
                PurchaseOrder.order_status.in_(["SUBMITTED", "APPROVED", "PARTIAL"])
            )
        ).scalar()
        
        return result or Decimal("0")
    
    def _get_back_order_quantity(self, stock_id: int) -> Decimal:
        """Get quantity on back order"""
        result = self.db.query(
            func.sum(BackOrder.outstanding_quantity)
        ).filter(
            and_(
                BackOrder.stock_id == stock_id,
                BackOrder.status == "OPEN"
            )
        ).scalar()
        
        return result or Decimal("0")
    
    def _calculate_reorder_quantity(self, stock_item: StockItem) -> Decimal:
        """Calculate reorder quantity"""
        if stock_item.economic_order_qty and stock_item.economic_order_qty > 0:
            return stock_item.economic_order_qty
        
        if stock_item.reorder_quantity and stock_item.reorder_quantity > 0:
            return stock_item.reorder_quantity
        
        # Default: order enough to reach max stock level
        if stock_item.maximum_stock:
            return max(
                stock_item.maximum_stock - stock_item.quantity_on_hand,
                Decimal("0")
            )
        
        # Default: double the reorder point
        return stock_item.reorder_point * 2
    
    def _get_last_purchase_price(self, stock_item: StockItem) -> Decimal:
        """Get last purchase price"""
        last_invoice = self.db.query(PurchaseInvoiceLine).filter(
            PurchaseInvoiceLine.stock_id == stock_item.id
        ).order_by(desc(PurchaseInvoiceLine.created_at)).first()
        
        if last_invoice:
            return last_invoice.unit_price
        
        return stock_item.unit_cost or Decimal("0")
    
    def _calculate_average_usage(
        self,
        stock_id: int,
        days: int
    ) -> Decimal:
        """Calculate average daily usage"""
        from_date = date.today() - timedelta(days=days)
        
        # Get outward movements
        total_usage = self.db.query(
            func.sum(StockMovement.quantity)
        ).filter(
            and_(
                StockMovement.stock_id == stock_id,
                StockMovement.is_inward == False,
                StockMovement.movement_type.in_([
                    "SALES_ISSUE", "TRANSFER", "PRODUCTION_OUT"
                ]),
                StockMovement.movement_date >= from_date
            )
        ).scalar() or Decimal("0")
        
        return (total_usage / days).quantize(Decimal("0.01"))
    
    def _calculate_confidence_score(
        self,
        stock_item: StockItem,
        avg_usage: Decimal
    ) -> Decimal:
        """Calculate confidence score for reorder suggestion"""
        score = Decimal("100")
        
        # Reduce score if no recent usage
        if avg_usage <= 0:
            score -= 50
        
        # Reduce score if no reorder parameters set
        if not stock_item.reorder_point:
            score -= 20
        if not stock_item.economic_order_qty:
            score -= 10
        
        # Reduce score if no supplier assigned
        if not stock_item.primary_supplier_id:
            score -= 20
        
        return max(score, Decimal("0"))
    
    def _get_stock_out_events(
        self,
        stock_id: int,
        from_date: date,
        to_date: date
    ) -> List[Dict]:
        """Get stock-out events in period"""
        # Simplified - would need more complex logic to track actual stock-outs
        events = []
        
        # Check for negative movements that would have caused stock-out
        movements = self.db.query(StockMovement).filter(
            and_(
                StockMovement.stock_id == stock_id,
                StockMovement.movement_date.between(from_date, to_date),
                StockMovement.quantity_after < 0
            )
        ).all()
        
        for movement in movements:
            events.append({
                "date": movement.movement_date,
                "quantity_short": abs(movement.quantity_after)
            })
        
        return events
    
    def _get_reorder_history(
        self,
        stock_id: int,
        from_date: date,
        to_date: date
    ) -> List[Dict]:
        """Get reorder history"""
        orders = self.db.query(PurchaseOrderLine).join(PurchaseOrder).filter(
            and_(
                PurchaseOrderLine.stock_id == stock_id,
                PurchaseOrder.order_date.between(from_date, to_date)
            )
        ).all()
        
        return [{
            "order_date": order.order.order_date,
            "quantity": order.quantity_ordered,
            "received_date": None  # Would need to join with goods receipts
        } for order in orders]
    
    def _calculate_actual_lead_time(self, stock_id: int) -> Optional[int]:
        """Calculate actual average lead time from orders"""
        # Simplified - would need to track order to receipt timing
        return None
    
    def _generate_recommendations(
        self,
        item: StockItem,
        stock_outs: List[Dict],
        avg_usage: Decimal
    ) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if len(stock_outs) > 0:
            recommendations.append(
                f"Experienced {len(stock_outs)} stock-out events - consider increasing reorder point"
            )
        
        if item.reorder_point and avg_usage > 0:
            days_cover = item.reorder_point / avg_usage
            if days_cover < 7:
                recommendations.append(
                    f"Current reorder point only provides {days_cover:.1f} days cover - consider increasing"
                )
        
        if not item.economic_order_qty:
            recommendations.append(
                "No economic order quantity set - consider setting EOQ to optimize order costs"
            )
        
        return recommendations
    
    def _generate_analysis_summary(self, results: List[Dict]) -> Dict:
        """Generate summary of analysis results"""
        total_items = len(results)
        items_with_stockouts = sum(
            1 for r in results 
            if r["metrics"]["stock_out_events"] > 0
        )
        
        items_needing_adjustment = sum(
            1 for r in results
            if r["suggested_parameters"]["reorder_point"] != r["current_parameters"]["reorder_point"]
        )
        
        return {
            "total_items_analyzed": total_items,
            "items_with_stockouts": items_with_stockouts,
            "items_needing_reorder_adjustment": items_needing_adjustment,
            "stockout_rate": (
                items_with_stockouts / total_items * 100
                if total_items > 0 else 0
            )
        }