"""
Integration tests for Purchase Order API endpoints
Tests the complete API workflow from HTTP requests to database operations
"""
import pytest
from decimal import Decimal
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.purchase_transactions import PurchaseOrderStatus


class TestPurchaseOrderAPI:
    """Test Purchase Order API endpoints"""

    def test_create_purchase_order_success(
        self, 
        client: TestClient, 
        sample_supplier
    ):
        """Test successful purchase order creation via API"""
        order_data = {
            "supplier_code": sample_supplier.supplier_code,
            "order_date": date.today().isoformat(),
            "delivery_date": date.today().isoformat(),
            "delivery_address": "123 Test Street",
            "notes": "Test purchase order",
            "order_lines": [
                {
                    "stock_code": "TEST001",
                    "description": "Test Item",
                    "quantity_ordered": 10,
                    "unit_cost": 50.00,
                    "discount_percent": 5
                }
            ]
        }
        
        response = client.post("/api/v1/purchase-orders/", json=order_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["supplier_code"] == sample_supplier.supplier_code
        assert data["order_status"] == PurchaseOrderStatus.PENDING.value
        assert len(data["order_lines"]) == 1
        assert data["gross_amount"] == "475.00"  # 10 * 50 * 0.95

    def test_create_purchase_order_invalid_supplier(
        self, 
        client: TestClient
    ):
        """Test purchase order creation with invalid supplier"""
        order_data = {
            "supplier_code": "INVALID",
            "order_date": date.today().isoformat(),
            "order_lines": [
                {
                    "stock_code": "TEST001",
                    "description": "Test Item",
                    "quantity_ordered": 10,
                    "unit_cost": 50.00
                }
            ]
        }
        
        response = client.post("/api/v1/purchase-orders/", json=order_data)
        
        assert response.status_code == 404
        assert "Supplier not found" in response.json()["detail"]

    def test_create_purchase_order_empty_lines(
        self, 
        client: TestClient, 
        sample_supplier
    ):
        """Test purchase order creation with empty order lines"""
        order_data = {
            "supplier_code": sample_supplier.supplier_code,
            "order_date": date.today().isoformat(),
            "order_lines": []
        }
        
        response = client.post("/api/v1/purchase-orders/", json=order_data)
        
        assert response.status_code == 422
        assert "Order must have at least one line" in response.json()["detail"]

    def test_get_purchase_order_success(
        self, 
        client: TestClient, 
        sample_purchase_order
    ):
        """Test getting purchase order by ID"""
        response = client.get(f"/api/v1/purchase-orders/{sample_purchase_order.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_purchase_order.id
        assert data["order_number"] == sample_purchase_order.order_number
        assert data["supplier_code"] == sample_purchase_order.supplier_code

    def test_get_purchase_order_not_found(
        self, 
        client: TestClient
    ):
        """Test getting non-existent purchase order"""
        response = client.get("/api/v1/purchase-orders/99999")
        
        assert response.status_code == 404
        assert "Purchase order not found" in response.json()["detail"]

    def test_update_purchase_order_success(
        self, 
        client: TestClient, 
        sample_purchase_order
    ):
        """Test updating purchase order"""
        update_data = {
            "delivery_address": "Updated delivery address",
            "notes": "Updated notes"
        }
        
        response = client.patch(
            f"/api/v1/purchase-orders/{sample_purchase_order.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["delivery_address"] == "Updated delivery address"
        assert data["notes"] == "Updated notes"

    def test_authorize_purchase_order_success(
        self, 
        client: TestClient, 
        sample_purchase_order
    ):
        """Test authorizing purchase order"""
        response = client.post(
            f"/api/v1/purchase-orders/{sample_purchase_order.id}/authorize"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["order_status"] == PurchaseOrderStatus.APPROVED.value
        assert data["authorized_date"] is not None

    def test_authorize_already_authorized_order(
        self, 
        client: TestClient, 
        sample_purchase_order
    ):
        """Test authorizing already authorized order"""
        # First authorization
        client.post(f"/api/v1/purchase-orders/{sample_purchase_order.id}/authorize")
        
        # Second authorization should fail
        response = client.post(
            f"/api/v1/purchase-orders/{sample_purchase_order.id}/authorize"
        )
        
        assert response.status_code == 400
        assert "already authorized" in response.json()["detail"].lower()

    def test_cancel_purchase_order_success(
        self, 
        client: TestClient, 
        sample_purchase_order
    ):
        """Test cancelling purchase order"""
        cancel_data = {
            "cancellation_reason": "Order no longer required"
        }
        
        response = client.post(
            f"/api/v1/purchase-orders/{sample_purchase_order.id}/cancel",
            json=cancel_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["order_status"] == PurchaseOrderStatus.CANCELLED.value
        assert data["cancellation_reason"] == "Order no longer required"

    def test_search_purchase_orders(
        self, 
        client: TestClient, 
        sample_purchase_order
    ):
        """Test searching purchase orders"""
        response = client.get(
            "/api/v1/purchase-orders/search",
            params={
                "supplier_code": sample_purchase_order.supplier_code,
                "page": 1,
                "page_size": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert "total_count" in data
        assert data["total_count"] >= 1
        assert len(data["orders"]) >= 1

    def test_get_purchase_orders_by_status(
        self, 
        client: TestClient, 
        sample_purchase_order
    ):
        """Test getting purchase orders by status"""
        response = client.get(
            "/api/v1/purchase-orders/by-status",
            params={
                "status": PurchaseOrderStatus.PENDING.value,
                "page": 1,
                "page_size": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert "total_count" in data

    def test_get_purchase_order_statistics(
        self, 
        client: TestClient, 
        sample_purchase_order
    ):
        """Test getting purchase order statistics"""
        response = client.get("/api/v1/purchase-orders/statistics")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_orders" in data
        assert "pending_orders" in data
        assert "approved_orders" in data
        assert "total_value" in data

    def test_export_purchase_orders(
        self, 
        client: TestClient, 
        sample_purchase_order
    ):
        """Test exporting purchase orders"""
        response = client.get(
            "/api/v1/purchase-orders/export",
            params={
                "format": "csv",
                "start_date": date.today().isoformat(),
                "end_date": date.today().isoformat()
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

    def test_purchase_order_workflow_complete(
        self, 
        client: TestClient, 
        sample_supplier
    ):
        """Test complete purchase order workflow via API"""
        # 1. Create order
        order_data = {
            "supplier_code": sample_supplier.supplier_code,
            "order_date": date.today().isoformat(),
            "order_lines": [
                {
                    "stock_code": "TEST001",
                    "description": "Test Item",
                    "quantity_ordered": 10,
                    "unit_cost": 50.00
                }
            ]
        }
        
        create_response = client.post("/api/v1/purchase-orders/", json=order_data)
        assert create_response.status_code == 201
        order_id = create_response.json()["id"]
        
        # 2. Get order details
        get_response = client.get(f"/api/v1/purchase-orders/{order_id}")
        assert get_response.status_code == 200
        assert get_response.json()["order_status"] == PurchaseOrderStatus.PENDING.value
        
        # 3. Update order
        update_data = {"notes": "Order approved for processing"}
        update_response = client.patch(
            f"/api/v1/purchase-orders/{order_id}",
            json=update_data
        )
        assert update_response.status_code == 200
        
        # 4. Authorize order
        auth_response = client.post(f"/api/v1/purchase-orders/{order_id}/authorize")
        assert auth_response.status_code == 200
        assert auth_response.json()["order_status"] == PurchaseOrderStatus.APPROVED.value
        
        # 5. Verify final state
        final_response = client.get(f"/api/v1/purchase-orders/{order_id}")
        assert final_response.status_code == 200
        final_data = final_response.json()
        assert final_data["order_status"] == PurchaseOrderStatus.APPROVED.value
        assert final_data["notes"] == "Order approved for processing"

    def test_purchase_order_pagination(
        self, 
        client: TestClient, 
        sample_supplier
    ):
        """Test purchase order list pagination"""
        # Create multiple orders
        for i in range(5):
            order_data = {
                "supplier_code": sample_supplier.supplier_code,
                "order_date": date.today().isoformat(),
                "order_lines": [
                    {
                        "stock_code": f"TEST{i:03d}",
                        "description": f"Test Item {i}",
                        "quantity_ordered": 10,
                        "unit_cost": 50.00
                    }
                ]
            }
            client.post("/api/v1/purchase-orders/", json=order_data)
        
        # Test pagination
        response = client.get(
            "/api/v1/purchase-orders/search",
            params={"page": 1, "page_size": 3}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) <= 3
        assert data["total_count"] >= 5

    def test_purchase_order_validation_errors(
        self, 
        client: TestClient, 
        sample_supplier
    ):
        """Test various validation errors"""
        # Missing required fields
        invalid_data = {
            "supplier_code": sample_supplier.supplier_code
            # Missing order_date and order_lines
        }
        
        response = client.post("/api/v1/purchase-orders/", json=invalid_data)
        assert response.status_code == 422
        
        # Invalid date format
        invalid_date_data = {
            "supplier_code": sample_supplier.supplier_code,
            "order_date": "invalid-date",
            "order_lines": [
                {
                    "stock_code": "TEST001",
                    "description": "Test Item",
                    "quantity_ordered": 10,
                    "unit_cost": 50.00
                }
            ]
        }
        
        response = client.post("/api/v1/purchase-orders/", json=invalid_date_data)
        assert response.status_code == 422

    def test_concurrent_order_operations(
        self, 
        client: TestClient, 
        sample_purchase_order
    ):
        """Test concurrent operations on same order"""
        # Simulate concurrent authorization attempts
        response1 = client.post(
            f"/api/v1/purchase-orders/{sample_purchase_order.id}/authorize"
        )
        response2 = client.post(
            f"/api/v1/purchase-orders/{sample_purchase_order.id}/authorize"
        )
        
        # One should succeed, one should fail
        success_responses = [r for r in [response1, response2] if r.status_code == 200]
        error_responses = [r for r in [response1, response2] if r.status_code == 400]
        
        assert len(success_responses) == 1
        assert len(error_responses) == 1