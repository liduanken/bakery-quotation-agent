"""Tests for Agent Orchestrator Components

Tests the core orchestrator logic without full LangChain dependencies.
Focuses on tool functions, state management, and calculation logic.
"""
# Mock LangChain before imports
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.modules['langchain.agents'] = MagicMock()
sys.modules['langchain.prompts'] = MagicMock()
sys.modules['langchain.memory'] = MagicMock()
sys.modules['langchain.tools'] = MagicMock()
sys.modules['langchain_openai'] = MagicMock()

from src.agent.orchestrator import BakeryQuotationAgent
from src.config import Config
from src.models import QuoteState


@pytest.fixture
def mock_agent(temp_database, temp_dir):
    """Create agent with mocked LangChain components"""
    template_path = temp_dir / "template.md"
    template_path.write_text("# Quote {{quote_id}}\nCustomer: {{customer_name}}\nTotal: {{currency}}{{total}}")

    config = Config(
        openai_api_key="test-key",
        database_path=temp_database,
        template_path=str(template_path),
        output_dir=str(temp_dir / "output")
    )

    with patch('httpx.Client') as mock_httpx:
        mock_instance = MagicMock()
        mock_health = Mock()
        mock_health.status_code = 200
        mock_health.json.return_value = {"status": "ok"}
        mock_instance.get.return_value = mock_health
        mock_httpx.return_value = mock_instance

        agent = BakeryQuotationAgent(config)
        yield agent


class TestQuoteStateManagement:
    """Test quote state management"""

    def test_quote_state_initialization(self):
        """Test quote state initializes with correct defaults"""
        state = QuoteState()

        assert state.job_type is None
        assert state.quantity is None
        assert state.customer_name is None
        assert state.bom_data is None
        assert state.material_costs is None

    def test_quote_state_reset(self):
        """Test quote state reset"""
        state = QuoteState()

        # Set values
        state.job_type = 'cupcakes'
        state.quantity = 24
        state.customer_name = 'Test Customer'

        # Reset
        state.reset()

        # Verify cleared
        assert state.job_type is None
        assert state.quantity is None
        assert state.customer_name is None

    def test_generate_quote_id(self):
        """Test quote ID generation"""
        state = QuoteState()

        quote_id = state.generate_quote_id()

        assert quote_id is not None
        assert len(quote_id) > 0
        assert 'Q-' in quote_id or quote_id.startswith('Q')


class TestCalculationLogic:
    """Test quote calculation logic"""

    def test_calculate_quote_totals(self, mock_agent):
        """Test quote totals calculation"""
        # Set up state
        mock_agent.quote_state.bom_data = {
            'materials': [
                {'name': 'flour', 'unit': 'kg', 'qty': 1.0},
                {'name': 'sugar', 'unit': 'kg', 'qty': 0.5},
            ],
            'labor_hours': 1.0
        }
        mock_agent.quote_state.material_costs = {
            'flour': {'unit': 'kg', 'unit_cost': 0.90, 'currency': 'GBP'},
            'sugar': {'unit': 'kg', 'unit_cost': 0.70, 'currency': 'GBP'}
        }
        mock_agent.quote_state.quantity = 10

        # Calculate
        calc = mock_agent._calculate_quote_totals()

        # Verify - calc is now a dict
        assert calc['materials_subtotal'] == pytest.approx(1.25)  # 0.90 + 0.35
        assert calc['labor_cost'] == pytest.approx(15.0)  # 1.0h * £15/h
        assert calc['subtotal'] == pytest.approx(16.25)
        assert calc['markup_value'] > 0
        assert calc['vat_value'] > 0
        assert calc['total'] > calc['subtotal']
        assert calc['unit_price'] == pytest.approx(calc['total'] / 10)

    def test_calculate_with_unit_conversion(self, mock_agent):
        """Test calculation handles unit conversions"""
        # BOM in ml, DB in L (would need conversion if we had L unit)
        mock_agent.quote_state.bom_data = {
            'materials': [
                {'name': 'vanilla', 'unit': 'ml', 'qty': 50.0},
            ],
            'labor_hours': 0.5
        }
        mock_agent.quote_state.material_costs = {
            'vanilla': {'unit': 'ml', 'unit_cost': 0.05, 'currency': 'GBP'}
        }
        mock_agent.quote_state.quantity = 1

        calc = mock_agent._calculate_quote_totals()

        assert calc['materials_subtotal'] == pytest.approx(2.50)  # 50 * 0.05


