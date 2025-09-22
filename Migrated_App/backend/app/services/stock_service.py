"""
Main Stock Service
Facade for all stock control operations
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from app.models.stock import StockItem
from app.models.control_tables import NumberSequence
from app.services.base import BaseService
from app.services.stock_control import (
    StockMovementService,
    StockValuationService,
    StockTakeService,
    StockReorderService
)


class StockService(BaseService):
    """Main stock service - facade for stock operations"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.movement_service = StockMovementService(db)
        self.valuation_service = StockValuationService(db)
        self.stock_take_service = StockTakeService(db)
        self.reorder_service = StockReorderService(db)
    
    def create_stock_item(
        self,
        stock_code: str,
        description: str,
        category_code: Optional[str] = None,
        unit_of_measure: str = "EACH",
        location: Optional[str] = None,
        sell_price: Optional[Decimal] = None,
        unit_cost: Optional[Decimal] = None,
        vat_code: str = "S",
        supplier_code: Optional[str] = None,
        reorder_point: Optional[Decimal] = None,
        economic_order_qty: Optional[Decimal] = None,
        user_id: int = None
    ) -> StockItem:
        """Create new stock item"""
        try:
            # Check for duplicate
            existing = self.db.query(StockItem).filter(
                StockItem.stock_code == stock_code
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Stock code {stock_code} already exists"
                )
            
            # Get supplier if specified
            supplier_id = None
            if supplier_code:
                from app.models.suppliers import Supplier
                supplier = self.db.query(Supplier).filter(
                    Supplier.supplier_code == supplier_code
                ).first()
                if supplier:
                    supplier_id = supplier.id
            
            # Create stock item
            stock_item = StockItem(
                stock_code=stock_code,
                description=description,
                category_code=category_code,
                unit_of_measure=unit_of_measure,
                location=location,
                quantity_on_hand=Decimal("0"),
                sell_price=sell_price,
                unit_cost=unit_cost,
                vat_code=vat_code,
                primary_supplier_id=supplier_id,
                reorder_point=reorder_point,
                economic_order_qty=economic_order_qty,
                is_active=True,
                created_by=str(user_id) if user_id else None
            )
            
            self.db.add(stock_item)
            self.db.commit()
            self.db.refresh(stock_item)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="stock_items",
                record_id=str(stock_item.id),
                operation="CREATE",
                user_id=user_id,
                details=f"Created stock item {stock_code}"
            )
            
            return stock_item
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating stock item: {str(e)}"
            )
    
    def update_stock_item(
        self,
        stock_id: int,
        updates: Dict,
        user_id: int = None
    ) -> StockItem:
        """Update stock item details"""
        try:
            stock_item = self.db.query(StockItem).filter(
                StockItem.id == stock_id
            ).first()
            if not stock_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stock item not found"
                )
            
            # Track changes
            changes = {}
            
            # Update allowed fields
            updatable_fields = [
                "description", "category_code", "unit_of_measure",
                "location", "bin_location", "sell_price", "vat_code",
                "reorder_point", "reorder_quantity", "economic_order_qty",
                "minimum_stock", "maximum_stock", "lead_time_days",
                "notes", "is_active"
            ]
            
            for field in updatable_fields:
                if field in updates and getattr(stock_item, field) != updates[field]:
                    changes[field] = {
                        "old": getattr(stock_item, field),
                        "new": updates[field]
                    }
                    setattr(stock_item, field, updates[field])
            
            stock_item.updated_at = datetime.now()
            stock_item.updated_by = str(user_id) if user_id else None
            
            self.db.commit()
            self.db.refresh(stock_item)
            
            # Create audit trail
            if changes:
                self._create_audit_trail(
                    table_name="stock_items",
                    record_id=str(stock_item.id),
                    operation="UPDATE",
                    user_id=user_id,
                    details=f"Updated stock item {stock_item.stock_code}",
                    changes=changes
                )
            
            return stock_item
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating stock item: {str(e)}"
            )
    
    def get_stock_item(
        self,
        stock_id: Optional[int] = None,
        stock_code: Optional[str] = None
    ) -> StockItem:
        """Get stock item by ID or code"""
        try:
            query = self.db.query(StockItem)
            
            if stock_id:
                query = query.filter(StockItem.id == stock_id)
            elif stock_code:
                query = query.filter(StockItem.stock_code == stock_code)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either stock_id or stock_code must be provided"
                )
            
            stock_item = query.first()
            if not stock_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stock item not found"
                )
            
            return stock_item
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving stock item: {str(e)}"
            )
    
    def search_stock_items(
        self,
        search_term: Optional[str] = None,
        category_code: Optional[str] = None,
        location: Optional[str] = None,
        supplier_code: Optional[str] = None,
        below_reorder: bool = False,
        active_only: bool = True,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """Search stock items with filtering"""
        try:
            query = self.db.query(StockItem)
            
            # Apply filters
            if active_only:
                query = query.filter(StockItem.is_active == True)
            
            if search_term:
                query = query.filter(
                    or_(
                        StockItem.stock_code.ilike(f"%{search_term}%"),
                        StockItem.description.ilike(f"%{search_term}%")
                    )
                )
            
            if category_code:
                query = query.filter(StockItem.category_code == category_code)
            
            if location:
                query = query.filter(StockItem.location == location)
            
            if supplier_code:
                from app.models.suppliers import Supplier
                query = query.join(Supplier).filter(
                    Supplier.supplier_code == supplier_code
                )
            
            if below_reorder:
                query = query.filter(
                    and_(
                        StockItem.reorder_point.isnot(None),
                        StockItem.quantity_on_hand <= StockItem.reorder_point
                    )
                )
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            items = query.order_by(StockItem.stock_code)\
                        .offset((page - 1) * page_size)\
                        .limit(page_size)\
                        .all()
            
            return {
                "items": items,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error searching stock items: {str(e)}"
            )
    
    def get_stock_summary(
        self,
        location_code: Optional[str] = None,
        category_code: Optional[str] = None
    ) -> Dict:
        """Get stock summary statistics"""
        try:
            query = self.db.query(StockItem).filter(
                StockItem.is_active == True
            )
            
            if location_code:
                query = query.filter(StockItem.location == location_code)
            
            if category_code:
                query = query.filter(StockItem.category_code == category_code)
            
            items = query.all()
            
            # Calculate summary
            total_items = len(items)
            total_quantity = sum(item.quantity_on_hand for item in items)
            total_value = sum(
                item.quantity_on_hand * (item.unit_cost or Decimal("0"))
                for item in items
            )
            
            # Count by status
            items_below_reorder = sum(
                1 for item in items
                if item.reorder_point and item.quantity_on_hand <= item.reorder_point
            )
            items_zero_stock = sum(
                1 for item in items
                if item.quantity_on_hand == 0
            )
            items_negative_stock = sum(
                1 for item in items
                if item.quantity_on_hand < 0
            )
            
            return {
                "summary_date": datetime.now(),
                "filters": {
                    "location": location_code,
                    "category": category_code
                },
                "totals": {
                    "item_count": total_items,
                    "total_quantity": total_quantity,
                    "total_value": total_value
                },
                "status": {
                    "below_reorder": items_below_reorder,
                    "zero_stock": items_zero_stock,
                    "negative_stock": items_negative_stock
                },
                "percentages": {
                    "below_reorder_pct": (
                        items_below_reorder / total_items * 100
                        if total_items > 0 else 0
                    ),
                    "zero_stock_pct": (
                        items_zero_stock / total_items * 100
                        if total_items > 0 else 0
                    )
                }
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating stock summary: {str(e)}"
            )
    
    # Delegate to sub-services
    def create_stock_movement(self, **kwargs):
        """Create stock movement - delegates to movement service"""
        return self.movement_service.create_stock_movement(**kwargs)
    
    def calculate_stock_value(self, **kwargs):
        """Calculate stock value - delegates to valuation service"""
        return self.valuation_service.calculate_stock_value(**kwargs)
    
    def check_reorder_levels(self, **kwargs):
        """Check reorder levels - delegates to reorder service"""
        return self.reorder_service.check_reorder_levels(**kwargs)
    
    def create_stock_take(self, **kwargs):
        """Create stock take - delegates to stock take service"""
        return self.stock_take_service.create_stock_take(**kwargs)