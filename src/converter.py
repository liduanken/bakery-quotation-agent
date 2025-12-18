"""Unit conversion utilities for bakery quotation system"""
from typing import Dict, Tuple, List
from enum import Enum


class Unit(str, Enum):
    """Supported units"""
    KILOGRAM = "kg"
    GRAM = "g"
    LITER = "L"
    MILLILITER = "ml"
    EACH = "each"


class UnitConversionError(Exception):
    """Cannot convert between units"""
    pass


class UnitConverter:
    """
    Convert quantities between compatible units.
    
    Supported conversions:
    - Mass: g ↔ kg
    - Volume: ml ↔ L
    - Count: each (no conversion)
    """
    
    # Conversion factors: (from_unit, to_unit) -> factor
    CONVERSIONS: Dict[Tuple[str, str], float] = {
        # Mass conversions
        ('g', 'kg'): 0.001,
        ('kg', 'g'): 1000.0,
        
        # Volume conversions
        ('ml', 'L'): 0.001,
        ('L', 'ml'): 1000.0,
        
        # Identity conversions (same unit)
        ('kg', 'kg'): 1.0,
        ('g', 'g'): 1.0,
        ('L', 'L'): 1.0,
        ('ml', 'ml'): 1.0,
        ('each', 'each'): 1.0,
    }
    
    # Unit families (units that can be converted between each other)
    UNIT_FAMILIES = {
        'mass': {'kg', 'g'},
        'volume': {'L', 'ml'},
        'count': {'each'},
    }
    
    def convert(self, value: float, from_unit: str, to_unit: str) -> float:
        """
        Convert a value from one unit to another.
        
        Args:
            value: The quantity to convert
            from_unit: Source unit
            to_unit: Target unit
            
        Returns:
            Converted value
            
        Raises:
            UnitConversionError: If units are incompatible
            
        Examples:
            >>> converter = UnitConverter()
            >>> converter.convert(1000, 'g', 'kg')
            1.0
            >>> converter.convert(1.5, 'L', 'ml')
            1500.0
        """
        # Normalize units (case-insensitive)
        from_unit = from_unit.strip()
        to_unit = to_unit.strip()
        
        # Check if conversion is possible
        if not self.can_convert(from_unit, to_unit):
            raise UnitConversionError(
                f"Cannot convert from '{from_unit}' to '{to_unit}'. "
                f"Units are not compatible."
            )
        
        # Get conversion factor
        conversion_key = (from_unit, to_unit)
        
        if conversion_key not in self.CONVERSIONS:
            raise UnitConversionError(
                f"No conversion defined for {from_unit} → {to_unit}"
            )
        
        factor = self.CONVERSIONS[conversion_key]
        return value * factor
    
    def can_convert(self, from_unit: str, to_unit: str) -> bool:
        """
        Check if two units can be converted between each other.
        
        Args:
            from_unit: Source unit
            to_unit: Target unit
            
        Returns:
            True if conversion is possible
        """
        from_unit = from_unit.strip()
        to_unit = to_unit.strip()
        
        # Same unit is always convertible
        if from_unit == to_unit:
            return True
        
        # Check if both units are in the same family
        for family_units in self.UNIT_FAMILIES.values():
            if from_unit in family_units and to_unit in family_units:
                return True
        
        return False
    
    def get_unit_family(self, unit: str) -> str:
        """
        Get the family of a unit (mass, volume, count).
        
        Args:
            unit: Unit to check
            
        Returns:
            Family name
            
        Raises:
            ValueError: If unit is unknown
        """
        unit = unit.strip()
        
        for family_name, family_units in self.UNIT_FAMILIES.items():
            if unit in family_units:
                return family_name
        
        raise ValueError(f"Unknown unit: {unit}")
    
    def normalize_to_base_unit(self, value: float, unit: str) -> Tuple[float, str]:
        """
        Convert to base unit of the family (kg for mass, L for volume).
        
        Args:
            value: Quantity
            unit: Current unit
            
        Returns:
            (converted_value, base_unit)
        """
        family = self.get_unit_family(unit)
        
        base_units = {
            'mass': 'kg',
            'volume': 'L',
            'count': 'each'
        }
        
        base_unit = base_units[family]
        converted_value = self.convert(value, unit, base_unit)
        
        return converted_value, base_unit
    
    def convert_with_precision(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        precision: int = 3
    ) -> float:
        """
        Convert and round to specified precision.
        
        Args:
            value: Quantity to convert
            from_unit: Source unit
            to_unit: Target unit
            precision: Number of decimal places
            
        Returns:
            Converted and rounded value
        """
        result = self.convert(value, from_unit, to_unit)
        return round(result, precision)
    
    def smart_convert(
        self,
        value: float,
        from_unit: str,
        to_unit: str
    ) -> str:
        """
        Convert and format with appropriate precision.
        
        Returns formatted string with unit.
        
        Args:
            value: Quantity to convert
            from_unit: Source unit
            to_unit: Target unit
            
        Returns:
            Formatted string with unit (e.g., "1.5 kg")
        """
        converted = self.convert(value, from_unit, to_unit)
        
        # Use different precision based on magnitude
        if converted >= 100:
            precision = 1
        elif converted >= 1:
            precision = 2
        else:
            precision = 3
        
        return f"{converted:.{precision}f} {to_unit}"
    
    def batch_convert(
        self,
        items: List[Tuple[float, str]],
        to_unit: str
    ) -> List[float]:
        """
        Convert multiple items to the same target unit.
        
        Args:
            items: List of (value, from_unit) tuples
            to_unit: Target unit
            
        Returns:
            List of converted values
        """
        return [
            self.convert(value, from_unit, to_unit)
            for value, from_unit in items
        ]
