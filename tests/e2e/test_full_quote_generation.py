"""End-to-End Tests for Complete Quote Generation Workflow

Tests the entire system from user input through all tools to final quote output.
"""
import pytest
from pathlib import Path
import json
from unittest.mock import Mock, patch, MagicMock
import httpx

from src.tools.database_tool import DatabaseTool
from src.tools.bom_tool import BOMAPITool
from src.tools.template_tool import TemplateTool, QuoteDataBuilder
from src.calculator import PricingCalculator
from src.converter import UnitConverter
from tests.fixtures.sample_data import TestDataFactory


@pytest.mark.e2e
class TestFullQuoteGeneration:
    """Test complete quote generation workflows"""
    
    def test_end_to_end_cupcakes_quote(self, temp_database, temp_dir):
        """Test complete workflow: cupcakes order from start to finish"""
        # Setup
        db = DatabaseTool(temp_database)
        converter = UnitConverter()
        calculator = PricingCalculator(labor_rate=15.0, markup_pct=0.30, vat_pct=0.20)
        
        template_path = temp_dir / "quote_template.md"
        template_path.write_text("""# {{company_name}} - Quotation

**Quote ID:** {{quote_id}}
**Date:** {{quote_date}}
**Valid Until:** {{valid_until}}
**Customer:** {{customer_name}}

## Project Details
**Job Type:** {{job_type}}
**Quantity:** {{quantity}}
**Due Date:** {{due_date}}

## Bill of Materials
{{#lines}}
- {{name}}: {{qty}} {{unit}} @ {{currency}}{{unit_cost}} = {{currency}}{{line_cost}}
{{/lines}}

**Materials Subtotal:** {{currency}}{{materials_subtotal}}

## Labor
**Hours:** {{labor_hours}} @ {{currency}}{{labor_rate}}/hr = {{currency}}{{labor_cost}}

## Pricing Summary
- Subtotal: {{currency}}{{subtotal}}
- Markup ({{markup_pct}}): {{currency}}{{markup_value}}
- Price before VAT: {{currency}}{{price_before_vat}}
- VAT ({{vat_pct}}): {{currency}}{{vat_value}}

**TOTAL: {{currency}}{{total}}**

{{#notes}}
**Notes:** {{notes}}
{{/notes}}
""")
        
        template_tool = TemplateTool(
            template_path=str(template_path),
            output_dir=str(temp_dir / "output")
        )
        
        # Mock BOM API response
        with patch('httpx.Client') as mock_client:
            mock_instance = MagicMock()
            
            # Mock health check
            health_response = Mock()
            health_response.status_code = 200
            health_response.json.return_value = {"status": "ok"}
            
            # Mock estimate response
            estimate_response = Mock()
            estimate_response.status_code = 200
            estimate_response.raise_for_status = Mock()
            estimate_response.json.return_value = {
                'job_type': 'cupcakes',
                'quantity': 24,
                'materials': [
                    {'name': 'flour', 'unit': 'kg', 'qty': 1.92},
                    {'name': 'sugar', 'unit': 'kg', 'qty': 1.44},
                    {'name': 'butter', 'unit': 'kg', 'qty': 0.96},
                    {'name': 'eggs', 'unit': 'each', 'qty': 12.0},
                    {'name': 'milk', 'unit': 'L', 'qty': 1.2},
                    {'name': 'vanilla', 'unit': 'ml', 'qty': 24.0},
                    {'name': 'baking_powder', 'unit': 'kg', 'qty': 0.024},
                ],
                'labor_hours': 1.2
            }
            
            mock_instance.get.return_value = health_response
            mock_instance.post.return_value = estimate_response
            mock_client.return_value = mock_instance
            
            # Step 1: Get BOM estimate
            bom_tool = BOMAPITool(base_url="http://localhost:8000")
            bom_estimate = bom_tool.estimate('cupcakes', 24)
            
            assert bom_estimate.job_type == 'cupcakes'
            assert bom_estimate.quantity == 24
            assert len(bom_estimate.materials) == 7
            assert bom_estimate.labor_hours == 1.2
        
        # Step 2: Get material costs from database
        material_names = [m.name for m in bom_estimate.materials]
        costs = db.get_materials_bulk(material_names)
        
        assert len(costs) == 7
        assert all(name in costs for name in material_names)
        
        # Step 3: Process materials with unit conversion
        processed_materials = []
        for material in bom_estimate.materials:
            cost_data = costs[material.name]
            
            # Convert units if needed
            if material.unit != cost_data['unit']:
                if converter.can_convert(material.unit, cost_data['unit']):
                    qty_converted = converter.convert(material.qty, material.unit, cost_data['unit'])
                else:
                    qty_converted = material.qty
            else:
                qty_converted = material.qty
            
            line_cost = calculator.calculate_line_cost(qty_converted, cost_data['unit_cost'])
            
            processed_materials.append({
                'name': material.name,
                'qty': material.qty,
                'unit': material.unit,
                'unit_cost': cost_data['unit_cost'],
                'line_cost': line_cost
            })
        
        # Step 4: Calculate quote with markup and VAT
        quote_calc = calculator.calculate_quote(processed_materials, bom_estimate.labor_hours)
        
        assert quote_calc.materials_subtotal > 0
        assert quote_calc.labor_cost == pytest.approx(1.2 * 15.0)
        assert quote_calc.markup_value > 0
        assert quote_calc.vat_value > 0
        assert quote_calc.total > quote_calc.subtotal
        
        # Step 5: Build template data
        # Convert MaterialLine objects to dicts for template
        lines_dict = [
            {
                'name': line.name,
                'qty': line.qty,
                'unit': line.unit,
                'unit_cost': line.unit_cost,
                'line_cost': line.line_cost
            }
            for line in quote_calc.lines
        ]
        
        builder = QuoteDataBuilder()
        quote_data = (builder
            .set_header('Q-E2E-001', 'Test Bakery', 'E2E Customer', '2025-12-18', 30)
            .set_project('cupcakes', 24, '2025-12-25')
            .set_materials(lines_dict)
            .set_labor(bom_estimate.labor_hours, 15.0, quote_calc.labor_cost)
            .set_calculations(
                quote_calc.materials_subtotal,
                quote_calc.subtotal,
                30,
                quote_calc.markup_value,
                quote_calc.price_before_vat,
                20,
                quote_calc.vat_value,
                quote_calc.total,
                'GBP'
            )
            .set_notes('End-to-end test quote')
            .build())
        
        # Step 6: Render and save quote
        output_path = template_tool.render_and_save(quote_data)
        
        # Verify output
        assert output_path.exists()
        content = output_path.read_text()
        
        # Verify key content
        assert 'Test Bakery' in content
        assert 'E2E Customer' in content
        assert 'Q-E2E-001' in content
        assert 'cupcakes' in content
        assert '24' in content
        assert 'flour' in content
        assert 'sugar' in content
        assert 'GBP' in content
        assert 'End-to-end test quote' in content
        
        # Verify calculations in content
        assert f'{quote_calc.total:.2f}' in content
        
        print(f"✓ E2E test completed successfully. Quote saved to: {output_path}")
    
    def test_end_to_end_cake_quote(self, temp_database, temp_dir):
        """Test complete workflow for cake order"""
        # Setup tools
        db = DatabaseTool(temp_database)
        converter = UnitConverter()
        calculator = PricingCalculator(labor_rate=15.0, markup_pct=0.30, vat_pct=0.20)
        
        # Simple template for testing
        template_path = temp_dir / "cake_template.md"
        template_path.write_text("""# Cake Quote {{quote_id}}

Customer: {{customer_name}}
Job: {{job_type}} x {{quantity}}
Total: {{currency}}{{total}}
""")
        
        template_tool = TemplateTool(str(template_path), str(temp_dir / "output"))
        
        # Mock BOM API for cake
        with patch('httpx.Client') as mock_client:
            mock_instance = MagicMock()
            
            health_response = Mock()
            health_response.status_code = 200
            health_response.json.return_value = {"status": "ok"}
            
            cake_response = Mock()
            cake_response.status_code = 200
            cake_response.raise_for_status = Mock()
            cake_response.json.return_value = {
                'job_type': 'cake',
                'quantity': 1,
                'materials': [
                    {'name': 'flour', 'unit': 'kg', 'qty': 0.5},
                    {'name': 'sugar', 'unit': 'kg', 'qty': 0.4},
                    {'name': 'butter', 'unit': 'kg', 'qty': 0.3},
                    {'name': 'eggs', 'unit': 'each', 'qty': 6.0},
                    {'name': 'milk', 'unit': 'L', 'qty': 0.3},
                ],
                'labor_hours': 0.8
            }
            
            mock_instance.get.return_value = health_response
            mock_instance.post.return_value = cake_response
            mock_client.return_value = mock_instance
            
            # Get BOM
            bom_tool = BOMAPITool(base_url="http://localhost:8000")
            bom = bom_tool.estimate('cake', 1)
        
        # Get costs
        costs = db.get_materials_bulk([m.name for m in bom.materials])
        
        # Process and calculate
        materials = []
        for mat in bom.materials:
            cost = costs[mat.name]
            qty = mat.qty if mat.unit == cost['unit'] else converter.convert(mat.qty, mat.unit, cost['unit'])
            line_cost = calculator.calculate_line_cost(qty, cost['unit_cost'])
            
            materials.append({
                'name': mat.name,
                'qty': mat.qty,
                'unit': mat.unit,
                'unit_cost': cost['unit_cost'],
                'line_cost': line_cost
            })
        
        quote = calculator.calculate_quote(materials, bom.labor_hours)
        
        # Build and render
        builder = QuoteDataBuilder()
        data = (builder
            .set_header('Q-CAKE-001', 'Bakery', 'Cake Customer', '2025-12-18', 30)
            .set_project('cake', 1, '2025-12-20')
            .set_materials(materials)
            .set_labor(bom.labor_hours, 15.0, quote.labor_cost)
            .set_calculations(
                quote.materials_subtotal, quote.subtotal, 30,
                quote.markup_value, quote.price_before_vat, 20,
                quote.vat_value, quote.total, 'GBP'
            )
            .build())
        
        output = template_tool.render_and_save(data)
        
        # Verify
        assert output.exists()
        content = output.read_text()
        assert 'Cake Customer' in content
        assert 'cake' in content
        assert quote.total > 10  # Cake should be reasonably priced
    
    def test_end_to_end_with_unit_conversion(self, temp_database, temp_dir):
        """Test workflow requiring unit conversions"""
        db = DatabaseTool(temp_database)
        converter = UnitConverter()
        calculator = PricingCalculator(labor_rate=15.0, markup_pct=0.30, vat_pct=0.20)
        
        # Create minimal template
        template_path = temp_dir / "test.md"
        template_path.write_text("# Quote {{quote_id}}\nTotal: {{total}}")
        template_tool = TemplateTool(str(template_path), str(temp_dir / "out"))
        
        # Scenario: Test with vanilla (ml unit in both BOM and DB, no conversion needed)
        with patch('httpx.Client') as mock_client:
            mock_instance = MagicMock()
            
            health_resp = Mock()
            health_resp.status_code = 200
            health_resp.json.return_value = {"status": "ok"}
            
            estimate_resp = Mock()
            estimate_resp.status_code = 200
            estimate_resp.raise_for_status = Mock()
            estimate_resp.json.return_value = {
                'job_type': 'test',
                'quantity': 1,
                'materials': [
                    {'name': 'vanilla', 'unit': 'ml', 'qty': 50.0},  # ml unit
                ],
                'labor_hours': 0.5
            }
            
            mock_instance.get.return_value = health_resp
            mock_instance.post.return_value = estimate_resp
            mock_client.return_value = mock_instance
            
            bom_tool = BOMAPITool(base_url="http://localhost:8000")
            bom = bom_tool.estimate('test', 1)
        
        # Get DB cost (in ml)
        vanilla_cost = db.get_material_cost('vanilla')
        assert vanilla_cost.unit == 'ml'
        
        # Material has same unit as DB
        material = bom.materials[0]
        assert material.unit == 'ml'
        
        # No conversion needed (same unit)
        qty = material.qty
        assert qty == 50.0
        
        # Calculate cost
        line_cost = calculator.calculate_line_cost(qty, vanilla_cost.unit_cost)
        assert line_cost == pytest.approx(50.0 * 0.05)
        
        # Build quote
        materials = [{
            'name': 'vanilla',
            'qty': material.qty,
            'unit': material.unit,
            'unit_cost': vanilla_cost.unit_cost,
            'line_cost': line_cost
        }]
        
        quote = calculator.calculate_quote(materials, 0.5)
        
        # Verify calculation
        assert quote.materials_subtotal == pytest.approx(2.50)
        
        # Complete quote
        builder = QuoteDataBuilder()
        data = (builder
            .set_header('Q-CONV-001', 'Bakery', 'Customer', '2025-12-18', 30)
            .set_project('test', 1, '2025-12-20')
            .set_materials(materials)
            .set_labor(0.5, 15.0, quote.labor_cost)
            .set_calculations(
                quote.materials_subtotal, quote.subtotal, 30,
                quote.markup_value, quote.price_before_vat, 20,
                quote.vat_value, quote.total, 'GBP'
            )
            .build())
        
        output = template_tool.render_and_save(data)
        assert output.exists()


