"""
Stock Take Service
Migrated from COBOL st300.cbl, st310.cbl, st320.cbl
Handles stock take and physical inventory counting
"""
from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status
import enum

from app.models.stock import StockItem, StockMovement
from app.models.control_tables import NumberSequence
from app.models.system import AuditTrail, CompanyPeriod
from app.config.settings import settings
from app.services.base import BaseService
from app.services.stock_control.stock_movement_service import StockMovementService


class StockTakeStatus(str, enum.Enum):
    """Stock take status"""
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"


class StockTakeService(BaseService):
    """Stock take processing service"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.movement_service = StockMovementService(db)
    
    def create_stock_take(
        self,
        take_date: date,
        location_code: Optional[str] = None,
        category_code: Optional[str] = None,
        stock_codes: Optional[List[str]] = None,
        description: str = None,
        user_id: int = None
    ) -> Dict:
        """
        Create new stock take
        Migrated from st300.cbl CREATE-STOCK-TAKE
        """
        try:
            # Generate stock take number
            take_number = self._get_next_stock_take_number()
            
            # Get stock items to count
            query = self.db.query(StockItem).filter(
                StockItem.is_active == True
            )
            
            if location_code:
                query = query.filter(StockItem.location == location_code)
            
            if category_code:
                query = query.filter(StockItem.category_code == category_code)
            
            if stock_codes:
                query = query.filter(StockItem.stock_code.in_(stock_codes))
            
            stock_items = query.order_by(StockItem.stock_code).all()
            
            if not stock_items:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No stock items found for the criteria"
                )
            
            # Create stock take header (would be in separate table)
            stock_take = {
                "take_number": take_number,
                "take_date": take_date,
                "location_code": location_code,
                "category_code": category_code,
                "description": description or f"Stock take {take_date}",
                "status": StockTakeStatus.DRAFT,
                "created_at": datetime.now(),
                "created_by": str(user_id) if user_id else None,
                "items": []
            }
            
            # Create stock take lines
            line_number = 0
            for item in stock_items:
                line_number += 10
                
                # Get current system quantity
                system_quantity = item.quantity_on_hand
                
                stock_take["items"].append({
                    "line_number": line_number,
                    "stock_id": item.id,
                    "stock_code": item.stock_code,
                    "description": item.description,
                    "location": item.location,
                    "bin_number": item.bin_location,
                    "unit_of_measure": item.unit_of_measure,
                    "system_quantity": system_quantity,
                    "counted_quantity": None,  # To be filled during count
                    "variance_quantity": None,
                    "variance_value": None,
                    "counted": False,
                    "count_date": None,
                    "counted_by": None
                })
            
            # Store stock take (in real system would save to database)
            # For now, create audit trail
            self._create_audit_trail(
                table_name="stock_takes",
                record_id=take_number,
                operation="CREATE",
                user_id=user_id,
                details=f"Created stock take {take_number} with {len(stock_items)} items"
            )
            
            return stock_take
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating stock take: {str(e)}"
            )
    
    def record_count(
        self,
        take_number: str,
        count_data: List[Dict],
        user_id: int
    ) -> Dict:
        """
        Record physical count
        Migrated from st310.cbl RECORD-COUNT
        """
        try:
            # In a real system, would retrieve stock take from database
            # For this example, we'll process the count data directly
            
            processed_items = []
            total_variance_value = Decimal("0")
            
            for count in count_data:
                stock_id = count["stock_id"]
                counted_quantity = Decimal(str(count["counted_quantity"]))
                
                # Get stock item
                stock_item = self.db.query(StockItem).filter(
                    StockItem.id == stock_id
                ).first()
                if not stock_item:
                    continue
                
                # Calculate variance
                system_quantity = stock_item.quantity_on_hand
                variance_quantity = counted_quantity - system_quantity
                
                # Calculate variance value
                unit_cost = stock_item.unit_cost or Decimal("0")
                variance_value = variance_quantity * unit_cost
                
                processed_items.append({
                    "stock_id": stock_id,
                    "stock_code": stock_item.stock_code,
                    "description": stock_item.description,
                    "system_quantity": system_quantity,
                    "counted_quantity": counted_quantity,
                    "variance_quantity": variance_quantity,
                    "variance_value": variance_value,
                    "variance_percent": (
                        (abs(variance_quantity) / system_quantity * 100)
                        if system_quantity > 0 else Decimal("100")
                    ),
                    "counted": True,
                    "count_date": datetime.now(),
                    "counted_by": str(user_id)
                })
                
                total_variance_value += variance_value
            
            # Create audit trail
            self._create_audit_trail(
                table_name="stock_takes",
                record_id=take_number,
                operation="COUNT",
                user_id=user_id,
                details=f"Recorded count for {len(processed_items)} items"
            )
            
            return {
                "take_number": take_number,
                "count_date": datetime.now(),
                "items_counted": len(processed_items),
                "total_variance_value": total_variance_value,
                "items": processed_items
            }
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error recording count: {str(e)}"
            )
    
    def validate_stock_take(
        self,
        take_number: str,
        variance_data: List[Dict],
        user_id: int
    ) -> Dict:
        """
        Validate stock take variances
        Migrated from st320.cbl VALIDATE-VARIANCES
        """
        try:
            validation_results = []
            items_requiring_approval = []
            
            variance_limit = settings.STOCK_TAKE_VARIANCE_LIMIT
            
            for item in variance_data:
                variance_percent = Decimal(str(item.get("variance_percent", "0")))
                variance_value = Decimal(str(item.get("variance_value", "0")))
                
                # Check variance limits
                requires_approval = False
                approval_reasons = []
                
                if abs(variance_percent) > variance_limit:
                    requires_approval = True
                    approval_reasons.append(f"Variance {variance_percent:.2f}% exceeds limit of {variance_limit}%")
                
                if abs(variance_value) > 1000:  # Value threshold
                    requires_approval = True
                    approval_reasons.append(f"Variance value {variance_value:.2f} exceeds threshold")
                
                validation_result = {
                    "stock_id": item["stock_id"],
                    "stock_code": item["stock_code"],
                    "variance_quantity": item["variance_quantity"],
                    "variance_value": variance_value,
                    "variance_percent": variance_percent,
                    "requires_approval": requires_approval,
                    "approval_reasons": approval_reasons,
                    "approved": False,
                    "approved_by": None,
                    "approval_notes": None
                }
                
                validation_results.append(validation_result)
                
                if requires_approval:
                    items_requiring_approval.append(validation_result)
            
            return {
                "take_number": take_number,
                "validation_date": datetime.now(),
                "total_items": len(validation_results),
                "items_requiring_approval": len(items_requiring_approval),
                "validation_results": validation_results,
                "items_for_approval": items_requiring_approval
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error validating stock take: {str(e)}"
            )
    
    def post_stock_take(
        self,
        take_number: str,
        adjustment_data: List[Dict],
        user_id: int
    ) -> Dict:
        """
        Post stock take adjustments
        Migrated from st320.cbl POST-ADJUSTMENTS
        """
        try:
            posted_adjustments = []
            total_adjustments = 0
            
            for adjustment in adjustment_data:
                stock_id = adjustment["stock_id"]
                variance_quantity = Decimal(str(adjustment["variance_quantity"]))
                
                if variance_quantity == 0:
                    continue
                
                # Create stock movement for adjustment
                movement = self.movement_service.adjust_stock(
                    stock_id=stock_id,
                    adjustment_quantity=variance_quantity,
                    reason_code="STOCK_TAKE",
                    notes=f"Stock take adjustment - Take number: {take_number}",
                    user_id=user_id
                )
                
                posted_adjustments.append({
                    "stock_id": stock_id,
                    "stock_code": adjustment["stock_code"],
                    "adjustment_quantity": variance_quantity,
                    "movement_id": movement.id,
                    "movement_number": movement.movement_number
                })
                
                total_adjustments += 1
            
            # Create audit trail
            self._create_audit_trail(
                table_name="stock_takes",
                record_id=take_number,
                operation="POST",
                user_id=user_id,
                details=f"Posted {total_adjustments} stock take adjustments"
            )
            
            return {
                "take_number": take_number,
                "post_date": datetime.now(),
                "posted_by": str(user_id),
                "total_adjustments": total_adjustments,
                "adjustments": posted_adjustments
            }
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error posting stock take: {str(e)}"
            )
    
    def generate_count_sheets(
        self,
        take_number: str,
        group_by: str = "location"
    ) -> List[Dict]:
        """
        Generate count sheets for physical counting
        Migrated from st300.cbl PRINT-COUNT-SHEETS
        """
        try:
            # In real system, would retrieve stock take from database
            # For this example, we'll generate sample count sheets
            
            # Get all active stock items
            stock_items = self.db.query(StockItem).filter(
                StockItem.is_active == True
            ).order_by(StockItem.location, StockItem.stock_code).all()
            
            # Group items
            count_sheets = {}
            
            for item in stock_items:
                if group_by == "location":
                    group_key = item.location or "UNASSIGNED"
                elif group_by == "category":
                    group_key = item.category_code or "UNCATEGORIZED"
                else:
                    group_key = "ALL"
                
                if group_key not in count_sheets:
                    count_sheets[group_key] = {
                        "sheet_number": len(count_sheets) + 1,
                        "group": group_key,
                        "take_number": take_number,
                        "print_date": datetime.now(),
                        "items": []
                    }
                
                count_sheets[group_key]["items"].append({
                    "stock_code": item.stock_code,
                    "description": item.description,
                    "location": item.location,
                    "bin_number": item.bin_location,
                    "unit": item.unit_of_measure,
                    "system_qty": "_____",  # Blank for blind count
                    "count_1": "_____",
                    "count_2": "_____",
                    "notes": "__________"
                })
            
            return list(count_sheets.values())
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating count sheets: {str(e)}"
            )
    
    def get_variance_report(
        self,
        take_number: str
    ) -> Dict:
        """
        Get stock take variance report
        Migrated from st320.cbl VARIANCE-REPORT
        """
        try:
            # In real system, would retrieve from database
            # For this example, return sample variance report structure
            
            return {
                "take_number": take_number,
                "report_date": datetime.now(),
                "summary": {
                    "total_items": 0,
                    "items_counted": 0,
                    "items_with_variance": 0,
                    "total_positive_variance": Decimal("0"),
                    "total_negative_variance": Decimal("0"),
                    "net_variance": Decimal("0")
                },
                "variances_by_category": {},
                "variances_by_location": {},
                "top_variances_by_value": [],
                "top_variances_by_percent": []
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating variance report: {str(e)}"
            )
    
    def _get_next_stock_take_number(self) -> str:
        """Generate next stock take number"""
        sequence = self.db.query(NumberSequence).filter(
            NumberSequence.sequence_type == "STOCK_TAKE"
        ).with_for_update().first()
        
        if not sequence:
            sequence = NumberSequence(
                sequence_type="STOCK_TAKE",
                prefix="ST",
                current_number=1,
                min_digits=6
            )
            self.db.add(sequence)
        
        sequence.current_number += 1
        number_str = str(sequence.current_number).zfill(sequence.min_digits)
        take_number = f"{sequence.prefix}{number_str}"
        
        self.db.commit()
        return take_number