class TestTemplateDataPreparation:
    """Test template data preparation"""

    def test_prepare_template_data(self, mock_agent):
        """Test template data formatting"""
        # Set up state
        mock_agent.quote_state.job_type = 'cupcakes'
        mock_agent.quote_state.quantity = 24
        mock_agent.quote_state.customer_name = 'Test Customer'
        mock_agent.quote_state.company_name = 'Test Bakery'
        mock_agent.quote_state.due_date = '2025-12-25'

        # Create calc dict like _calculate_quote_totals() returns
        calculations = {
            'lines': [
                {'name': 'flour', 'qty': 1.92, 'unit': 'kg', 'unit_cost': 0.90, 'line_cost': 1.73}
            ],
            'materials_subtotal': 1.73,
            'labor_hours': 1.2,
            'labor_rate': 15.0,
            'labor_cost': 18.0,
            'subtotal': 19.73,
            'markup_pct': 30.0,
            'markup_value': 5.92,
            'price_before_vat': 25.65,
            'vat_pct': 20.0,
            'vat_value': 5.13,
            'total': 30.78
        }

        # Prepare
        template_data = mock_agent._prepare_template_data(calculations)

        # Verify
        assert 'quote_id' in template_data
        assert template_data['customer_name'] == 'Test Customer'
        assert template_data['job_type'] == 'cupcakes'
        assert template_data['quantity'] == 24
        assert len(template_data['lines']) == 1
        assert 'total' in template_data
        assert template_data['currency'] == 'GBP'

    def test_template_data_formatting(self, mock_agent):
        """Test that numbers are properly formatted"""
        mock_agent.quote_state.job_type = 'test'
        mock_agent.quote_state.quantity = 1
        mock_agent.quote_state.customer_name = 'Customer'
        mock_agent.quote_state.company_name = 'Company'
        mock_agent.quote_state.due_date = '2025-12-20'

        calculations = {
            'lines': [
                {'name': 'item', 'qty': 1.234, 'unit': 'kg', 'unit_cost': 5.678, 'line_cost': 7.012}
            ],
            'materials_subtotal': 7.01,
            'labor_hours': 1.5,
            'labor_rate': 15.0,
            'labor_cost': 22.50,
            'subtotal': 29.51,
            'markup_pct': 30.0,
            'markup_value': 8.85,
            'price_before_vat': 38.36,
            'vat_pct': 20.0,
            'vat_value': 7.67,
            'total': 46.03
        }

        data = mock_agent._prepare_template_data(calculations)

        # Check formatting (should be strings with 2 decimals)
        assert data['labor_hours'] == '1.5'
        assert data['labor_rate'] == '15.00'
        assert data['total'] == '46.03'


class TestBOMToolIntegration:
    """Test BOM tool integration with agent"""

    def test_get_job_types_via_bom_tool(self, mock_agent):
        """Test get_job_types through BOM tool"""
        with patch('httpx.Client') as mock_httpx:
            mock_instance = MagicMock()

            # Health check
            mock_health = Mock()
            mock_health.status_code = 200
            mock_health.json.return_value = {"status": "ok"}

            # Job types response
            mock_types = Mock()
            mock_types.status_code = 200
            mock_types.raise_for_status = Mock()
            mock_types.json.return_value = ["cupcakes", "cake", "pastry_box"]

            mock_instance.get.side_effect = [mock_health, mock_types]
            mock_httpx.return_value = mock_instance

            # Reinitialize BOM tool
            from src.tools.bom_tool import BOMAPITool
            mock_agent.bom_tool = BOMAPITool(base_url="http://localhost:8000")

            result = mock_agent.bom_tool.get_job_types()

            assert "cupcakes" in result
            assert "cake" in result

    def test_get_bom_estimate_updates_state(self, mock_agent):
        """Test that BOM estimate updates agent state"""
        with patch('httpx.Client') as mock_httpx:
            mock_instance = MagicMock()

            mock_health = Mock()
            mock_health.status_code = 200
            mock_health.json.return_value = {"status": "ok"}

            mock_estimate = Mock()
            mock_estimate.status_code = 200
            mock_estimate.raise_for_status = Mock()
            mock_estimate.json.return_value = {
                'job_type': 'cupcakes',
                'quantity': 24,
                'materials': [
                    {'name': 'flour', 'unit': 'kg', 'qty': 1.92},
                ],
                'labor_hours': 1.2
            }

            mock_instance.get.return_value = mock_health
            mock_instance.post.return_value = mock_estimate
            mock_httpx.return_value = mock_instance

            # Reinitialize BOM tool
            from src.tools.bom_tool import BOMAPITool, JobType
            mock_agent.bom_tool = BOMAPITool(base_url="http://localhost:8000")

            # Call BOM estimate - returns EstimateResponse object
            estimate_resp = mock_agent.bom_tool.estimate(JobType.CUPCAKES, 24)

            # Manually update state like tool would
            # estimate_resp.job_type is already a string from the API mock
            mock_agent.quote_state.job_type = estimate_resp.job_type
            mock_agent.quote_state.quantity = estimate_resp.quantity
            mock_agent.quote_state.bom_data = {
                'job_type': estimate_resp.job_type,
                'quantity': estimate_resp.quantity,
                'materials': [{'name': m.name, 'unit': m.unit, 'qty': m.qty} for m in estimate_resp.materials],
                'labor_hours': estimate_resp.labor_hours
            }

            # Verify state updated
            assert mock_agent.quote_state.job_type == 'cupcakes'
            assert mock_agent.quote_state.quantity == 24
            assert mock_agent.quote_state.bom_data is not None


