"""
Discount Calculation Engine
Migrated from ACAS COBOL discount logic
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional
from enum import Enum
from datetime import date


class DiscountType(str, Enum):
    """Discount types from COBOL system"""
    TRADE = "TRADE"                # Customer-specific percentage
    VOLUME = "VOLUME"              # Quantity-based tiered discount
    SETTLEMENT = "SETTLEMENT"      # Early payment discount
    PROMOTION = "PROMOTION"        # Time-limited special offers
    SPECIAL = "SPECIAL"            # Ad-hoc negotiated discount


class DiscountCalculator:
    """
    Discount calculation engine preserving COBOL logic
    Implements exact calculation methods from ACAS invoicing
    """
    
    @staticmethod
    def calculate_trade_discount(
        gross_amount: Decimal,
        discount_percentage: Decimal
    ) -> tuple[Decimal, Decimal]:
        """
        Calculate trade discount based on COBOL formula:
        multiply work-n by work-d giving work-1
        divide work-1 by 100 giving work-1
        subtract work-1 from WS-Net
        
        Args:
            gross_amount: Amount before discount
            discount_percentage: Discount percentage (stored as 99v99)
            
        Returns:
            Tuple of (discount_amount, net_amount)
        """
        gross_amount = Decimal(str(gross_amount))
        discount_percentage = Decimal(str(discount_percentage))
        
        # COBOL calculation
        discount_amount = (gross_amount * discount_percentage / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        net_amount = gross_amount - discount_amount
        
        return discount_amount, net_amount
    
    @staticmethod
    def calculate_volume_discount(
        unit_price: Decimal,
        quantity: Decimal,
        volume_breaks: List[Dict[str, Decimal]]
    ) -> tuple[Decimal, Decimal, Decimal]:
        """
        Calculate volume discount based on quantity breaks
        
        Args:
            unit_price: Base unit price
            quantity: Order quantity
            volume_breaks: List of {'min_qty': x, 'discount_pct': y}
            
        Returns:
            Tuple of (effective_price, discount_amount, net_amount)
        """
        unit_price = Decimal(str(unit_price))
        quantity = Decimal(str(quantity))
        
        # Find applicable volume discount
        discount_pct = Decimal("0.00")
        for break_point in sorted(volume_breaks, key=lambda x: x['min_qty'], reverse=True):
            if quantity >= break_point['min_qty']:
                discount_pct = break_point['discount_pct']
                break
        
        # Calculate amounts
        gross_amount = unit_price * quantity
        discount_amount = (gross_amount * discount_pct / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        net_amount = gross_amount - discount_amount
        effective_price = net_amount / quantity if quantity > 0 else Decimal("0.00")
        
        return effective_price.quantize(Decimal("0.01")), discount_amount, net_amount
    
    @staticmethod
    def calculate_settlement_discount(
        invoice_amount: Decimal,
        settlement_percentage: Decimal,
        settlement_days: int,
        payment_date: date,
        invoice_date: date
    ) -> tuple[bool, Decimal]:
        """
        Calculate settlement discount for early payment
        
        Args:
            invoice_amount: Total invoice amount
            settlement_percentage: Discount percentage if paid early
            settlement_days: Days within which payment qualifies
            payment_date: Date of payment
            invoice_date: Date of invoice
            
        Returns:
            Tuple of (eligible, discount_amount)
        """
        invoice_amount = Decimal(str(invoice_amount))
        settlement_percentage = Decimal(str(settlement_percentage))
        
        # Check if payment is within settlement period
        days_to_payment = (payment_date - invoice_date).days
        eligible = days_to_payment <= settlement_days
        
        if eligible and settlement_percentage > 0:
            discount_amount = (invoice_amount * settlement_percentage / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            discount_amount = Decimal("0.00")
        
        return eligible, discount_amount
    
    @staticmethod
    def calculate_compound_discount(
        base_amount: Decimal,
        discounts: List[Dict[str, any]],
        compound_method: str = "CASCADE"
    ) -> Dict[str, Decimal]:
        """
        Calculate multiple discounts with proper precedence
        
        Args:
            base_amount: Original amount before any discounts
            discounts: List of discount dictionaries with type and percentage
            compound_method: CASCADE (apply sequentially) or BEST (take highest)
            
        Returns:
            Dict with breakdown of discounts and final amount
        """
        base_amount = Decimal(str(base_amount))
        result = {
            "base_amount": base_amount,
            "total_discount": Decimal("0.00"),
            "net_amount": base_amount,
            "discounts_applied": []
        }
        
        if compound_method == "CASCADE":
            # Apply discounts in sequence (COBOL method)
            current_amount = base_amount
            
            # Sort by precedence: Trade -> Volume -> Promotion -> Special
            precedence = {
                DiscountType.TRADE: 1,
                DiscountType.VOLUME: 2,
                DiscountType.PROMOTION: 3,
                DiscountType.SPECIAL: 4,
                DiscountType.SETTLEMENT: 5  # Settlement is separate, usually
            }
            
            sorted_discounts = sorted(
                discounts,
                key=lambda x: precedence.get(x.get('type', DiscountType.SPECIAL), 99)
            )
            
            for discount in sorted_discounts:
                if discount.get('percentage', 0) > 0:
                    disc_pct = Decimal(str(discount['percentage']))
                    disc_amt = (current_amount * disc_pct / Decimal("100")).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    current_amount -= disc_amt
                    
                    result["discounts_applied"].append({
                        "type": discount.get('type'),
                        "percentage": disc_pct,
                        "amount": disc_amt,
                        "description": discount.get('description', '')
                    })
                    result["total_discount"] += disc_amt
            
            result["net_amount"] = current_amount
            
        elif compound_method == "BEST":
            # Take the highest single discount
            best_discount = max(discounts, key=lambda x: x.get('percentage', 0))
            if best_discount.get('percentage', 0) > 0:
                disc_pct = Decimal(str(best_discount['percentage']))
                disc_amt = (base_amount * disc_pct / Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                
                result["discounts_applied"].append({
                    "type": best_discount.get('type'),
                    "percentage": disc_pct,
                    "amount": disc_amt,
                    "description": best_discount.get('description', '')
                })
                result["total_discount"] = disc_amt
                result["net_amount"] = base_amount - disc_amt
        
        return result
    
    @staticmethod
    def validate_discount_limits(
        discount_percentage: Decimal,
        discount_type: DiscountType,
        user_level: int
    ) -> tuple[bool, Optional[str]]:
        """
        Validate discount against business rules and user authority
        
        Args:
            discount_percentage: Requested discount
            discount_type: Type of discount
            user_level: User's authority level (1-9)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        discount_percentage = Decimal(str(discount_percentage))
        
        # Maximum discount limits by type and user level
        limits = {
            # (discount_type, user_level): max_percentage
            (DiscountType.TRADE, 1): Decimal("0.00"),     # No authority
            (DiscountType.TRADE, 2): Decimal("5.00"),     # Operator
            (DiscountType.TRADE, 3): Decimal("10.00"),    # Supervisor
            (DiscountType.TRADE, 4): Decimal("15.00"),    # Manager
            (DiscountType.TRADE, 9): Decimal("100.00"),   # Admin
            
            (DiscountType.SPECIAL, 1): Decimal("0.00"),
            (DiscountType.SPECIAL, 2): Decimal("0.00"),
            (DiscountType.SPECIAL, 3): Decimal("15.00"),
            (DiscountType.SPECIAL, 4): Decimal("25.00"),
            (DiscountType.SPECIAL, 9): Decimal("100.00"),
        }
        
        # Get limit for this combination
        max_allowed = limits.get((discount_type, user_level), Decimal("0.00"))
        
        if discount_percentage > max_allowed:
            return False, f"Maximum {discount_type} discount for your user level is {max_allowed}%"
        
        # Additional business rules
        if discount_percentage > Decimal("50.00") and user_level < 9:
            return False, "Discounts over 50% require administrator approval"
        
        if discount_percentage < Decimal("0.00"):
            return False, "Negative discounts are not allowed"
        
        return True, None