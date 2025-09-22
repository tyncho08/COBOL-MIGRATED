"""
Unit tests for Stock Valuation Service
Tests the core business logic migrated from COBOL st600.cbl, st610.cbl, st700.cbl
"""
import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.services.stock_control.stock_valuation_service import StockValuationService
from app.models.stock import StockValuation, ValuationMethod


class TestStockValuationService:
    """Test Stock Valuation Service functionality"""

    def test_calculate_fifo_valuation(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test FIFO valuation calculation"""
        service = StockValuationService(db)
        
        # Create stock movements with different costs
        from app.services.stock_control.stock_movement_service import StockMovementService
        movement_service = StockMovementService(db)
        
        # First receipt at $20
        movement_service.create_stock_receipt(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("50"),
            unit_cost=Decimal("20.00"),
            reference="PO001",
            user_id=test_user_id
        )
        
        # Second receipt at $25
        movement_service.create_stock_receipt(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("30"),
            unit_cost=Decimal("25.00"),
            reference="PO002",
            user_id=test_user_id
        )
        
        # Issue 60 units (should take 50 @ $20 + 10 @ $25)
        movement_service.create_stock_issue(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("60"),
            reference="SO001",
            user_id=test_user_id
        )
        
        valuation = service.calculate_fifo_valuation(
            sample_stock_item.stock_code,
            date.today()
        )
        
        # Remaining: 20 units @ $25 + original 100 units @ $30 = $500 + $3000 = $3500
        # Plus remaining 20 units from second receipt @ $25 = $500
        # Total should be calculated based on FIFO logic
        assert valuation is not None
        assert valuation["method"] == "FIFO"
        assert valuation["total_quantity"] > 0
        assert valuation["total_value"] > 0
        assert valuation["average_cost"] > 0

    def test_calculate_lifo_valuation(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test LIFO valuation calculation"""
        service = StockValuationService(db)
        
        # Create stock movements with different costs
        from app.services.stock_control.stock_movement_service import StockMovementService
        movement_service = StockMovementService(db)
        
        # First receipt at $20
        movement_service.create_stock_receipt(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("50"),
            unit_cost=Decimal("20.00"),
            reference="PO001",
            user_id=test_user_id
        )
        
        # Second receipt at $25
        movement_service.create_stock_receipt(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("30"),
            unit_cost=Decimal("25.00"),
            reference="PO002",
            user_id=test_user_id
        )
        
        # Issue 60 units (LIFO: should take 30 @ $25 + 30 @ $20)
        movement_service.create_stock_issue(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("60"),
            reference="SO001",
            user_id=test_user_id
        )
        
        valuation = service.calculate_lifo_valuation(
            sample_stock_item.stock_code,
            date.today()
        )
        
        assert valuation is not None
        assert valuation["method"] == "LIFO"
        assert valuation["total_quantity"] > 0
        assert valuation["total_value"] > 0
        assert valuation["average_cost"] > 0

    def test_calculate_average_cost_valuation(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test Average Cost valuation calculation"""
        service = StockValuationService(db)
        
        # Create stock movements
        from app.services.stock_control.stock_movement_service import StockMovementService
        movement_service = StockMovementService(db)
        
        # Receipt at $20
        movement_service.create_stock_receipt(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("50"),
            unit_cost=Decimal("20.00"),
            reference="PO001",
            user_id=test_user_id
        )
        
        # Receipt at $30
        movement_service.create_stock_receipt(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("50"),
            unit_cost=Decimal("30.00"),
            reference="PO002",
            user_id=test_user_id
        )
        
        valuation = service.calculate_average_cost_valuation(
            sample_stock_item.stock_code,
            date.today()
        )
        
        assert valuation is not None
        assert valuation["method"] == "AVERAGE"
        assert valuation["total_quantity"] > 0
        assert valuation["total_value"] > 0
        # Average cost should be calculated correctly
        assert valuation["average_cost"] > Decimal("20.00")
        assert valuation["average_cost"] < Decimal("30.00")

    def test_calculate_standard_cost_valuation(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test Standard Cost valuation calculation"""
        service = StockValuationService(db)
        
        # Update standard cost
        sample_stock_item.unit_cost = Decimal("25.00")
        db.commit()
        
        # Create movements
        from app.services.stock_control.stock_movement_service import StockMovementService
        movement_service = StockMovementService(db)
        
        movement_service.create_stock_receipt(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("50"),
            unit_cost=Decimal("20.00"),  # Actual cost different from standard
            reference="PO001",
            user_id=test_user_id
        )
        
        valuation = service.calculate_standard_cost_valuation(
            sample_stock_item.stock_code,
            date.today()
        )
        
        assert valuation is not None
        assert valuation["method"] == "STANDARD"
        assert valuation["total_quantity"] > 0
        assert valuation["average_cost"] == Decimal("25.00")  # Should use standard cost

    def test_create_valuation_snapshot(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test creating valuation snapshot"""
        service = StockValuationService(db)
        
        snapshot = service.create_valuation_snapshot(
            valuation_date=date.today(),
            method=ValuationMethod.AVERAGE,
            stock_codes=[sample_stock_item.stock_code],
            user_id=test_user_id
        )
        
        assert snapshot is not None
        assert len(snapshot["valuations"]) >= 1
        assert snapshot["total_value"] > 0
        assert snapshot["method"] == "AVERAGE"

    def test_get_valuation_history(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test getting valuation history"""
        service = StockValuationService(db)
        
        # Create a snapshot first
        service.create_valuation_snapshot(
            valuation_date=date.today(),
            method=ValuationMethod.AVERAGE,
            stock_codes=[sample_stock_item.stock_code],
            user_id=test_user_id
        )
        
        history = service.get_valuation_history(
            stock_code=sample_stock_item.stock_code,
            start_date=date.today(),
            end_date=date.today()
        )
        
        assert "valuations" in history
        assert len(history["valuations"]) >= 1

    def test_compare_valuation_methods(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test comparing different valuation methods"""
        service = StockValuationService(db)
        
        # Create movements with varying costs
        from app.services.stock_control.stock_movement_service import StockMovementService
        movement_service = StockMovementService(db)
        
        movement_service.create_stock_receipt(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("50"),
            unit_cost=Decimal("20.00"),
            reference="PO001",
            user_id=test_user_id
        )
        
        movement_service.create_stock_receipt(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("50"),
            unit_cost=Decimal("30.00"),
            reference="PO002",
            user_id=test_user_id
        )
        
        comparison = service.compare_valuation_methods(
            sample_stock_item.stock_code,
            date.today()
        )
        
        assert "FIFO" in comparison
        assert "LIFO" in comparison
        assert "AVERAGE" in comparison
        assert "STANDARD" in comparison
        
        # Each method should return valuation data
        for method, valuation in comparison.items():
            assert "total_value" in valuation
            assert "average_cost" in valuation
            assert "total_quantity" in valuation

    def test_calculate_valuation_variance(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test calculating valuation variance"""
        service = StockValuationService(db)
        
        # Set standard cost
        sample_stock_item.unit_cost = Decimal("25.00")
        db.commit()
        
        # Create movements at different costs
        from app.services.stock_control.stock_movement_service import StockMovementService
        movement_service = StockMovementService(db)
        
        movement_service.create_stock_receipt(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("100"),
            unit_cost=Decimal("23.00"),  # Below standard
            reference="PO001",
            user_id=test_user_id
        )
        
        variance = service.calculate_valuation_variance(
            sample_stock_item.stock_code,
            date.today()
        )
        
        assert variance is not None
        assert "standard_value" in variance
        assert "actual_value" in variance
        assert "variance_amount" in variance
        assert "variance_percent" in variance
        
        # Should show favorable variance (actual < standard)
        assert variance["variance_amount"] < 0

    def test_generate_valuation_report(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test generating comprehensive valuation report"""
        service = StockValuationService(db)
        
        report = service.generate_valuation_report(
            valuation_date=date.today(),
            method=ValuationMethod.AVERAGE,
            category_filter=sample_stock_item.category_code,
            location_filter=sample_stock_item.location
        )
        
        assert report is not None
        assert "summary" in report
        assert "items" in report
        assert "totals" in report
        
        assert report["summary"]["method"] == "AVERAGE"
        assert report["summary"]["valuation_date"] == date.today().isoformat()
        assert len(report["items"]) >= 1

    def test_update_standard_costs(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test updating standard costs"""
        service = StockValuationService(db)
        
        # Update standard cost
        result = service.update_standard_cost(
            stock_code=sample_stock_item.stock_code,
            new_standard_cost=Decimal("35.00"),
            effective_date=date.today(),
            reason="Annual cost review",
            user_id=test_user_id
        )
        
        assert result is not None
        assert result["old_cost"] == Decimal("30.00")  # From sample data
        assert result["new_cost"] == Decimal("35.00")
        assert result["effective_date"] == date.today()

    def test_calculate_obsolete_stock_value(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test calculating obsolete stock value"""
        service = StockValuationService(db)
        
        # Create old movements to simulate obsolete stock
        from app.services.stock_control.stock_movement_service import StockMovementService
        movement_service = StockMovementService(db)
        
        movement_service.create_stock_receipt(
            stock_code=sample_stock_item.stock_code,
            quantity=Decimal("50"),
            unit_cost=Decimal("25.00"),
            reference="OLD001",
            user_id=test_user_id
        )
        
        obsolete_analysis = service.calculate_obsolete_stock_value(
            cutoff_days=30,
            minimum_value_threshold=Decimal("100.00")
        )
        
        assert "total_obsolete_value" in obsolete_analysis
        assert "obsolete_items" in obsolete_analysis
        assert "analysis_date" in obsolete_analysis

    def test_revalue_stock_batch(
        self, 
        db: Session, 
        sample_stock_item, 
        test_user_id
    ):
        """Test batch stock revaluation"""
        service = StockValuationService(db)
        
        revaluation_data = [
            {
                "stock_code": sample_stock_item.stock_code,
                "new_unit_cost": "28.00",
                "reason": "Market price adjustment"
            }
        ]
        
        result = service.revalue_stock_batch(
            revaluation_data,
            effective_date=date.today(),
            user_id=test_user_id
        )
        
        assert "processed_count" in result
        assert "failed_count" in result
        assert "revaluations" in result
        assert result["processed_count"] == 1
        assert result["failed_count"] == 0