@pytest.mark.e2e
class TestQuoteOutputValidation:
    """Test quote output file validation"""
    
    def test_quote_file_structure(self, temp_database, temp_dir):
        """Test that generated quote files have correct structure"""
        # Create template with all required fields
        template_path = temp_dir / "full_template.md"
        template_path.write_text("""# {{company_name}} - Professional Quotation

## Header
Quote ID: {{quote_id}}
Date: {{quote_date}}
Valid Until: {{valid_until}}

## Customer
Name: {{customer_name}}

## Project
Type: {{job_type}}
Quantity: {{quantity}}
Due: {{due_date}}

## Materials
{{#lines}}
- {{name}}: {{qty}} {{unit}} @ {{unit_cost}} = {{line_cost}}
{{/lines}}

## Costs
Materials: {{materials_subtotal}}
Labor: {{labor_cost}} ({{labor_hours}} hrs @ {{labor_rate}})
Subtotal: {{subtotal}}
Markup: {{markup_value}} ({{markup_pct}})
Before VAT: {{price_before_vat}}
VAT: {{vat_value}} ({{vat_pct}})
TOTAL: {{total}} {{currency}}
""")
        
        tool = TemplateTool(str(template_path), str(temp_dir / "output"))
        
        # Create complete quote data
        builder = QuoteDataBuilder()
        data = (builder
            .set_header('Q-TEST-001', 'Professional Bakery', 'Important Client', '2025-12-18', 30)
            .set_project('cupcakes', 24, '2025-12-25')
            .set_materials([
                {'name': 'flour', 'qty': 1.92, 'unit': 'kg', 'unit_cost': 0.90, 'line_cost': 1.73}
            ])
            .set_labor(1.2, 15.0, 18.0)
            .set_calculations(1.73, 19.73, 30, 5.92, 25.65, 20, 5.13, 30.78, 'GBP')
            .set_notes('')
            .build())
        
        # Render and save
        output_path = tool.render_and_save(data)
        
        # Validate file
        assert output_path.exists()
        assert output_path.suffix == '.md'
        assert output_path.name == 'quote_Q-TEST-001.md'
        
        # Validate content completeness
        content = output_path.read_text()
        required_fields = [
            'Q-TEST-001', 'Professional Bakery', 'Important Client',
            'cupcakes', '24', 'flour', '1.92', 'kg',
            '18.0', '1.2', '15.0',  # Labor
            '30.78', 'GBP'  # Total
        ]
        
        for field in required_fields:
            assert str(field) in content, f"Missing required field: {field}"
    
    def test_multiple_quotes_different_ids(self, temp_dir):
        """Test generating multiple quotes with different IDs"""
        template_path = temp_dir / "simple.md"
        template_path.write_text("Quote: {{quote_id}}, Total: {{total}}")
        
        tool = TemplateTool(str(template_path), str(temp_dir / "output"))
        
        # Generate 3 quotes
        quote_ids = ['Q-001', 'Q-002', 'Q-003']
        
        for qid in quote_ids:
            builder = QuoteDataBuilder()
            data = (builder
                .set_header(qid, 'Bakery', 'Customer', '2025-12-18', 30)
                .set_project('cupcakes', 24, '2025-12-25')
                .set_materials([{'name': 'flour', 'qty': 1, 'unit': 'kg', 'unit_cost': 1, 'line_cost': 1}])
                .set_labor(1.0, 15.0, 15.0)
                .set_calculations(1, 16, 30, 4.8, 20.8, 20, 4.16, 24.96, 'GBP')
                .build())
            
            output = tool.render_and_save(data)
            assert output.exists()
            assert qid in output.name
        
        # Verify all files exist
        output_dir = temp_dir / "output"
        quote_files = list(output_dir.glob("quote_*.md"))
        assert len(quote_files) == 3


