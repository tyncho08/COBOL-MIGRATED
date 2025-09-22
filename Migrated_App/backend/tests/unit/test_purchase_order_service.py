"""
Unit tests for Purchase Order Service
Tests the core business logic migrated from COBOL pl800.cbl, pl810.cbl, pl900.cbl
"""
import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.services.purchase_ledger.purchase_order_service import PurchaseOrderService
from app.models.purchase_transactions import PurchaseOrder, PurchaseOrderStatus


class TestPurchaseOrderService:
    """Test Purchase Order Service functionality"""

    def test_create_purchase_order_success(
        self, 
        db: Session, 
        sample_supplier, 
        test_user_id
    ):
        """Test successful purchase order creation"""
        service = PurchaseOrderService(db)
        
        order_lines = [
            {
                "stock_code": "TEST001",
                "description": "Test Item",
                "quantity_ordered": Decimal("10"),
                "unit_cost": Decimal("50.00"),
                "discount_percent": Decimal("5")
            }
        ]
        
        order = service.create_purchase_order(
            supplier_code=sample_supplier.supplier_code,
            order_lines=order_lines,
            user_id=test_user_id
        )
        
        assert order is not None
        assert order.supplier_code == sample_supplier.supplier_code
        assert order.order_status == PurchaseOrderStatus.PENDING
        assert order.gross_amount == Decimal("475.00")  # 10 * 50 * 0.95
        assert order.net_amount > order.gross_amount  # Includes VAT
        assert len(order.order_lines) == 1

    def test_create_purchase_order_invalid_supplier(
        self, 
        db: Session, 
        test_user_id
    ):
        """Test purchase order creation with invalid supplier"""
        service = PurchaseOrderService(db)
        
        order_lines = [
            {
                "stock_code": "TEST001",
                "description": "Test Item",
                "quantity_ordered": Decimal("10"),
                "unit_cost": Decimal("50.00")
            }
        ]
        
        with pytest.raises(Exception):  # Should raise HTTPException
            service.create_purchase_order(
                supplier_code="INVALID",
                order_lines=order_lines,
                user_id=test_user_id
            )

    def test_create_purchase_order_empty_lines(
        self, 
        db: Session, 
        sample_supplier, 
        test_user_id
    ):
        """Test purchase order creation with empty order lines"""
        service = PurchaseOrderService(db)
        
        with pytest.raises(Exception):  # Should raise HTTPException
            service.create_purchase_order(
                supplier_code=sample_supplier.supplier_code,
                order_lines=[],
                user_id=test_user_id
            )

    def test_authorize_purchase_order(
        self, 
        db: Session, 
        sample_purchase_order, 
        test_user_id
    ):
        """Test purchase order authorization"""
        service = PurchaseOrderService(db)
        
        # Authorize the order
        authorized_order = service.authorize_order(
            sample_purchase_order.id, 
            test_user_id
        )
        
        assert authorized_order.order_status == PurchaseOrderStatus.APPROVED
        assert authorized_order.authorized_by == str(test_user_id)
        assert authorized_order.authorized_date is not None

    def test_authorize_already_authorized_order(
        self, 
        db: Session, 
        sample_purchase_order, 
        test_user_id
    ):
        """Test authorization of already authorized order"""
        service = PurchaseOrderService(db)
        
        # First authorization
        service.authorize_order(sample_purchase_order.id, test_user_id)
        
        # Second authorization should fail
        with pytest.raises(Exception):
            service.authorize_order(sample_purchase_order.id, test_user_id)

    def test_cancel_purchase_order(
        self, 
        db: Session, 
        sample_purchase_order, 
        test_user_id
    ):
        """Test purchase order cancellation"""
        service = PurchaseOrderService(db)
        
        cancellation_reason = "Order no longer required"
        cancelled_order = service.cancel_order(
            sample_purchase_order.id, 
            cancellation_reason, 
            test_user_id
        )
        
        assert cancelled_order.order_status == PurchaseOrderStatus.CANCELLED
        assert cancelled_order.cancellation_reason == cancellation_reason
        assert cancelled_order.cancelled_by == str(test_user_id)
        assert cancelled_order.cancelled_date is not None

    def test_get_purchase_order(
        self, 
        db: Session, 
        sample_purchase_order
    ):
        """Test getting purchase order by ID"""
        service = PurchaseOrderService(db)
        
        order = service.get_purchase_order(sample_purchase_order.id)
        
        assert order is not None
        assert order.id == sample_purchase_order.id
        assert order.order_number == sample_purchase_order.order_number

    def test_get_nonexistent_purchase_order(self, db: Session):
        """Test getting non-existent purchase order"""
        service = PurchaseOrderService(db)
        
        order = service.get_purchase_order(99999)
        
        assert order is None

    def test_search_purchase_orders(
        self, 
        db: Session, 
        sample_purchase_order
    ):
        """Test searching purchase orders"""
        service = PurchaseOrderService(db)
        
        result = service.search_purchase_orders(
            supplier_code=sample_purchase_order.supplier_code,
            page=1,
            page_size=10
        )
        
        assert "orders" in result
        assert "total_count" in result
        assert result["total_count"] >= 1
        assert len(result["orders"]) >= 1

    def test_update_purchase_order(
        self, 
        db: Session, 
        sample_purchase_order, 
        test_user_id
    ):
        """Test updating purchase order"""
        service = PurchaseOrderService(db)
        
        updates = {
            "delivery_address": "Updated delivery address",
            "notes": "Updated notes"
        }
        
        updated_order = service.update_purchase_order(
            sample_purchase_order.id,
            updates,
            test_user_id
        )
        
        assert updated_order.delivery_address == "Updated delivery address"
        assert updated_order.notes == "Updated notes"
        assert updated_order.updated_by == str(test_user_id)

    def test_calculate_order_totals(
        self, 
        db: Session, 
        sample_supplier
    ):
        """Test order total calculations"""
        service = PurchaseOrderService(db)
        
        order_lines = [
            {
                "stock_code": "TEST001",
                "description": "Test Item 1",
                "quantity_ordered": Decimal("10"),
                "unit_cost": Decimal("100.00"),
                "discount_percent": Decimal("10")  # 10% discount
            },
            {
                "stock_code": "TEST002",
                "description": "Test Item 2",
                "quantity_ordered": Decimal("5"),
                "unit_cost": Decimal("200.00"),
                "discount_percent": Decimal("0")  # No discount
            }
        ]
        
        order = service.create_purchase_order(
            supplier_code=sample_supplier.supplier_code,
            order_lines=order_lines,
            user_id=1
        )
        
        # Calculate expected totals
        # Item 1: 10 * 100 * 0.9 = 900
        # Item 2: 5 * 200 = 1000
        # Gross total: 1900
        expected_gross = Decimal("1900.00")
        
        assert order.gross_amount == expected_gross
        assert order.vat_amount > 0  # Should have VAT
        assert order.net_amount == order.gross_amount + order.vat_amount

    def test_purchase_order_workflow_complete(
        self, 
        db: Session, 
        sample_supplier, 
        test_user_id
    ):
        """Test complete purchase order workflow"""
        service = PurchaseOrderService(db)
        
        # 1. Create order
        order_lines = [
            {
                "stock_code": "TEST001",
                "description": "Test Item",
                "quantity_ordered": Decimal("10"),
                "unit_cost": Decimal("50.00")
            }
        ]
        
        order = service.create_purchase_order(
            supplier_code=sample_supplier.supplier_code,
            order_lines=order_lines,
            user_id=test_user_id
        )
        
        assert order.order_status == PurchaseOrderStatus.PENDING
        
        # 2. Authorize order
        authorized_order = service.authorize_order(order.id, test_user_id)
        assert authorized_order.order_status == PurchaseOrderStatus.APPROVED
        
        # 3. Update order
        updates = {"notes": "Order has been approved and sent to supplier"}
        updated_order = service.update_purchase_order(
            order.id, 
            updates, 
            test_user_id
        )
        
        assert updated_order.notes == "Order has been approved and sent to supplier"
        assert updated_order.order_status == PurchaseOrderStatus.APPROVED