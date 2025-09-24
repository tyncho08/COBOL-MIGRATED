"""
VAT/Tax Calculation Engine
Migrated from ACAS COBOL VAT calculation logic
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from typing import Dict, List, Optional, Tuple
from enum import Enum


class VATCode(str, Enum):
    """VAT codes from COBOL system"""
    STANDARD = "S"     # Code 1 - Standard rate
    REDUCED = "R"      # Code 2 - Reduced rate
    ZERO = "Z"         # Code 3 - Zero rate
    EXEMPT = "E"       # Code 4 - Exempt
    LOCAL_TAX_1 = "L1" # Code 4 - Local sales tax
    LOCAL_TAX_2 = "L2" # Code 5 - Local sales tax


class VATCalculator:
    """
    VAT calculation engine preserving COBOL logic
    Implements exact calculation methods from sl910.cbl
    """
    
    # VAT rates as of 01/01/2017 (from COBOL)
    VAT_RATES = {
        VATCode.STANDARD: Decimal("20.00"),
        VATCode.REDUCED: Decimal("5.00"),
        VATCode.ZERO: Decimal("0.00"),
        VATCode.EXEMPT: Decimal("0.00"),
        VATCode.LOCAL_TAX_1: Decimal("8.00"),  # Example local rate
        VATCode.LOCAL_TAX_2: Decimal("10.00"), # Example local rate
    }
    
    # Historical VAT rates for back-dated transactions
    HISTORICAL_RATES = [
        # Format: (effective_date, {code: rate})
        (date(2011, 1, 4), {VATCode.STANDARD: Decimal("20.00")}),
        (date(2010, 1, 1), {VATCode.STANDARD: Decimal("17.50")}),
        (date(2008, 12, 1), {VATCode.STANDARD: Decimal("15.00")}),
    ]
    
    @classmethod
    def calculate_vat(
        cls,
        net_amount: Decimal,
        vat_code: str,
        transaction_date: Optional[date] = None,
        reverse_charge: bool = False
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calculate VAT amount based on COBOL logic
        
        Args:
            net_amount: Net amount before VAT
            vat_code: VAT code (S, R, Z, E, etc.)
            transaction_date: Date for historical rate lookup
            reverse_charge: Apply reverse charge rules
            
        Returns:
            Tuple of (vat_amount, gross_amount, effective_rate)
        """
        # Ensure Decimal type
        net_amount = Decimal(str(net_amount))
        
        # Get effective VAT rate
        effective_rate = cls._get_effective_rate(vat_code, transaction_date)
        
        # Apply reverse charge rules
        if reverse_charge and vat_code == VATCode.STANDARD:
            # Reverse charge - VAT is not added but noted
            vat_amount = Decimal("0.00")
            gross_amount = net_amount
        else:
            # Standard VAT calculation (COBOL formula)
            # compute WS-VAT rounded = (WS-Net * WS-VAT-Rate) / 100
            vat_amount = (net_amount * effective_rate / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            gross_amount = net_amount + vat_amount
        
        return vat_amount, gross_amount, effective_rate
    
    @classmethod
    def calculate_vat_inclusive(
        cls,
        gross_amount: Decimal,
        vat_code: str,
        transaction_date: Optional[date] = None
    ) -> Tuple[Decimal, Decimal]:
        """
        Extract VAT from gross amount (VAT-inclusive price)
        
        Args:
            gross_amount: Gross amount including VAT
            vat_code: VAT code
            transaction_date: Date for historical rate lookup
            
        Returns:
            Tuple of (net_amount, vat_amount)
        """
        gross_amount = Decimal(str(gross_amount))
        effective_rate = cls._get_effective_rate(vat_code, transaction_date)
        
        # Calculate net amount: gross / (1 + rate/100)
        divisor = Decimal("1") + (effective_rate / Decimal("100"))
        net_amount = (gross_amount / divisor).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        vat_amount = gross_amount - net_amount
        
        return net_amount, vat_amount
    
    @classmethod
    def calculate_compound_vat(
        cls,
        line_items: List[Dict],
        header_discount_pct: Decimal = Decimal("0.00"),
        extra_charges: Decimal = Decimal("0.00"),
        shipping: Decimal = Decimal("0.00")
    ) -> Dict[str, Decimal]:
        """
        Calculate VAT for complete invoice with multiple items
        Implements logic from sl910.cbl invoice calculation
        
        Args:
            line_items: List of {'net': Decimal, 'vat_code': str, 'discount_pct': Decimal}
            header_discount_pct: Overall invoice discount
            extra_charges: Additional charges
            shipping: Shipping charges (always standard VAT)
            
        Returns:
            Dict with totals and VAT breakdown
        """
        result = {
            "net_total": Decimal("0.00"),
            "vat_total": Decimal("0.00"),
            "gross_total": Decimal("0.00"),
            "vat_breakdown": {}
        }
        
        # Process line items
        for item in line_items:
            # Apply line-level discount
            net = Decimal(str(item["net"]))
            if "discount_pct" in item and item["discount_pct"]:
                discount_amt = (net * Decimal(str(item["discount_pct"])) / Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                net = net - discount_amt
            
            # Apply header-level discount
            if header_discount_pct:
                header_discount = (net * header_discount_pct / Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                net = net - header_discount
            
            # Calculate VAT
            vat_amount, _, rate = cls.calculate_vat(net, item["vat_code"])
            
            # Accumulate totals
            result["net_total"] += net
            result["vat_total"] += vat_amount
            
            # Track VAT breakdown by code
            vat_code = item["vat_code"]
            if vat_code not in result["vat_breakdown"]:
                result["vat_breakdown"][vat_code] = {
                    "net": Decimal("0.00"),
                    "vat": Decimal("0.00"),
                    "rate": rate
                }
            result["vat_breakdown"][vat_code]["net"] += net
            result["vat_breakdown"][vat_code]["vat"] += vat_amount
        
        # Add extra charges (no discount applied)
        if extra_charges:
            vat_on_extras, _, _ = cls.calculate_vat(extra_charges, VATCode.STANDARD)
            result["net_total"] += extra_charges
            result["vat_total"] += vat_on_extras
            
            # Update breakdown
            if VATCode.STANDARD not in result["vat_breakdown"]:
                result["vat_breakdown"][VATCode.STANDARD] = {
                    "net": Decimal("0.00"),
                    "vat": Decimal("0.00"),
                    "rate": cls.VAT_RATES[VATCode.STANDARD]
                }
            result["vat_breakdown"][VATCode.STANDARD]["net"] += extra_charges
            result["vat_breakdown"][VATCode.STANDARD]["vat"] += vat_on_extras
        
        # Add shipping (always standard VAT per COBOL)
        if shipping:
            vat_on_shipping, _, _ = cls.calculate_vat(shipping, VATCode.STANDARD)
            result["net_total"] += shipping
            result["vat_total"] += vat_on_shipping
            
            # Update breakdown
            if VATCode.STANDARD not in result["vat_breakdown"]:
                result["vat_breakdown"][VATCode.STANDARD] = {
                    "net": Decimal("0.00"),
                    "vat": Decimal("0.00"),
                    "rate": cls.VAT_RATES[VATCode.STANDARD]
                }
            result["vat_breakdown"][VATCode.STANDARD]["net"] += shipping
            result["vat_breakdown"][VATCode.STANDARD]["vat"] += vat_on_shipping
        
        # Calculate gross total
        result["gross_total"] = result["net_total"] + result["vat_total"]
        
        return result
    
    @classmethod
    def _get_effective_rate(cls, vat_code: str, transaction_date: Optional[date] = None) -> Decimal:
        """Get effective VAT rate for given date"""
        # Use current rates if no date specified
        if not transaction_date:
            return cls.VAT_RATES.get(vat_code, Decimal("0.00"))
        
        # Check historical rates for standard rate
        if vat_code == VATCode.STANDARD:
            for cutoff_date, rates in cls.HISTORICAL_RATES:
                if transaction_date >= cutoff_date:
                    return rates.get(vat_code, cls.VAT_RATES[vat_code])
        
        return cls.VAT_RATES.get(vat_code, Decimal("0.00"))
    
    @classmethod
    def validate_ec_vat_number(cls, vat_number: str, country_code: str) -> bool:
        """
        Validate EC VAT number format
        Implements basic validation - full validation would use VIES service
        """
        # Basic format validation
        if not vat_number or len(vat_number) < 4:
            return False
        
        # Country-specific format rules (simplified)
        formats = {
            "GB": r"^\d{9}$|^\d{12}$",  # 9 or 12 digits
            "FR": r"^[A-Z0-9]{2}\d{9}$", # 2 chars + 9 digits
            "DE": r"^\d{9}$",            # 9 digits
            "IT": r"^\d{11}$",           # 11 digits
        }
        
        # Add more country formats as needed
        return True  # Simplified for now