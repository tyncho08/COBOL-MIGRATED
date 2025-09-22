"""
Unit tests for Stock Movement Service
Tests the core business logic migrated from COBOL st400.cbl, st410.cbl, st500.cbl
"""
import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.services.stock_control.stock_movement_service import StockMovementService
from app.models.stock import StockMovement, MovementType, MovementStatus


class TestStockMovementService:
    """Test Stock Movement Service functionality"""

    def test_create_stock_receipt_success(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test successful stock receipt creation"""
        service = StockMovementService(db)
        
        movement = service.create_stock_receipt(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("50"),
            unit_cost=Decimal("25.00"),
            reference="PO001",
            notes="Stock receipt from supplier",
            user_id=test_user_id
        )
        
        assert movement is not None
        assert movement.stock_code == sample_stock_item.stock_code
        assert movement.movement_type == MovementType.RECEIPT
        assert movement.quantity == Decimal("50")
        assert movement.unit_cost == Decimal("25.00")
        assert movement.reference == "PO001"
        assert movement.movement_status == MovementStatus.CONFIRMED

    def test_create_stock_issue_success(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test successful stock issue creation"""
        service = StockMovementService(db)
        
        movement = service.create_stock_issue(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("20"),
            reference="SO001",
            notes="Stock issue for sales order",
            user_id=test_user_id
        )
        
        assert movement is not None
        assert movement.stock_code == sample_stock_item.stock_code
        assert movement.movement_type == MovementType.ISSUE
        assert movement.quantity == Decimal("20")
        assert movement.reference == "SO001"
        assert movement.movement_status == MovementStatus.CONFIRMED

    def test_create_stock_adjustment_success(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test successful stock adjustment creation"""
        service = StockMovementService(db)
        
        movement = service.create_stock_adjustment(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("-5"),  # Negative for reduction
            reason_code="DAMAGE",
            notes="Damaged items written off",
            user_id=test_user_id
        )
        
        assert movement is not None
        assert movement.stock_code == sample_stock_item.stock_code
        assert movement.movement_type == MovementType.ADJUSTMENT
        assert movement.quantity == Decimal("-5")
        assert movement.reason_code == "DAMAGE"
        assert movement.movement_status == MovementStatus.CONFIRMED

    def test_create_stock_transfer_success(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test successful stock transfer creation"""
        service = StockMovementService(db)
        
        movement = service.create_stock_transfer(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("10"),
            from_location="MAIN",
            to_location="SHOP",
            reference="TR001",
            notes="Transfer to shop floor",
            user_id=test_user_id
        )
        
        assert movement is not None
        assert movement.stock_code == sample_stock_item.stock_code
        assert movement.movement_type == MovementType.TRANSFER
        assert movement.quantity == Decimal("10")
        assert movement.from_location == "MAIN"
        assert movement.to_location == "SHOP"
        assert movement.movement_status == MovementStatus.CONFIRMED

    def test_create_movement_invalid_stock_code(
        self, 
        db: Session, 
        test_user_id
    ):
        """Test movement creation with invalid stock code"""
        service = StockMovementService(db)
        
        with pytest.raises(Exception):  # Should raise HTTPException
            service.create_stock_receipt(
                stock_code="INVALID",
                quantity=Decimal("10"),
                unit_cost=Decimal("25.00"),
                reference="PO001",
                user_id=test_user_id
            )

    def test_create_movement_zero_quantity(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test movement creation with zero quantity"""
        service = StockMovementService(db)
        
        with pytest.raises(Exception):  # Should raise HTTPException
            service.create_stock_receipt(
                stock_code=sample_stock_item.stock_code,
                quantity=Decimal("0"),
                unit_cost=Decimal("25.00"),
                reference="PO001",
                user_id=test_user_id
            )

    def test_get_stock_movements_by_item(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test getting stock movements for a specific item"""
        service = StockMovementService(db)
        
        # Create a movement first
        service.create_stock_receipt(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("50"),
            unit_cost=Decimal("25.00"),
            reference="PO001",
            user_id=test_user_id
        )
        
        movements = service.get_movements_by_stock_code(
            sample_stock_item.stock_code,
            page=1,
            page_size=10
        )
        
        assert "movements" in movements
        assert "total_count" in movements
        assert movements["total_count"] >= 1
        assert len(movements["movements"]) >= 1

    def test_get_movements_by_date_range(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test getting movements by date range"""
        service = StockMovementService(db)
        
        # Create a movement first
        service.create_stock_receipt(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("50"),
            unit_cost=Decimal("25.00"),
            reference="PO001",
            user_id=test_user_id
        )
        
        movements = service.get_movements_by_date_range(
            start_date=date.today(),
            end_date=date.today(),
            page=1,
            page_size=10
        )
        
        assert "movements" in movements
        assert "total_count" in movements
        assert movements["total_count"] >= 1

    def test_reverse_stock_movement(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test reversing a stock movement"""
        service = StockMovementService(db)
        
        # Create original movement
        original_movement = service.create_stock_receipt(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("50"),
            unit_cost=Decimal("25.00"),
            reference="PO001",
            user_id=test_user_id
        )
        
        # Reverse the movement
        reversal = service.reverse_movement(
            original_movement.id,
            reason="Incorrect receipt",
            user_id=test_user_id
        )
        
        assert reversal is not None
        assert reversal.quantity == Decimal("-50")  # Opposite of original
        assert reversal.movement_type == MovementType.REVERSAL
        assert reversal.original_movement_id == original_movement.id
        assert reversal.movement_status == MovementStatus.CONFIRMED

    def test_calculate_running_balance(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test running balance calculation"""
        service = StockMovementService(db)
        
        # Create multiple movements
        service.create_stock_receipt(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("100"),
            unit_cost=Decimal("25.00"),
            reference="PO001",
            user_id=test_user_id
        )
        
        service.create_stock_issue(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("30"),
            reference="SO001",
            user_id=test_user_id
        )
        
        service.create_stock_adjustment(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("-5"),
            reason_code="DAMAGE",
            user_id=test_user_id
        )
        
        # Calculate running balance
        balance = service.calculate_running_balance(sample_stock_item.stock_code)
        
        # Original: 100, Receipt: +100, Issue: -30, Adjustment: -5 = 165
        expected_balance = Decimal("165")  # 100 (original) + 100 - 30 - 5
        assert balance == expected_balance

    def test_get_movement_summary(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test getting movement summary statistics"""
        service = StockMovementService(db)
        
        # Create various movements
        service.create_stock_receipt(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("100"),
            unit_cost=Decimal("25.00"),
            reference="PO001",
            user_id=test_user_id
        )
        
        service.create_stock_issue(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("30"),
            reference="SO001",
            user_id=test_user_id
        )
        
        summary = service.get_movement_summary(
            stock_code=sample_stock_item.stock_code,
            start_date=date.today(),
            end_date=date.today()
        )
        
        assert "total_receipts" in summary
        assert "total_issues" in summary
        assert "total_adjustments" in summary
        assert "net_movement" in summary
        assert summary["total_receipts"] == Decimal("100")
        assert summary["total_issues"] == Decimal("30")

    def test_validate_stock_availability(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test stock availability validation"""
        service = StockMovementService(db)
        
        # Test with sufficient stock
        is_available = service.validate_stock_availability(
            sample_stock_item.stock_code,
            Decimal("50")  # Less than available (100)
        )
        assert is_available is True
        
        # Test with insufficient stock
        is_available = service.validate_stock_availability(
            sample_stock_item.stock_code,
            Decimal("150")  # More than available (100)
        )
        assert is_available is False

    def test_batch_stock_movements(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test processing batch stock movements"""
        service = StockMovementService(db)
        
        movements_data = [
            {
                "stock_code": sample_stock_item.stock_code,
                "movement_type": "RECEIPT",
                "quantity": "50",
                "unit_cost": "25.00",
                "reference": "BATCH001"
            },
            {
                "stock_code": sample_stock_item.stock_code,
                "movement_type": "ISSUE", 
                "quantity": "20",
                "reference": "BATCH001"
            }
        ]
        
        result = service.process_batch_movements(
            movements_data,
            user_id=test_user_id
        )
        
        assert "processed_count" in result
        assert "failed_count" in result
        assert "movements" in result
        assert result["processed_count"] == 2
        assert result["failed_count"] == 0
        assert len(result["movements"]) == 2