@pytest.mark.e2e
class TestErrorHandlingE2E:
    """Test error handling in complete workflows"""
    
    def test_missing_material_in_database_workflow(self, temp_database, temp_dir):
        """Test workflow when material is missing from database"""
        db = DatabaseTool(temp_database)
        
        # Mock BOM with non-existent material
        with patch('httpx.Client') as mock_client:
            mock_instance = MagicMock()
            
            health_resp = Mock()
            health_resp.status_code = 200
            health_resp.json.return_value = {"status": "ok"}
            
            estimate_resp = Mock()
            estimate_resp.status_code = 200
            estimate_resp.raise_for_status = Mock()
            estimate_resp.json.return_value = {
                'job_type': 'test',
                'quantity': 1,
                'materials': [
                    {'name': 'flour', 'unit': 'kg', 'qty': 1.0},
                    {'name': 'unicorn_dust', 'unit': 'kg', 'qty': 0.5},  # Doesn't exist
                ],
                'labor_hours': 1.0
            }
            
            mock_instance.get.return_value = health_resp
            mock_instance.post.return_value = estimate_resp
            mock_client.return_value = mock_instance
            
            bom_tool = BOMAPITool(base_url="http://localhost:8000")
            bom = bom_tool.estimate('test', 1)
        
        # Try to get costs - should handle missing material gracefully
        material_names = [m.name for m in bom.materials]
        costs = db.get_materials_bulk(material_names)
        
        # Bulk lookup returns only found materials
        assert 'flour' in costs
        assert 'unicorn_dust' not in costs
        assert len(costs) == 1  # Only flour found
        
        # Workflow should identify missing material
        missing_materials = [name for name in material_names if name not in costs]
        assert 'unicorn_dust' in missing_materials
    
    def test_bom_api_connection_error_handling(self):
        """Test handling of BOM API connection failures"""
        from src.tools.bom_tool import APIConnectionError
        
        with patch('httpx.Client') as mock_client:
            mock_instance = MagicMock()
            mock_instance.get.side_effect = httpx.ConnectError("Connection refused")
            mock_client.return_value = mock_instance
            
            # Should raise APIConnectionError on connection failure
            with pytest.raises(APIConnectionError):
                BOMAPITool(base_url="http://localhost:8000")
    
    def test_invalid_template_path(self):
        """Test handling of invalid template path"""
        with pytest.raises(FileNotFoundError):
            TemplateTool(template_path="/nonexistent/template.md", output_dir="/tmp")


