"""Tests for BOM API tool"""
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from src.tools.bom_tool import (
    APIConnectionError,
    BOMAPITool,
    EstimateRequest,
    EstimateResponse,
    InvalidJobTypeError,
    JobType,
    Material,
)


@pytest.fixture
def mock_health_response():
    """Mock successful health check response"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}
    return mock_response


@pytest.fixture
def mock_httpx_client(mock_health_response):
    """Mock httpx client with health check"""
    with patch('httpx.Client') as mock_client:
        mock_instance = MagicMock()
        # Mock the health check that happens in __init__
        mock_instance.get.return_value = mock_health_response
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def bom_tool(mock_httpx_client):
    """Create BOM API tool with mocked client"""
    return BOMAPITool(base_url="http://localhost:8000")


class TestBOMAPITool:
    """Test suite for BOM API tool"""

    def test_initialization(self, mock_httpx_client):
        """Test tool initialization"""
        tool = BOMAPITool(base_url="http://localhost:8000")
        assert tool.base_url == "http://localhost:8000"
        assert tool.timeout == 10.0
        assert tool.max_retries == 3
        # Verify health check was called during init
        mock_httpx_client.get.assert_called_with("/healthz")

    def test_custom_initialization(self, mock_httpx_client):
        """Test initialization with custom parameters"""
        tool = BOMAPITool(
            base_url="http://api.example.com",
            timeout=30.0,
            max_retries=5
        )
        assert tool.base_url == "http://api.example.com"
        assert tool.timeout == 30.0
        assert tool.max_retries == 5

    def test_is_healthy_success(self, bom_tool, mock_httpx_client):
        """Test successful health check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_httpx_client.get.return_value = mock_response

        result = bom_tool.is_healthy()
        assert result is True

    def test_is_healthy_failure(self, bom_tool, mock_httpx_client):
        """Test failed health check"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_httpx_client.get.return_value = mock_response

        result = bom_tool.is_healthy()
        assert result is False

    def test_get_job_types_success(self, bom_tool, mock_httpx_client):
        """Test getting job types"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["cupcakes", "cake", "pastry_box"]
        mock_response.raise_for_status = Mock()
        mock_httpx_client.get.return_value = mock_response

        job_types = bom_tool.get_job_types()
        assert len(job_types) == 3
        assert "cupcakes" in job_types
        assert "cake" in job_types

    def test_get_job_types_error(self, bom_tool, mock_httpx_client):
        """Test job types with API error"""
        import httpx
        mock_httpx_client.get.side_effect = httpx.HTTPError("Connection failed")

        with pytest.raises(APIConnectionError):
            bom_tool.get_job_types()

    def test_estimate_success(self, bom_tool, mock_httpx_client):
        """Test successful estimate request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            'job_type': 'cupcakes',
            'quantity': 24,
            'materials': [
                {'name': 'flour', 'unit': 'kg', 'qty': 1.92},
                {'name': 'sugar', 'unit': 'kg', 'qty': 1.44},
            ],
            'labor_hours': 1.2
        }
        mock_httpx_client.post.return_value = mock_response

        result = bom_tool.estimate('cupcakes', 24)

        assert isinstance(result, EstimateResponse)
        assert result.job_type == 'cupcakes'
        assert result.quantity == 24
        assert len(result.materials) == 2
        assert result.labor_hours == 1.2

    def test_estimate_invalid_job_type(self, bom_tool, mock_httpx_client):
        """Test estimate with invalid job type"""
        import httpx
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'detail': 'Invalid job type'}
        mock_response.raise_for_status = Mock(side_effect=httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=mock_response
        ))
        mock_httpx_client.post.return_value = mock_response

        with pytest.raises(InvalidJobTypeError):
            bom_tool.estimate('invalid_job', 24)

    def test_estimate_invalid_quantity(self, bom_tool):
        """Test estimate with invalid quantity"""
        with pytest.raises(ValueError):
            bom_tool.estimate('cupcakes', 0)

        with pytest.raises(ValueError):
            bom_tool.estimate('cupcakes', -5)

    def test_estimate_api_error(self, bom_tool, mock_httpx_client):
        """Test estimate with API error"""
        import httpx
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status = Mock(side_effect=httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=mock_response
        ))
        mock_httpx_client.post.return_value = mock_response

        with pytest.raises(APIConnectionError):
            bom_tool.estimate('cupcakes', 24)

    def test_format_estimate(self, bom_tool, mock_httpx_client):
        """Test estimate formatting"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            'job_type': 'cupcakes',
            'quantity': 24,
            'materials': [
                {'name': 'flour', 'unit': 'kg', 'qty': 1.92},
            ],
            'labor_hours': 1.2
        }
        mock_httpx_client.post.return_value = mock_response

        result = bom_tool.estimate('cupcakes', 24)
        formatted = bom_tool.format_estimate(result)

        assert 'cupcakes' in formatted
        assert '24' in formatted
        assert 'flour' in formatted
        assert '1.2' in formatted

    def test_estimate_summary(self, bom_tool, mock_httpx_client):
        """Test estimate summary"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            'job_type': 'cupcakes',
            'quantity': 24,
            'materials': [
                {'name': 'flour', 'unit': 'kg', 'qty': 1.92},
                {'name': 'sugar', 'unit': 'kg', 'qty': 1.44},
            ],
            'labor_hours': 1.2
        }
        mock_httpx_client.post.return_value = mock_response

        result = bom_tool.estimate('cupcakes', 24)
        summary = bom_tool.estimate_summary(result)

        assert summary['job_type'] == 'cupcakes'
        assert summary['quantity'] == 24
        assert summary['material_count'] == 2
        assert summary['labor_hours'] == 1.2

    def test_estimate_multiple_success(self, bom_tool, mock_httpx_client):
        """Test batch estimation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            'job_type': 'cupcakes',
            'quantity': 24,
            'materials': [{'name': 'flour', 'unit': 'kg', 'qty': 1.92}],
            'labor_hours': 1.2
        }
        mock_httpx_client.post.return_value = mock_response

        requests = [
            ('cupcakes', 24),
            ('cake', 1),
        ]

        results = bom_tool.estimate_multiple(requests)
        assert len(results) == 2
        assert all(isinstance(r, EstimateResponse) for r in results)

    def test_validate_job_type(self, bom_tool, mock_httpx_client):
        """Test job type validation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = ["cupcakes", "cake", "pastry_box"]
        mock_httpx_client.get.return_value = mock_response

        assert bom_tool.validate_job_type('cupcakes') is True
        assert bom_tool.validate_job_type('cake') is True
        assert bom_tool.validate_job_type('pastry_box') is True
        assert bom_tool.validate_job_type('invalid') is False

    def test_pydantic_models(self):
        """Test Pydantic model validation"""
        # Test Material
        material = Material(name='flour', unit='kg', qty=1.92)
        assert material.name == 'flour'
        assert material.unit == 'kg'
        assert material.qty == 1.92

        # Test EstimateRequest
        request = EstimateRequest(job_type=JobType.CUPCAKES, quantity=24)
        assert request.job_type == JobType.CUPCAKES
        assert request.quantity == 24

        # Test EstimateResponse
        response = EstimateResponse(
            job_type=JobType.CUPCAKES,
            quantity=24,
            materials=[material],
            labor_hours=1.2
        )
        assert response.job_type == JobType.CUPCAKES
        assert len(response.materials) == 1

    def test_job_type_enum(self):
        """Test JobType enum"""
        assert JobType.CUPCAKES.value == "cupcakes"
        assert JobType.CAKE.value == "cake"
        assert JobType.PASTRY_BOX.value == "pastry_box"

        # Test enum creation from string
        assert JobType("cupcakes") == JobType.CUPCAKES

    def test_connection_error_handling(self, bom_tool, mock_httpx_client):
        """Test connection error handling"""
        mock_httpx_client.post.side_effect = httpx.ConnectError("Connection failed")

        with pytest.raises(APIConnectionError):
            bom_tool.estimate('cupcakes', 24)

    def test_context_manager(self, mock_httpx_client):
        """Test using tool as context manager"""
        with BOMAPITool(base_url="http://localhost:8000") as tool:
            assert tool is not None
            assert tool.base_url == "http://localhost:8000"