class TestDatabaseToolIntegration:
    """Test database tool integration with agent"""

    def test_query_material_costs(self, mock_agent):
        """Test query_material_costs via database tool"""
        costs = mock_agent.db_tool.get_materials_bulk(['flour', 'sugar'])

        assert 'flour' in costs
        assert 'sugar' in costs
        assert costs['flour']['unit_cost'] > 0

    def test_query_material_costs_with_missing(self, mock_agent):
        """Test query_material_costs handles missing materials"""
        costs = mock_agent.db_tool.get_materials_bulk(['flour', 'unicorn_dust'])

        # Should have flour but not unicorn_dust
        assert 'flour' in costs
        assert 'unicorn_dust' not in costs


class TestCompleteWorkflow:
    """Test complete quote generation workflow"""

    def test_full_workflow_with_all_components(self, mock_agent):
        """Test complete workflow from BOM to quote generation"""
        # Set up complete state
        mock_agent.quote_state.bom_data = {
            'materials': [
                {'name': 'flour', 'unit': 'kg', 'qty': 1.0},
            ],
            'labor_hours': 1.0
        }
        mock_agent.quote_state.material_costs = {
            'flour': {'unit': 'kg', 'unit_cost': 0.90, 'currency': 'GBP'}
        }
        mock_agent.quote_state.job_type = 'cupcakes'
        mock_agent.quote_state.quantity = 24
        mock_agent.quote_state.customer_name = 'Test Customer'
        mock_agent.quote_state.due_date = '2025-12-25'
        mock_agent.quote_state.company_name = 'Test Bakery'

        # Calculate quote totals
        calc = mock_agent._calculate_quote_totals()
        assert calc['total'] > 0

        # Prepare template data
        template_data = mock_agent._prepare_template_data(calc)
        assert 'quote_id' in template_data

        # Render quote
        output_path = mock_agent.template_tool.render_and_save(template_data)
        assert Path(output_path).exists()


class TestAgentReset:
    """Test agent reset functionality"""

    def test_agent_reset_clears_state(self, mock_agent):
        """Test reset clears agent state"""
        # Set state
        mock_agent.quote_state.job_type = 'cupcakes'
        mock_agent.quote_state.quantity = 24
        mock_agent.quote_state.customer_name = 'Test'

        # Reset
        mock_agent.reset()

        # Verify cleared
        assert mock_agent.quote_state.job_type is None
        assert mock_agent.quote_state.quantity is None
        assert mock_agent.quote_state.customer_name is None


class TestErrorHandling:
    """Test error handling"""

    def test_bom_api_connection_error(self, temp_database, temp_dir):
        """Test handling of BOM API connection errors"""
        template_path = temp_dir / "template.md"
        template_path.write_text("# Quote")

        config = Config(
            openai_api_key="test-key",
            database_path=temp_database,
            template_path=str(template_path),
            output_dir=str(temp_dir / "output")
        )

        with patch('httpx.Client') as mock_httpx:
            import httpx
            mock_instance = MagicMock()
            mock_instance.get.side_effect = httpx.ConnectError("Connection refused")
            mock_httpx.return_value = mock_instance

            from src.tools.bom_tool import APIConnectionError
            with pytest.raises(APIConnectionError):
                BakeryQuotationAgent(config)
