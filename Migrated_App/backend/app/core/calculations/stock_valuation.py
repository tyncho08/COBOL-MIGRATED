"""
Stock Valuation Calculation Engine
Migrated from ACAS st030.cbl (433 procedures)
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from enum import Enum
from collections import deque


class ValuationMethod(str, Enum):
    """Stock valuation methods from COBOL"""
    FIFO = "FIFO"              # First In, First Out
    LIFO = "LIFO"              # Last In, First Out
    AVERAGE = "AVERAGE"        # Weighted Average Cost
    STANDARD = "STANDARD"      # Standard Cost
    REPLACEMENT = "REPLACEMENT" # Current Market Value


class StockMovement:
    """Represents a stock movement for valuation"""
    def __init__(self, date: date, quantity: Decimal, unit_cost: Decimal, 
                 movement_type: str, reference: str):
        self.date = date
        self.quantity = Decimal(str(quantity))
        self.unit_cost = Decimal(str(unit_cost))
        self.movement_type = movement_type  # RECEIPT, ISSUE, ADJUSTMENT
        self.reference = reference
        self.remaining_qty = self.quantity if movement_type == "RECEIPT" else Decimal("0")


class StockValuationCalculator:
    """
    Stock valuation engine preserving COBOL logic from st030.cbl
    Handles FIFO, LIFO, Average, and Standard costing methods
    """
    
    @staticmethod
    def calculate_fifo_cost(
        movements: List[StockMovement],
        quantity_to_value: Decimal
    ) -> Tuple[Decimal, List[Dict]]:
        """
        Calculate FIFO cost for given quantity
        
        Args:
            movements: List of stock movements (receipts)
            quantity_to_value: Quantity to calculate cost for
            
        Returns:
            Tuple of (total_cost, cost_breakdown)
        """
        quantity_to_value = Decimal(str(quantity_to_value))
        total_cost = Decimal("0.00")
        cost_breakdown = []
        remaining_qty = quantity_to_value
        
        # Sort by date (oldest first for FIFO)
        sorted_movements = sorted(
            [m for m in movements if m.movement_type == "RECEIPT" and m.remaining_qty > 0],
            key=lambda x: x.date
        )
        
        for movement in sorted_movements:
            if remaining_qty <= 0:
                break
                
            qty_from_this_batch = min(movement.remaining_qty, remaining_qty)
            batch_cost = qty_from_this_batch * movement.unit_cost
            
            total_cost += batch_cost
            cost_breakdown.append({
                "date": movement.date,
                "quantity": qty_from_this_batch,
                "unit_cost": movement.unit_cost,
                "total_cost": batch_cost,
                "reference": movement.reference
            })
            
            remaining_qty -= qty_from_this_batch
        
        return total_cost.quantize(Decimal("0.01"), ROUND_HALF_UP), cost_breakdown
    
    @staticmethod
    def calculate_lifo_cost(
        movements: List[StockMovement],
        quantity_to_value: Decimal
    ) -> Tuple[Decimal, List[Dict]]:
        """
        Calculate LIFO cost for given quantity
        
        Args:
            movements: List of stock movements (receipts)
            quantity_to_value: Quantity to calculate cost for
            
        Returns:
            Tuple of (total_cost, cost_breakdown)
        """
        quantity_to_value = Decimal(str(quantity_to_value))
        total_cost = Decimal("0.00")
        cost_breakdown = []
        remaining_qty = quantity_to_value
        
        # Sort by date (newest first for LIFO)
        sorted_movements = sorted(
            [m for m in movements if m.movement_type == "RECEIPT" and m.remaining_qty > 0],
            key=lambda x: x.date,
            reverse=True
        )
        
        for movement in sorted_movements:
            if remaining_qty <= 0:
                break
                
            qty_from_this_batch = min(movement.remaining_qty, remaining_qty)
            batch_cost = qty_from_this_batch * movement.unit_cost
            
            total_cost += batch_cost
            cost_breakdown.append({
                "date": movement.date,
                "quantity": qty_from_this_batch,
                "unit_cost": movement.unit_cost,
                "total_cost": batch_cost,
                "reference": movement.reference
            })
            
            remaining_qty -= qty_from_this_batch
        
        return total_cost.quantize(Decimal("0.01"), ROUND_HALF_UP), cost_breakdown
    
    @staticmethod
    def calculate_average_cost(
        current_qty: Decimal,
        current_value: Decimal,
        receipt_qty: Decimal,
        receipt_cost: Decimal
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate weighted average cost after a receipt
        Based on COBOL formula from st030.cbl
        
        Args:
            current_qty: Current stock quantity
            current_value: Current stock value
            receipt_qty: Quantity received
            receipt_cost: Unit cost of receipt
            
        Returns:
            Tuple of (new_average_cost, new_total_value)
        """
        current_qty = Decimal(str(current_qty))
        current_value = Decimal(str(current_value))
        receipt_qty = Decimal(str(receipt_qty))
        receipt_cost = Decimal(str(receipt_cost))
        
        # Calculate new totals
        new_qty = current_qty + receipt_qty
        receipt_value = receipt_qty * receipt_cost
        new_value = current_value + receipt_value
        
        # Calculate new average (avoid division by zero)
        if new_qty > 0:
            new_average = (new_value / new_qty).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
        else:
            new_average = Decimal("0.0000")
        
        return new_average, new_value.quantize(Decimal("0.01"), ROUND_HALF_UP)
    
    @staticmethod
    def process_stock_movement(
        movement_type: str,
        quantity: Decimal,
        unit_cost: Decimal,
        current_stock: Dict[str, Decimal],
        valuation_method: ValuationMethod
    ) -> Dict[str, Decimal]:
        """
        Process a stock movement and update values
        Implements COBOL logic for stock updates
        
        Args:
            movement_type: RECEIPT, ISSUE, or ADJUSTMENT
            quantity: Movement quantity
            unit_cost: Unit cost (for receipts)
            current_stock: Current stock status dict
            valuation_method: Valuation method to use
            
        Returns:
            Updated stock status dict
        """
        quantity = Decimal(str(quantity))
        unit_cost = Decimal(str(unit_cost))
        
        result = current_stock.copy()
        
        if movement_type == "RECEIPT":
            # Update quantities
            result["quantity_on_hand"] = current_stock["quantity_on_hand"] + quantity
            result["ytd_receipts"] = current_stock.get("ytd_receipts", Decimal("0")) + quantity
            
            # Update costs based on method
            if valuation_method == ValuationMethod.AVERAGE:
                new_avg, new_value = StockValuationCalculator.calculate_average_cost(
                    current_stock["quantity_on_hand"],
                    current_stock.get("stock_value", Decimal("0")),
                    quantity,
                    unit_cost
                )
                result["average_cost"] = new_avg
                result["stock_value"] = new_value
            elif valuation_method == ValuationMethod.STANDARD:
                # Standard cost doesn't change with receipts
                result["stock_value"] = result["quantity_on_hand"] * current_stock["standard_cost"]
            else:
                # For FIFO/LIFO, just track the movement
                result["last_cost"] = unit_cost
                
        elif movement_type == "ISSUE":
            # Update quantities
            result["quantity_on_hand"] = current_stock["quantity_on_hand"] - quantity
            result["ytd_issues"] = current_stock.get("ytd_issues", Decimal("0")) + quantity
            
            # Update value based on method
            if valuation_method == ValuationMethod.AVERAGE:
                issue_value = quantity * current_stock["average_cost"]
                result["stock_value"] = current_stock["stock_value"] - issue_value
            elif valuation_method == ValuationMethod.STANDARD:
                result["stock_value"] = result["quantity_on_hand"] * current_stock["standard_cost"]
                
        elif movement_type == "ADJUSTMENT":
            # Adjustments can be positive or negative
            result["quantity_on_hand"] = current_stock["quantity_on_hand"] + quantity
            result["ytd_adjustments"] = current_stock.get("ytd_adjustments", Decimal("0")) + quantity
            
            # Recalculate value
            if valuation_method == ValuationMethod.AVERAGE:
                # Adjustment at current average cost
                adj_value = quantity * current_stock["average_cost"]
                result["stock_value"] = current_stock["stock_value"] + adj_value
            elif valuation_method == ValuationMethod.STANDARD:
                result["stock_value"] = result["quantity_on_hand"] * current_stock["standard_cost"]
        
        # Ensure non-negative stock value
        if result["stock_value"] < 0:
            result["stock_value"] = Decimal("0.00")
            
        return result
    
    @staticmethod
    def calculate_stock_valuation_report(
        stock_items: List[Dict],
        valuation_date: date,
        include_zero_stock: bool = False
    ) -> Dict[str, any]:
        """
        Generate stock valuation report like COBOL st030
        
        Args:
            stock_items: List of stock item dictionaries
            valuation_date: Date for valuation
            include_zero_stock: Include items with zero quantity
            
        Returns:
            Valuation report dictionary
        """
        report = {
            "valuation_date": valuation_date,
            "total_items": 0,
            "total_quantity": Decimal("0.000"),
            "total_value": Decimal("0.00"),
            "categories": {},
            "items": []
        }
        
        for item in stock_items:
            qty = Decimal(str(item.get("quantity_on_hand", 0)))
            
            # Skip zero stock if not included
            if not include_zero_stock and qty <= 0:
                continue
            
            # Calculate value based on valuation method
            method = item.get("valuation_method", ValuationMethod.AVERAGE)
            if method == ValuationMethod.AVERAGE:
                value = qty * Decimal(str(item.get("average_cost", 0)))
            elif method == ValuationMethod.STANDARD:
                value = qty * Decimal(str(item.get("standard_cost", 0)))
            elif method == ValuationMethod.REPLACEMENT:
                value = qty * Decimal(str(item.get("replacement_cost", 0)))
            else:
                # For FIFO/LIFO, use the stored stock value
                value = Decimal(str(item.get("stock_value", 0)))
            
            value = value.quantize(Decimal("0.01"), ROUND_HALF_UP)
            
            # Add to report
            report["total_items"] += 1
            report["total_quantity"] += qty
            report["total_value"] += value
            
            # Category subtotals
            category = item.get("category_code", "UNCATEGORIZED")
            if category not in report["categories"]:
                report["categories"][category] = {
                    "item_count": 0,
                    "total_quantity": Decimal("0.000"),
                    "total_value": Decimal("0.00")
                }
            
            report["categories"][category]["item_count"] += 1
            report["categories"][category]["total_quantity"] += qty
            report["categories"][category]["total_value"] += value
            
            # Item details
            report["items"].append({
                "stock_code": item.get("stock_code"),
                "description": item.get("description"),
                "quantity": qty,
                "unit_cost": item.get(f"{method.lower()}_cost", Decimal("0.00")),
                "total_value": value,
                "valuation_method": method,
                "category": category
            })
        
        return report
    
    @staticmethod
    def revalue_stock(
        current_value: Decimal,
        current_qty: Decimal,
        new_unit_cost: Decimal,
        revaluation_method: str = "TOTAL"
    ) -> Tuple[Decimal, Decimal]:
        """
        Revalue stock for period-end or cost changes
        
        Args:
            current_value: Current total stock value
            current_qty: Current quantity
            new_unit_cost: New unit cost for revaluation
            revaluation_method: TOTAL (replace) or VARIANCE (adjust)
            
        Returns:
            Tuple of (new_value, variance)
        """
        current_value = Decimal(str(current_value))
        current_qty = Decimal(str(current_qty))
        new_unit_cost = Decimal(str(new_unit_cost))
        
        if revaluation_method == "TOTAL":
            # Complete revaluation
            new_value = (current_qty * new_unit_cost).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )
            variance = new_value - current_value
        else:
            # Variance adjustment only
            target_value = (current_qty * new_unit_cost).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )
            variance = target_value - current_value
            new_value = current_value + variance
        
        return new_value, variance