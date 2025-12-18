"""Tests for pricing calculator"""
import pytest

from src.calculator import MaterialLine, PricingCalculator, QuoteCalculation


@pytest.fixture
def calculator():
    """Create calculator with default rates"""
    return PricingCalculator(
        labor_rate=15.0,
        markup_pct=0.30,
        vat_pct=0.20
    )


@pytest.fixture
def sample_materials():
    """Sample material list for testing"""
    return [
        {
            'name': 'flour',
            'qty': 1.92,
            'unit': 'kg',
            'unit_cost': 0.90,
            'line_cost': 1.73
        },
        {
            'name': 'sugar',
            'qty': 1.44,
            'unit': 'kg',
            'unit_cost': 0.70,
            'line_cost': 1.01
        },
        {
            'name': 'butter',
            'qty': 0.96,
            'unit': 'kg',
            'unit_cost': 4.50,
            'line_cost': 4.32
        },
        {
            'name': 'eggs',
            'qty': 12.0,
            'unit': 'each',
            'unit_cost': 0.18,
            'line_cost': 2.16
        },
    ]


class TestPricingCalculator:
    """Test suite for pricing calculator"""

    def test_initialization(self):
        """Test calculator initialization"""
        calc = PricingCalculator(labor_rate=20.0, markup_pct=0.25, vat_pct=0.15)
        assert calc.labor_rate == 20.0
        assert calc.markup_pct == 0.25
        assert calc.vat_pct == 0.15

    def test_default_initialization(self):
        """Test default parameter values"""
        calc = PricingCalculator()
        assert calc.labor_rate == 15.0
        assert calc.markup_pct == 0.30
        assert calc.vat_pct == 0.20

    def test_invalid_labor_rate(self):
        """Test negative labor rate raises error"""
        with pytest.raises(ValueError):
            PricingCalculator(labor_rate=-5)

    def test_invalid_markup(self):
        """Test negative markup raises error"""
        with pytest.raises(ValueError):
            PricingCalculator(markup_pct=-0.1)

    def test_invalid_vat(self):
        """Test invalid VAT raises error"""
        with pytest.raises(ValueError):
            PricingCalculator(vat_pct=1.5)

        with pytest.raises(ValueError):
            PricingCalculator(vat_pct=-0.1)

    def test_calculate_quote(self, calculator, sample_materials):
        """Test complete quote calculation"""
        calc = calculator.calculate_quote(
            materials=sample_materials,
            labor_hours=1.2
        )

        # Verify it returns QuoteCalculation object
        assert isinstance(calc, QuoteCalculation)

        # Verify materials subtotal
        expected_materials = sum(m['line_cost'] for m in sample_materials)
        assert calc.materials_subtotal == pytest.approx(expected_materials, 0.01)

        # Verify labor cost
        assert calc.labor_cost == pytest.approx(1.2 * 15.0, 0.01)

        # Verify subtotal
        expected_subtotal = expected_materials + (1.2 * 15.0)
        assert calc.subtotal == pytest.approx(expected_subtotal, 0.01)

        # Verify markup
        expected_markup = expected_subtotal * 0.30
        assert calc.markup_value == pytest.approx(expected_markup, 0.01)

        # Verify price before VAT
        expected_before_vat = expected_subtotal + expected_markup
        assert calc.price_before_vat == pytest.approx(expected_before_vat, 0.01)

        # Verify VAT
        expected_vat = expected_before_vat * 0.20
        assert calc.vat_value == pytest.approx(expected_vat, 0.01)

        # Verify total
        expected_total = expected_before_vat + expected_vat
        assert calc.total == pytest.approx(expected_total, 0.01)

    def test_zero_labor(self, calculator, sample_materials):
        """Test with no labor hours"""
        calc = calculator.calculate_quote(
            materials=sample_materials,
            labor_hours=0.0
        )

        assert calc.labor_cost == 0.0
        assert calc.subtotal == calc.materials_subtotal

    def test_zero_markup(self, sample_materials):
        """Test with no markup"""
        calc = PricingCalculator(labor_rate=15.0, markup_pct=0.0, vat_pct=0.20)
        result = calc.calculate_quote(sample_materials, 1.0)

        assert result.markup_value == 0.0
        assert result.price_before_vat == result.subtotal

    def test_zero_vat(self, sample_materials):
        """Test with no VAT"""
        calc = PricingCalculator(labor_rate=15.0, markup_pct=0.30, vat_pct=0.0)
        result = calc.calculate_quote(sample_materials, 1.0)

        assert result.vat_value == 0.0
        assert result.total == result.price_before_vat

    def test_calculate_unit_price(self, calculator):
        """Test unit price calculation"""
        unit_price = calculator.calculate_unit_price(total=100.0, quantity=24)
        assert unit_price == pytest.approx(4.17, 0.01)

        unit_price = calculator.calculate_unit_price(total=50.0, quantity=10)
        assert unit_price == 5.0

    def test_calculate_unit_price_invalid(self, calculator):
        """Test unit price with invalid quantity"""
        with pytest.raises(ValueError):
            calculator.calculate_unit_price(100.0, 0)

        with pytest.raises(ValueError):
            calculator.calculate_unit_price(100.0, -5)

    def test_calculate_line_cost(self, calculator):
        """Test line cost calculation"""
        line_cost = calculator.calculate_line_cost(qty=1.92, unit_cost=0.90)
        assert line_cost == pytest.approx(1.73, 0.01)

        line_cost = calculator.calculate_line_cost(qty=2.0, unit_cost=3.5)
        assert line_cost == 7.0

    def test_apply_discount(self, calculator, sample_materials):
        """Test discount application"""
        calc = calculator.calculate_quote(sample_materials, 1.2)
        original_total = calc.total

        # Apply 10% discount
        discounted = calculator.apply_discount(calc, 0.10)

        # Total should be less
        assert discounted.total < original_total

        # VAT should be recalculated
        expected_vat = discounted.price_before_vat * 0.20
        assert discounted.vat_value == pytest.approx(expected_vat, 0.01)

        # Materials and labor should be unchanged
        assert discounted.materials_subtotal == calc.materials_subtotal
        assert discounted.labor_cost == calc.labor_cost

    def test_apply_discount_invalid(self, calculator, sample_materials):
        """Test discount with invalid percentage"""
        calc = calculator.calculate_quote(sample_materials, 1.2)

        with pytest.raises(ValueError):
            calculator.apply_discount(calc, -0.1)

        with pytest.raises(ValueError):
            calculator.apply_discount(calc, 1.5)

    def test_get_breakdown_summary(self, calculator, sample_materials):
        """Test breakdown summary formatting"""
        calc = calculator.calculate_quote(sample_materials, 1.2)
        summary = calculator.get_breakdown_summary(calc)

        assert isinstance(summary, str)
        assert "Quote Breakdown" in summary
        assert "flour" in summary
        assert "TOTAL" in summary
        assert str(calc.total) in summary

    def test_real_world_example(self):
        """Test with actual specification example"""
        # 24 cupcakes example from spec
        calculator = PricingCalculator(
            labor_rate=15.0,
            markup_pct=0.30,
            vat_pct=0.20
        )

        materials = [
            {'name': 'flour', 'qty': 1.92, 'unit': 'kg', 'unit_cost': 0.90, 'line_cost': 1.73},
            {'name': 'sugar', 'qty': 1.44, 'unit': 'kg', 'unit_cost': 0.70, 'line_cost': 1.01},
            {'name': 'butter', 'qty': 0.96, 'unit': 'kg', 'unit_cost': 4.50, 'line_cost': 4.32},
            {'name': 'eggs', 'qty': 12.0, 'unit': 'each', 'unit_cost': 0.18, 'line_cost': 2.16},
            {'name': 'milk', 'qty': 1.2, 'unit': 'L', 'unit_cost': 0.60, 'line_cost': 0.72},
            {'name': 'vanilla', 'qty': 24.0, 'unit': 'ml', 'unit_cost': 0.05, 'line_cost': 1.20},
            {'name': 'baking_powder', 'qty': 0.024, 'unit': 'kg', 'unit_cost': 3.00, 'line_cost': 0.07},
        ]

        calc = calculator.calculate_quote(materials, labor_hours=1.2)

        # Verify key totals
        assert calc.materials_subtotal == pytest.approx(11.21, 0.1)
        assert calc.labor_cost == pytest.approx(18.0, 0.01)
        assert calc.total > 0  # Should produce a valid total

    def test_to_dict(self, calculator, sample_materials):
        """Test conversion to dictionary"""
        calc = calculator.calculate_quote(sample_materials, 1.2)
        data = calc.to_dict()

        # Verify structure
        assert 'lines' in data
        assert 'total' in data
        assert 'markup_pct' in data
        assert 'vat_pct' in data

        # Verify percentages converted
        assert data['markup_pct'] == 30  # Should be converted to percentage
        assert data['vat_pct'] == 20

        # Verify lines structure
        assert len(data['lines']) == len(sample_materials)
        first_line = data['lines'][0]
        assert 'name' in first_line
        assert 'qty' in first_line
        assert 'unit' in first_line
        assert 'unit_cost' in first_line
        assert 'line_cost' in first_line

    def test_material_line_dataclass(self):
        """Test MaterialLine dataclass"""
        line = MaterialLine(
            name='flour',
            qty=1.92,
            unit='kg',
            unit_cost=0.90,
            line_cost=1.73
        )

        assert line.name == 'flour'
        assert line.qty == 1.92
        assert line.unit == 'kg'
        assert line.unit_cost == 0.90
        assert line.line_cost == 1.73

    def test_quote_calculation_dataclass(self):
        """Test QuoteCalculation dataclass"""
        lines = [
            MaterialLine('flour', 1.92, 'kg', 0.90, 1.73)
        ]

        calc = QuoteCalculation(
            lines=lines,
            materials_subtotal=1.73,
            labor_hours=1.0,
            labor_rate=15.0,
            labor_cost=15.0,
            subtotal=16.73,
            markup_pct=0.30,
            markup_value=5.02,
            price_before_vat=21.75,
            vat_pct=0.20,
            vat_value=4.35,
            total=26.10
        )

        assert calc.total == 26.10
        assert len(calc.lines) == 1
        assert calc.materials_subtotal == 1.73

    def test_rounding(self, calculator):
        """Test that all monetary values are rounded to 2 decimals"""
        materials = [
            {'name': 'test', 'qty': 1.111, 'unit': 'kg', 'unit_cost': 3.333, 'line_cost': 3.70}
        ]

        calc = calculator.calculate_quote(materials, 1.111)

        # All monetary values should have at most 2 decimal places
        assert calc.materials_subtotal == round(calc.materials_subtotal, 2)
        assert calc.labor_cost == round(calc.labor_cost, 2)
        assert calc.subtotal == round(calc.subtotal, 2)
        assert calc.markup_value == round(calc.markup_value, 2)
        assert calc.price_before_vat == round(calc.price_before_vat, 2)
        assert calc.vat_value == round(calc.vat_value, 2)
        assert calc.total == round(calc.total, 2)
