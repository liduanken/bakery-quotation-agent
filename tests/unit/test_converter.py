"""Tests for unit converter"""
import pytest

from src.converter import Unit, UnitConversionError, UnitConverter


@pytest.fixture
def converter():
    """Create converter instance"""
    return UnitConverter()


class TestUnitConverter:
    """Test suite for unit converter"""

    def test_kg_to_g(self, converter):
        """Test kg to g conversion"""
        assert converter.convert(1, 'kg', 'g') == 1000
        assert converter.convert(0.5, 'kg', 'g') == 500
        assert converter.convert(2.5, 'kg', 'g') == 2500

    def test_g_to_kg(self, converter):
        """Test g to kg conversion"""
        assert converter.convert(1000, 'g', 'kg') == 1.0
        assert converter.convert(500, 'g', 'kg') == 0.5
        assert converter.convert(1, 'g', 'kg') == 0.001

    def test_L_to_ml(self, converter):
        """Test L to ml conversion"""
        assert converter.convert(1, 'L', 'ml') == 1000
        assert converter.convert(0.5, 'L', 'ml') == 500
        assert converter.convert(1.5, 'L', 'ml') == 1500

    def test_ml_to_L(self, converter):
        """Test ml to L conversion"""
        assert converter.convert(1000, 'ml', 'L') == 1.0
        assert converter.convert(500, 'ml', 'L') == 0.5
        assert converter.convert(250, 'ml', 'L') == 0.25

    def test_same_unit(self, converter):
        """Converting to same unit should return same value"""
        assert converter.convert(5, 'kg', 'kg') == 5
        assert converter.convert(100, 'ml', 'ml') == 100
        assert converter.convert(10, 'each', 'each') == 10

    def test_incompatible_units(self, converter):
        """Should raise error for incompatible units"""
        with pytest.raises(UnitConversionError):
            converter.convert(1, 'kg', 'L')

        with pytest.raises(UnitConversionError):
            converter.convert(1, 'ml', 'kg')

        with pytest.raises(UnitConversionError):
            converter.convert(1, 'each', 'kg')

    def test_can_convert(self, converter):
        """Test can_convert method"""
        assert converter.can_convert('kg', 'g')
        assert converter.can_convert('g', 'kg')
        assert converter.can_convert('L', 'ml')
        assert converter.can_convert('kg', 'kg')

        assert not converter.can_convert('kg', 'L')
        assert not converter.can_convert('each', 'kg')

    def test_get_unit_family(self, converter):
        """Test unit family detection"""
        assert converter.get_unit_family('kg') == 'mass'
        assert converter.get_unit_family('g') == 'mass'
        assert converter.get_unit_family('L') == 'volume'
        assert converter.get_unit_family('ml') == 'volume'
        assert converter.get_unit_family('each') == 'count'

    def test_get_unit_family_unknown(self, converter):
        """Test unknown unit raises error"""
        with pytest.raises(ValueError):
            converter.get_unit_family('unknown')

    def test_normalize_to_base_unit(self, converter):
        """Test normalization to base units"""
        value, unit = converter.normalize_to_base_unit(1000, 'g')
        assert value == 1.0
        assert unit == 'kg'

        value, unit = converter.normalize_to_base_unit(500, 'ml')
        assert value == 0.5
        assert unit == 'L'

        value, unit = converter.normalize_to_base_unit(10, 'each')
        assert value == 10
        assert unit == 'each'

    def test_convert_with_precision(self, converter):
        """Test conversion with precision rounding"""
        result = converter.convert_with_precision(1, 'g', 'kg', precision=3)
        assert result == 0.001

        result = converter.convert_with_precision(1.234567, 'kg', 'g', precision=2)
        assert result == 1234.57

    def test_smart_convert(self, converter):
        """Test smart conversion with formatting"""
        # Large values: 1 decimal
        result = converter.smart_convert(100, 'kg', 'g')
        assert result == "100000.0 g"

        # Medium values: 2 decimals (values >= 100 get 1 decimal)
        result = converter.smart_convert(1.5, 'L', 'ml')
        assert result == "1500.0 ml"  # 1500 >= 100, so 1 decimal

        # Small values: 3 decimals
        result = converter.smart_convert(24, 'ml', 'L')
        assert result == "0.024 L"

    def test_batch_convert(self, converter):
        """Test batch conversion"""
        items = [
            (1000, 'g'),
            (500, 'g'),
            (250, 'g')
        ]
        results = converter.batch_convert(items, 'kg')
        assert results == [1.0, 0.5, 0.25]

    def test_real_world_scenario(self, converter):
        """Test with real bakery quantities"""
        # BOM says 1.92 kg of flour
        # Database stores price per kg
        # No conversion needed
        assert converter.convert(1.92, 'kg', 'kg') == 1.92

        # BOM says 24 ml of vanilla
        # Database stores price per ml
        # No conversion needed
        assert converter.convert(24, 'ml', 'ml') == 24

        # If database had vanilla in L:
        vanilla_ml = 24
        vanilla_L = converter.convert(vanilla_ml, 'ml', 'L')
        assert vanilla_L == 0.024

    def test_unit_enum(self):
        """Test Unit enum"""
        assert Unit.KILOGRAM == "kg"
        assert Unit.GRAM == "g"
        assert Unit.LITER == "L"
        assert Unit.MILLILITER == "ml"
        assert Unit.EACH == "each"

    def test_whitespace_handling(self, converter):
        """Test that whitespace is handled correctly"""
        assert converter.convert(1000, ' g ', ' kg ') == 1.0
        assert converter.can_convert(' kg ', ' g ')
