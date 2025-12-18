"""Tests for template renderer tool"""
import pytest
from pathlib import Path
import tempfile
from src.tools.template_tool import (
    TemplateTool,
    QuoteDataBuilder,
    TemplateRenderError
)


@pytest.fixture
def temp_dir():
    """Create temporary directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def template_file(temp_dir):
    """Create test template file"""
    template_path = temp_dir / "test_template.md"
    template_content = """# {{company_name}} - Quotation

**Quote ID:** {{quote_id}}
**Date:** {{quote_date}}
**Customer:** {{customer_name}}
**Job Type:** {{job_type}}
**Quantity:** {{quantity}}

## Materials
{{#lines}}
- {{name}}: {{qty}} {{unit}} @ {{unit_cost}} = {{line_cost}}
{{/lines}}

**Total:** {{currency}}{{total}}

{{#notes}}
**Notes:** {{notes}}
{{/notes}}
"""
    template_path.write_text(template_content)
    return template_path


@pytest.fixture
def sample_data():
    """Sample quote data"""
    return {
        'quote_id': 'Q001',
        'quote_date': '2025-12-18',
        'valid_until': '2026-01-17',
        'company_name': 'Test Bakery',
        'customer_name': 'Test Customer',
        'job_type': 'cupcakes',
        'quantity': 24,
        'due_date': '2025-12-25',
        'lines': [
            {'name': 'flour', 'qty': 1.92, 'unit': 'kg', 'unit_cost': 0.90, 'line_cost': 1.73},
            {'name': 'sugar', 'qty': 1.44, 'unit': 'kg', 'unit_cost': 0.70, 'line_cost': 1.01},
        ],
        'materials_subtotal': 2.74,
        'labor_hours': 1.2,
        'labor_rate': 15.0,
        'labor_cost': 18.0,
        'subtotal': 20.74,
        'markup_pct': 30,
        'markup_value': 6.22,
        'price_before_vat': 26.96,
        'vat_pct': 20,
        'vat_value': 5.39,
        'total': 32.35,
        'currency': 'GBP',
        'notes': ''
    }


class TestTemplateTool:
    """Test suite for template tool"""
    
    def test_initialization(self, template_file, temp_dir):
        """Test tool initialization"""
        tool = TemplateTool(
            template_path=str(template_file),
            output_dir=str(temp_dir / "output")
        )
        assert tool.template_path == template_file
        assert tool.output_dir == temp_dir / "output"
    
    def test_initialization_creates_output_dir(self, template_file, temp_dir):
        """Test output directory creation"""
        output_dir = temp_dir / "output"
        assert not output_dir.exists()
        
        tool = TemplateTool(
            template_path=str(template_file),
            output_dir=str(output_dir)
        )
        assert output_dir.exists()
    
    def test_render_success(self, template_file, temp_dir, sample_data):
        """Test successful template rendering"""
        tool = TemplateTool(
            template_path=str(template_file),
            output_dir=str(temp_dir / "output")
        )
        
        result = tool.render(sample_data)
        
        assert 'Test Bakery' in result
        assert 'Q001' in result
        assert 'Test Customer' in result
        assert 'flour' in result
        assert '32.35' in result
    
    def test_render_missing_required_field(self, template_file, temp_dir):
        """Test rendering with missing required field"""
        tool = TemplateTool(
            template_path=str(template_file),
            output_dir=str(temp_dir / "output")
        )
        
        incomplete_data = {'quote_id': 'Q001'}
        
        with pytest.raises(TemplateRenderError):
            tool.render(incomplete_data)
    
    def test_save_success(self, template_file, temp_dir):
        """Test saving rendered content"""
        tool = TemplateTool(
            template_path=str(template_file),
            output_dir=str(temp_dir / "output")
        )
        
        content = "Test quote content"
        output_path = tool.save(content, quote_id='Q001')
        
        assert output_path.exists()
        assert output_path.read_text() == content
        assert 'Q001' in output_path.name
    
    def test_render_and_save(self, template_file, temp_dir, sample_data):
        """Test render and save combined"""
        tool = TemplateTool(
            template_path=str(template_file),
            output_dir=str(temp_dir / "output")
        )
        
        output_path = tool.render_and_save(sample_data)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert 'Test Bakery' in content
        assert 'Q001' in content
    
    def test_validate_template_success(self, template_file, temp_dir):
        """Test template validation"""
        tool = TemplateTool(
            template_path=str(template_file),
            output_dir=str(temp_dir / "output")
        )
        
        # validate_template checks for missing placeholders, not missing fields
        missing = tool.validate_template()
        # Our test template has all required placeholders
        assert len(missing) == 0
    
    def test_validate_template_missing_file(self, temp_dir):
        """Test validation with missing template"""
        # TemplateTool.__init__ raises FileNotFoundError if template doesn't exist
        with pytest.raises(FileNotFoundError):
            TemplateTool(
                template_path=str(temp_dir / "nonexistent.md"),
                output_dir=str(temp_dir / "output")
            )
    
    def test_data_formatting(self, template_file, temp_dir):
        """Test data formatting"""
        tool = TemplateTool(
            template_path=str(template_file),
            output_dir=str(temp_dir / "output")
        )
        
        data = {
            'quote_id': 'Q001',
            'quote_date': '2025-12-18',
            'valid_until': '2026-01-17',
            'company_name': 'Test',
            'customer_name': 'Customer',
            'job_type': 'cupcakes',
            'quantity': 24,
            'due_date': '2025-12-25',
            'lines': [],
            'materials_subtotal': 10.5,  # Should format to 10.50
            'labor_hours': 1.2,
            'labor_rate': 15.0,
            'labor_cost': 18.0,
            'subtotal': 28.5,
            'markup_pct': 30,
            'markup_value': 8.55,
            'price_before_vat': 37.05,
            'vat_pct': 20,
            'vat_value': 7.41,
            'total': 44.46,
            'currency': 'GBP',
            'notes': ''
        }
        
        formatted = tool._format_data(data)
        
        # Check currency formatting (2 decimals)
        assert formatted['materials_subtotal'] == '10.50'
        assert formatted['total'] == '44.46'


class TestQuoteDataBuilder:
    """Test suite for QuoteDataBuilder"""
    
    def test_builder_complete_flow(self):
        """Test complete builder workflow"""
        builder = QuoteDataBuilder()
        
        data = (builder
                .set_header('Q001', 'Test Bakery', 'Test Customer', '2025-12-18', 30)
                .set_project('cupcakes', 24, '2025-12-25')
                .set_materials([
                    {'name': 'flour', 'qty': 1.92, 'unit': 'kg', 'unit_cost': 0.90, 'line_cost': 1.73}
                ])
                .set_labor(1.2, 15.0, 18.0)
                .set_calculations(1.73, 19.73, 30, 5.92, 25.65, 20, 5.13, 30.78, 'GBP')
                .set_notes('')
                .build())
        
        assert data['quote_id'] == 'Q001'
        assert data['company_name'] == 'Test Bakery'
        assert data['total'] == 30.78
    
    def test_builder_validation_error(self):
        """Test builder validation"""
        builder = QuoteDataBuilder()
        
        # Missing required fields
        with pytest.raises(ValueError):
            builder.build()
    
    def test_builder_set_header(self):
        """Test set_header method"""
        builder = QuoteDataBuilder()
        result = builder.set_header('Q001', 'Bakery Co', 'Customer Name', '2025-12-18', 30)
        
        assert result is builder  # Should return self for chaining
        assert builder.data['quote_id'] == 'Q001'
        assert builder.data['company_name'] == 'Bakery Co'
        assert builder.data['customer_name'] == 'Customer Name'
        assert builder.data['quote_date'] == '2025-12-18'
        assert 'valid_until' in builder.data
    
    def test_builder_set_project(self):
        """Test set_project method"""
        builder = QuoteDataBuilder()
        result = builder.set_project('cupcakes', 24, '2025-12-25')
        
        assert result is builder
        assert builder.data['job_type'] == 'cupcakes'
        assert builder.data['quantity'] == 24
        assert builder.data['due_date'] == '2025-12-25'
    
    def test_builder_set_materials(self):
        """Test set_materials method"""
        builder = QuoteDataBuilder()
        lines = [{'name': 'flour', 'qty': 1.0, 'unit': 'kg', 'unit_cost': 0.90, 'line_cost': 0.90}]
        
        result = builder.set_materials(lines)
        
        assert result is builder
        assert len(builder.data['lines']) == 1
        assert builder.data['lines'][0]['name'] == 'flour'
    
    def test_builder_set_labor(self):
        """Test set_labor method"""
        builder = QuoteDataBuilder()
        result = builder.set_labor(1.5, 15.0, 22.5)
        
        assert result is builder
        assert builder.data['labor_hours'] == 1.5
        assert builder.data['labor_rate'] == 15.0
        assert builder.data['labor_cost'] == 22.5
    
    def test_builder_set_calculations(self):
        """Test set_calculations method"""
        builder = QuoteDataBuilder()
        result = builder.set_calculations(
            materials_subtotal=50,
            subtotal=100,
            markup_pct=30,
            markup_value=30,
            price_before_vat=130,
            vat_pct=20,
            vat_value=26,
            total=156,
            currency='GBP'
        )
        
        assert result is builder
        assert builder.data['materials_subtotal'] == 50
        assert builder.data['subtotal'] == 100
        assert builder.data['markup_pct'] == 30
        assert builder.data['total'] == 156
    
    def test_builder_set_notes(self):
        """Test set_notes method"""
        builder = QuoteDataBuilder()
        result = builder.set_notes('Special instructions')
        
        assert result is builder
        assert builder.data['notes'] == 'Special instructions'
    
    def test_builder_partial_data(self):
        """Test builder with partial data"""
        builder = QuoteDataBuilder()
        builder.set_header('Q001', 'Company', 'Customer', '2025-12-18', 30)
        
        # Should fail validation on build (missing job_type, quantity, total, currency)
        with pytest.raises(ValueError):
            builder.build()


class TestTemplateIntegration:
    """Integration tests for template tool"""
    
    def test_full_quote_rendering(self, template_file, temp_dir):
        """Test complete quote rendering workflow"""
        tool = TemplateTool(
            template_path=str(template_file),
            output_dir=str(temp_dir / "output")
        )
        
        # Build data with builder
        builder = QuoteDataBuilder()
        data = (builder
                .set_header('Q001', 'My Bakery', 'John Doe', '2025-12-18', 30)
                .set_project('cupcakes', 24, '2025-12-25')
                .set_materials([
                    {'name': 'flour', 'qty': 1.92, 'unit': 'kg', 'unit_cost': 0.90, 'line_cost': 1.73},
                    {'name': 'sugar', 'qty': 1.44, 'unit': 'kg', 'unit_cost': 0.70, 'line_cost': 1.01},
                ])
                .set_labor(1.2, 15.0, 18.0)
                .set_calculations(2.74, 20.74, 30, 6.22, 26.96, 20, 5.39, 32.35, 'GBP')
                .set_notes('Please deliver by 9 AM')
                .build())
        
        # Render and save
        output_path = tool.render_and_save(data)
        
        # Verify output
        assert output_path.exists()
        content = output_path.read_text()
        assert 'My Bakery' in content
        assert 'John Doe' in content
        assert 'cupcakes' in content
        assert '24' in content
        assert 'flour' in content
        assert '32.35' in content
        # Notes are conditionally rendered, check if present
        if data.get('notes'):
            assert 'Please deliver by 9 AM' in content
    
    def test_error_handling(self, temp_dir):
        """Test error handling with invalid data"""
        # Create template with required field
        template_path = temp_dir / "template.md"
        template_path.write_text("{{required_field}}")
        
        tool = TemplateTool(
            template_path=str(template_path),
            output_dir=str(temp_dir / "output")
        )
        
        # Missing required field
        with pytest.raises(TemplateRenderError):
            tool.render({})
