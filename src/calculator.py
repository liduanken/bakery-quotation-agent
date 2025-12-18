"""Pricing calculation utilities for bakery quotation system"""
from dataclasses import dataclass
from typing import Any


@dataclass
class MaterialLine:
    """Single material line in quote"""
    name: str
    qty: float
    unit: str
    unit_cost: float
    line_cost: float


@dataclass
class QuoteCalculation:
    """Complete quote calculation results"""
    # Material lines
    lines: list[MaterialLine]
    materials_subtotal: float

    # Labor
    labor_hours: float
    labor_rate: float
    labor_cost: float

    # Subtotal
    subtotal: float

    # Markup
    markup_pct: float  # as decimal (0.30 for 30%)
    markup_value: float
    price_before_vat: float

    # VAT
    vat_pct: float  # as decimal (0.20 for 20%)
    vat_value: float

    # Final
    total: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for template"""
        return {
            'lines': [
                {
                    'name': line.name,
                    'qty': line.qty,
                    'unit': line.unit,
                    'unit_cost': line.unit_cost,
                    'line_cost': line.line_cost
                }
                for line in self.lines
            ],
            'materials_subtotal': self.materials_subtotal,
            'labor_hours': self.labor_hours,
            'labor_rate': self.labor_rate,
            'labor_cost': self.labor_cost,
            'subtotal': self.subtotal,
            'markup_pct': self.markup_pct * 100,  # Convert to percentage
            'markup_value': self.markup_value,
            'price_before_vat': self.price_before_vat,
            'vat_pct': self.vat_pct * 100,  # Convert to percentage
            'vat_value': self.vat_value,
            'total': self.total
        }


class PricingCalculator:
    """
    Calculate quote totals with markup and VAT.
    
    Follows the pricing logic from specification.
    """

    def __init__(
        self,
        labor_rate: float = 15.0,
        markup_pct: float = 0.30,  # 30%
        vat_pct: float = 0.20  # 20%
    ):
        """
        Initialize calculator with rates.
        
        Args:
            labor_rate: Cost per labor hour (in currency)
            markup_pct: Markup percentage as decimal (0.30 = 30%)
            vat_pct: VAT percentage as decimal (0.20 = 20%)
        """
        if labor_rate < 0:
            raise ValueError("Labor rate must be non-negative")
        if markup_pct < 0:
            raise ValueError("Markup percentage must be non-negative")
        if vat_pct < 0 or vat_pct > 1:
            raise ValueError("VAT percentage must be between 0 and 1")

        self.labor_rate = labor_rate
        self.markup_pct = markup_pct
        self.vat_pct = vat_pct

    def calculate_quote(
        self,
        materials: list[dict[str, Any]],
        labor_hours: float
    ) -> QuoteCalculation:
        """
        Calculate complete quote with all totals.
        
        Args:
            materials: List of material dicts with keys:
                - name: Material name
                - qty: Quantity needed
                - unit: Unit of measurement
                - unit_cost: Cost per unit
                - line_cost: Pre-calculated line cost
            labor_hours: Total labor hours
            
        Returns:
            QuoteCalculation with all computed values
        """
        # Convert materials to MaterialLine objects
        lines = [
            MaterialLine(
                name=m['name'],
                qty=m['qty'],
                unit=m['unit'],
                unit_cost=m['unit_cost'],
                line_cost=m['line_cost']
            )
            for m in materials
        ]

        # 1. Materials subtotal
        materials_subtotal = sum(line.line_cost for line in lines)

        # 2. Labor cost
        labor_cost = labor_hours * self.labor_rate

        # 3. Subtotal (before markup)
        subtotal = materials_subtotal + labor_cost

        # 4. Apply markup
        markup_value = subtotal * self.markup_pct
        price_before_vat = subtotal + markup_value

        # 5. Apply VAT
        vat_value = price_before_vat * self.vat_pct
        total = price_before_vat + vat_value

        return QuoteCalculation(
            lines=lines,
            materials_subtotal=round(materials_subtotal, 2),
            labor_hours=labor_hours,
            labor_rate=self.labor_rate,
            labor_cost=round(labor_cost, 2),
            subtotal=round(subtotal, 2),
            markup_pct=self.markup_pct,
            markup_value=round(markup_value, 2),
            price_before_vat=round(price_before_vat, 2),
            vat_pct=self.vat_pct,
            vat_value=round(vat_value, 2),
            total=round(total, 2)
        )

    def calculate_unit_price(self, total: float, quantity: int) -> float:
        """
        Calculate price per unit.
        
        Args:
            total: Total quote price
            quantity: Number of units
            
        Returns:
            Price per unit
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        return round(total / quantity, 2)

    def calculate_line_cost(self, qty: float, unit_cost: float) -> float:
        """
        Calculate cost for a single material line.
        
        Args:
            qty: Quantity needed
            unit_cost: Cost per unit
            
        Returns:
            Total line cost
        """
        return round(qty * unit_cost, 2)

    def apply_discount(
        self,
        calculation: QuoteCalculation,
        discount_pct: float
    ) -> QuoteCalculation:
        """
        Apply a discount to the quote.
        
        Args:
            calculation: Original calculation
            discount_pct: Discount percentage as decimal
            
        Returns:
            New calculation with discount applied
        """
        if discount_pct < 0 or discount_pct > 1:
            raise ValueError("Discount must be between 0 and 1")

        # Apply discount to price before VAT
        discounted_price = calculation.price_before_vat * (1 - discount_pct)

        # Recalculate VAT on discounted price
        new_vat = discounted_price * self.vat_pct
        new_total = discounted_price + new_vat

        # Create new calculation (immutable pattern)
        return QuoteCalculation(
            lines=calculation.lines,
            materials_subtotal=calculation.materials_subtotal,
            labor_hours=calculation.labor_hours,
            labor_rate=calculation.labor_rate,
            labor_cost=calculation.labor_cost,
            subtotal=calculation.subtotal,
            markup_pct=calculation.markup_pct,
            markup_value=calculation.markup_value,
            price_before_vat=round(discounted_price, 2),
            vat_pct=self.vat_pct,
            vat_value=round(new_vat, 2),
            total=round(new_total, 2)
        )

    def get_breakdown_summary(self, calc: QuoteCalculation) -> str:
        """
        Format calculation breakdown for display.
        
        Returns:
            Formatted string with breakdown
        """
        lines = [
            "Quote Breakdown",
            "=" * 50,
            "",
            "Materials:",
        ]

        for line in calc.lines:
            lines.append(
                f"  {line.name}: {line.qty:.2f} {line.unit} "
                f"@ {line.unit_cost:.2f} = {line.line_cost:.2f}"
            )

        lines.extend([
            "",
            f"Materials Subtotal: {calc.materials_subtotal:.2f}",
            f"Labor ({calc.labor_hours:.2f}h @ {calc.labor_rate:.2f}/h): {calc.labor_cost:.2f}",
            f"Subtotal: {calc.subtotal:.2f}",
            "",
            f"Markup ({calc.markup_pct * 100:.0f}%): {calc.markup_value:.2f}",
            f"Price before VAT: {calc.price_before_vat:.2f}",
            "",
            f"VAT ({calc.vat_pct * 100:.0f}%): {calc.vat_value:.2f}",
            "",
            f"TOTAL: {calc.total:.2f}",
        ])

        return "\n".join(lines)
