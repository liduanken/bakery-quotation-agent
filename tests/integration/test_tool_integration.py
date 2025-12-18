"""Integration tests for tools working together"""
import pytest
import tempfile
from pathlib import Path
from src.tools.database_tool import DatabaseTool
from src.converter import UnitConverter
from src.calculator import PricingCalculator
from tests.fixtures.sample_data import TestDataFactory


@pytest.fixture
def temp_database():
    """Create temporary test database"""
    import sqlite3
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        db_path = f.name
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create schema
    cursor.execute("""
        CREATE TABLE materials (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            unit TEXT NOT NULL,
            unit_cost REAL NOT NULL,
            currency TEXT NOT NULL,
            last_updated TEXT NOT NULL
        )
    """)
    
    # Insert test data
    materials = TestDataFactory.create_material_costs()
    for mat in materials:
        cursor.execute(
            "INSERT INTO materials (name, unit, unit_cost, currency, last_updated) VALUES (?, ?, ?, ?, ?)",
            (mat['name'], mat['unit'], mat['unit_cost'], mat['currency'], '2025-12-18')
        )
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


class TestToolIntegration:
    """Test tools working together"""
    
    def test_bom_to_database_lookup(self, temp_database):
        """Test getting BOM materials from database"""
        db = DatabaseTool(temp_database)
        bom_estimate = TestDataFactory.create_bom_estimate('cupcakes', 24)
        
        # Get material names from BOM
        material_names = [m['name'] for m in bom_estimate['materials']]
        
        # Look up costs
        costs = db.get_materials_bulk(material_names)
        
        # Verify all materials found
        assert len(costs) == len(material_names)
        assert 'flour' in costs
        assert costs['flour']['unit_cost'] == 0.90
    
    def test_converter_with_bom_and_database(self, temp_database):
        """Test unit conversion between BOM and database"""
        db = DatabaseTool(temp_database)
        converter = UnitConverter()
        bom_estimate = TestDataFactory.create_bom_estimate('cupcakes', 24)
        
        # Get a material - get_material_cost returns MaterialCost object
        bom_material = bom_estimate['materials'][0]  # flour
        db_material = db.get_material_cost('flour')
        
        # MaterialCost has attributes
        bom_qty = bom_material['qty']
        bom_unit = bom_material['unit']
        db_unit = db_material.unit
        
        if bom_unit != db_unit:
            converted_qty = converter.convert(bom_qty, bom_unit, db_unit)
        else:
            converted_qty = bom_qty
        
        # Calculate cost
        cost = converted_qty * db_material.unit_cost
        assert cost > 0
    
    def test_full_calculation_pipeline(self, temp_database):
        """Test complete calculation from BOM to totals"""
        db = DatabaseTool(temp_database)
        converter = UnitConverter()
        calculator = PricingCalculator(
            labor_rate=15.0,
            markup_pct=0.30,
            vat_pct=0.20
        )
        
        bom_estimate = TestDataFactory.create_bom_estimate('cupcakes', 24)
        
        # Get material costs
        material_names = [m['name'] for m in bom_estimate['materials']]
        costs = db.get_materials_bulk(material_names)
        
        # Build material lines
        lines = []
        for material in bom_estimate['materials']:
            name = material['name']
            qty = material['qty']
            bom_unit = material['unit']
            
            # get_materials_bulk returns dicts
            cost_data = costs[name]
            db_unit = cost_data['unit']
            unit_cost = cost_data['unit_cost']
            
            # Convert units
            if bom_unit != db_unit and converter.can_convert(bom_unit, db_unit):
                qty_converted = converter.convert(qty, bom_unit, db_unit)
            else:
                qty_converted = qty
            
            line_cost = calculator.calculate_line_cost(qty_converted, unit_cost)
            
            lines.append({
                'name': name,
                'qty': qty,
                'unit': bom_unit,
                'unit_cost': unit_cost,
                'line_cost': line_cost
            })
        
        # Calculate totals
        calc = calculator.calculate_quote(
            materials=lines,
            labor_hours=bom_estimate['labor_hours']
        )
        
        # Verify calculations
        assert calc.materials_subtotal > 0
        assert calc.labor_cost == pytest.approx(bom_estimate['labor_hours'] * 15.0)
        assert calc.total > calc.subtotal
        assert len(calc.lines) == len(bom_estimate['materials'])
    
    def test_complete_workflow_cupcakes(self, temp_database):
        """Test complete workflow for cupcakes"""
        # Initialize tools
        db = DatabaseTool(temp_database)
        converter = UnitConverter()
        calculator = PricingCalculator(labor_rate=15.0, markup_pct=0.30, vat_pct=0.20)
        
        # Get BOM estimate
        bom = TestDataFactory.create_bom_estimate('cupcakes', 24)
        assert bom['job_type'] == 'cupcakes'
        assert bom['quantity'] == 24
        
        # Fetch material costs
        material_names = [m['name'] for m in bom['materials']]
        costs = db.get_materials_bulk(material_names)
        assert len(costs) == len(material_names)
        
        # Process materials with unit conversion
        processed_materials = []
        for mat in bom['materials']:
            # get_materials_bulk returns dicts
            db_mat = costs[mat['name']]
            
            # Convert units if needed
            if mat['unit'] != db_mat['unit']:
                qty = converter.convert(mat['qty'], mat['unit'], db_mat['unit'])
            else:
                qty = mat['qty']
            
            line_cost = calculator.calculate_line_cost(qty, db_mat['unit_cost'])
            
            processed_materials.append({
                'name': mat['name'],
                'qty': mat['qty'],
                'unit': mat['unit'],
                'unit_cost': db_mat['unit_cost'],
                'line_cost': line_cost
            })
        
        # Calculate quote
        quote = calculator.calculate_quote(processed_materials, bom['labor_hours'])
        
        # Verify structure
        assert quote.total > 0
        assert quote.vat_value > 0
        assert quote.markup_value > 0
        assert len(quote.lines) == 7  # cupcakes has 7 materials
    
    def test_complete_workflow_cake(self, temp_database):
        """Test complete workflow for cake"""
        db = DatabaseTool(temp_database)
        converter = UnitConverter()
        calculator = PricingCalculator(labor_rate=15.0, markup_pct=0.30, vat_pct=0.20)
        
        # Get BOM estimate for cake (1 unit)
        bom = TestDataFactory.create_bom_estimate('cake', 1)
        
        # Process workflow
        material_names = [m['name'] for m in bom['materials']]
        costs = db.get_materials_bulk(material_names)
        
        lines = []
        for mat in bom['materials']:
            # get_materials_bulk returns dicts
            db_mat = costs[mat['name']]
            qty = mat['qty']
            if mat['unit'] != db_mat['unit'] and converter.can_convert(mat['unit'], db_mat['unit']):
                qty = converter.convert(qty, mat['unit'], db_mat['unit'])
            
            line_cost = calculator.calculate_line_cost(qty, db_mat['unit_cost'])
            lines.append({
                'name': mat['name'],
                'qty': mat['qty'],
                'unit': mat['unit'],
                'unit_cost': db_mat['unit_cost'],
                'line_cost': line_cost
            })
        
        quote = calculator.calculate_quote(lines, bom['labor_hours'])
        
        # Cake should be more expensive than cupcakes (higher labor)
        assert quote.total > 10  # Reasonable minimum for a cake
        assert len(quote.lines) == 5  # cake has 5 materials
    
    def test_unit_conversion_integration(self, temp_database):
        """Test unit conversion across components"""
        db = DatabaseTool(temp_database)
        converter = UnitConverter()
        
        # Test conversion scenario: BOM in grams, DB in kg
        flour_db = db.get_material_cost('flour')
        assert flour_db.unit == 'kg'
        
        # BOM says 500g
        bom_qty = 500
        bom_unit = 'g'
        
        # Convert to database unit
        converted_qty = converter.convert(bom_qty, bom_unit, flour_db.unit)
        assert converted_qty == 0.5
        
        # Calculate cost
        cost = converted_qty * flour_db.unit_cost
        assert cost == pytest.approx(0.45, 0.01)  # 0.5 kg * 0.90
    
    def test_database_bulk_operations(self, temp_database):
        """Test bulk database operations in workflow"""
        db = DatabaseTool(temp_database)
        
        # Get multiple materials at once
        materials = ['flour', 'sugar', 'butter', 'eggs']
        costs = db.get_materials_bulk(materials)
        
        assert len(costs) == 4
        assert all(name in costs for name in materials)
        
        # Verify structure - bulk returns dicts
        for name, mat in costs.items():
            assert 'unit_cost' in mat
            assert 'unit' in mat
            assert mat['unit_cost'] > 0
    
    def test_calculator_to_dict_for_template(self, temp_database):
        """Test calculator output converts to template format"""
        calculator = PricingCalculator(labor_rate=15.0, markup_pct=0.30, vat_pct=0.20)
        
        materials = [
            {'name': 'flour', 'qty': 1.0, 'unit': 'kg', 'unit_cost': 0.90, 'line_cost': 0.90}
        ]
        
        calc = calculator.calculate_quote(materials, 1.0)
        data = calc.to_dict()
        
        # Verify template-ready format
        assert 'lines' in data
        assert 'total' in data
        assert 'markup_pct' in data
        assert data['markup_pct'] == 30  # Converted to percentage
        assert data['vat_pct'] == 20
        
        # Verify lines format
        assert len(data['lines']) == 1
        line = data['lines'][0]
        assert 'name' in line
        assert 'qty' in line
        assert 'unit' in line


class TestErrorHandling:
    """Test error handling in integrated workflows"""
    
    def test_missing_material_in_database(self, temp_database):
        """Test handling of missing materials"""
        db = DatabaseTool(temp_database)
        
        # get_material_cost returns None, use get_material_cost_strict for exception
        from src.tools.database_tool import MaterialNotFoundError
        with pytest.raises(MaterialNotFoundError):
            db.get_material_cost_strict('nonexistent_material')
    
    def test_incompatible_unit_conversion(self):
        """Test handling of incompatible unit conversions"""
        converter = UnitConverter()
        
        from src.converter import UnitConversionError
        with pytest.raises(UnitConversionError):
            converter.convert(1.0, 'kg', 'L')  # Can't convert mass to volume
    
    def test_calculator_with_empty_materials(self):
        """Test calculator with no materials"""
        calculator = PricingCalculator()
        
        calc = calculator.calculate_quote([], 1.0)
        assert calc.materials_subtotal == 0
        assert calc.labor_cost > 0
        assert calc.total > 0  # Should still have labor + markup + VAT