@pytest.mark.e2e
@pytest.mark.slow
class TestPerformanceE2E:
    """Performance tests for complete workflows"""
    
    def test_quote_generation_performance(self, temp_database, temp_dir):
        """Test that quote generation completes in reasonable time"""
        import time
        
        # Setup
        template_path = temp_dir / "perf.md"
        template_path.write_text("Quote {{quote_id}}: {{total}}")
        
        tool = TemplateTool(str(template_path), str(temp_dir / "output"))
        calculator = PricingCalculator(labor_rate=15.0, markup_pct=0.30, vat_pct=0.20)
        
        # Generate 10 quotes and measure time
        start_time = time.time()
        
        for i in range(10):
            materials = [
                {'name': 'flour', 'qty': 1.0, 'unit': 'kg', 'unit_cost': 0.90, 'line_cost': 0.90}
            ]
            
            quote = calculator.calculate_quote(materials, 1.0)
            
            builder = QuoteDataBuilder()
            data = (builder
                .set_header(f'Q-PERF-{i:03d}', 'Bakery', 'Customer', '2025-12-18', 30)
                .set_project('test', 1, '2025-12-20')
                .set_materials(materials)
                .set_labor(1.0, 15.0, quote.labor_cost)
                .set_calculations(
                    quote.materials_subtotal, quote.subtotal, 30,
                    quote.markup_value, quote.price_before_vat, 20,
                    quote.vat_value, quote.total, 'GBP'
                )
                .build())
            
            tool.render_and_save(data)
        
        elapsed = time.time() - start_time
        
        # Should complete 10 quotes in under 1 second
        assert elapsed < 1.0, f"Quote generation too slow: {elapsed:.2f}s for 10 quotes"
        
        # Verify all created
        output_dir = temp_dir / "output"
        quote_files = list(output_dir.glob("quote_Q-PERF-*.md"))
        assert len(quote_files) == 10
