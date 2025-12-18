"""Template rendering tool - Quotation template renderer

Full implementation based on documentation/04_Template_Renderer_Tool.md
Handles template loading, variable substitution, and file output.
"""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import chevron

logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================

class TemplateRenderError(Exception):
    """Error rendering template"""
    pass


# ============================================================================
# Template Tool
# ============================================================================

class TemplateTool:
    """Quotation template renderer using Mustache/Chevron"""

    def __init__(
        self,
        template_path: str = "resources/quote_template.md",
        output_dir: str = "out"
    ):
        """
        Initialize template renderer.
        
        Args:
            template_path: Path to Mustache template file
            output_dir: Directory for output files
        """
        self.template_path = Path(template_path)
        self.output_dir = Path(output_dir)

        # Verify template exists
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load template
        self.template = self._load_template()
        logger.info(f"Template loaded: {self.template_path}")

    def _load_template(self) -> str:
        """Load template content"""
        try:
            with open(self.template_path, encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise TemplateRenderError(f"Cannot load template: {e}") from e

    # ========================================================================
    # Rendering Methods
    # ========================================================================

    def render(self, data: dict[str, Any]) -> str:
        """
        Render template with data.
        
        Args:
            data: Dictionary with template variables
            
        Returns:
            Rendered markdown string
            
        Raises:
            TemplateRenderError: If rendering fails
        """
        try:
            # Validate data
            self._validate_data(data)

            # Format data for template
            formatted_data = self._format_data(data)

            # Render with chevron
            rendered = chevron.render(self.template, formatted_data)

            logger.info("Template rendered successfully")
            return rendered

        except Exception as e:
            raise TemplateRenderError(f"Rendering failed: {e}") from e

    def _validate_data(self, data: dict[str, Any]):
        """Validate required fields are present"""
        required_fields = [
            'company_name', 'quote_id', 'quote_date', 'customer_name',
            'job_type', 'quantity', 'due_date', 'lines', 'currency', 'total'
        ]

        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

    def _format_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Format data for template rendering.
        
        Handles number formatting, percentage display, etc.
        """
        formatted = data.copy()

        # Format currency values to 2 decimal places
        currency_fields = [
            'unit_cost', 'line_cost', 'materials_subtotal', 'labor_cost',
            'subtotal', 'markup_value', 'price_before_vat', 'vat_value', 'total'
        ]

        for field in currency_fields:
            if field in formatted and isinstance(formatted[field], (int, float)):
                formatted[field] = f"{formatted[field]:.2f}"

        # Format lines
        if 'lines' in formatted:
            formatted['lines'] = [
                {
                    'name': line['name'],
                    'qty': f"{line['qty']:.2f}" if isinstance(line['qty'], (int, float)) else line['qty'],
                    'unit': line['unit'],
                    'unit_cost': f"{line['unit_cost']:.2f}" if isinstance(line['unit_cost'], (int, float)) else line['unit_cost'],
                    'line_cost': f"{line['line_cost']:.2f}" if isinstance(line['line_cost'], (int, float)) else line['line_cost']
                }
                for line in formatted['lines']
            ]

        # Format labor hours
        if 'labor_hours' in formatted and isinstance(formatted['labor_hours'], (int, float)):
            formatted['labor_hours'] = f"{formatted['labor_hours']:.2f}"

        # Format percentages
        if 'markup_pct' in formatted and isinstance(formatted['markup_pct'], (int, float)):
            formatted['markup_pct'] = f"{formatted['markup_pct']:.0f}%"

        if 'vat_pct' in formatted and isinstance(formatted['vat_pct'], (int, float)):
            formatted['vat_pct'] = f"{formatted['vat_pct']:.0f}%"

        return formatted

    # ========================================================================
    # File Operations
    # ========================================================================

    def save(self, content: str, quote_id: str) -> Path:
        """
        Save rendered content to file.
        
        Args:
            content: Rendered markdown
            quote_id: Quote identifier for filename
            
        Returns:
            Path to saved file
        """
        filename = f"quote_{quote_id}.md"
        output_path = self.output_dir / filename

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Quote saved: {output_path}")
            return output_path

        except Exception as e:
            raise TemplateRenderError(f"Cannot save file: {e}") from e

    def render_and_save(self, data: dict[str, Any]) -> Path:
        """
        Render template and save to file in one step.
        
        Args:
            data: Template data (must include 'quote_id')
            
        Returns:
            Path to saved file
        """
        if 'quote_id' not in data:
            raise ValueError("Data must include 'quote_id'")

        rendered = self.render(data)
        output_path = self.save(rendered, data['quote_id'])

        return output_path

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def validate_template(self) -> list[str]:
        """
        Validate template has all required placeholders.
        
        Returns:
            List of missing placeholders
        """
        required_placeholders = [
            'company_name', 'quote_id', 'customer_name',
            'job_type', 'quantity', 'total', 'currency'
        ]

        missing = []
        for placeholder in required_placeholders:
            if f"{{{{{placeholder}}}}}" not in self.template:
                missing.append(placeholder)

        return missing


# ============================================================================
# Data Builder Helper
# ============================================================================

class QuoteDataBuilder:
    """Helper to build template data dictionary"""

    def __init__(self):
        self.data = {}

    def set_header(
        self,
        quote_id: str,
        company_name: str,
        customer_name: str,
        quote_date: str | None = None,
        valid_days: int = 30
    ) -> 'QuoteDataBuilder':
        """Set header information"""
        if quote_date is None:
            quote_date = datetime.now().strftime("%Y-%m-%d")

        valid_until = (
            datetime.now() + timedelta(days=valid_days)
        ).strftime("%Y-%m-%d")

        self.data.update({
            'quote_id': quote_id,
            'company_name': company_name,
            'customer_name': customer_name,
            'quote_date': quote_date,
            'valid_until': valid_until
        })
        return self

    def set_project(
        self,
        job_type: str,
        quantity: int,
        due_date: str
    ) -> 'QuoteDataBuilder':
        """Set project information"""
        self.data.update({
            'job_type': job_type,
            'quantity': quantity,
            'due_date': due_date
        })
        return self

    def set_materials(
        self,
        lines: list[dict[str, Any]]
    ) -> 'QuoteDataBuilder':
        """Set material lines"""
        self.data['lines'] = lines
        return self

    def set_labor(
        self,
        labor_hours: float,
        labor_rate: float,
        labor_cost: float
    ) -> 'QuoteDataBuilder':
        """Set labor information"""
        self.data.update({
            'labor_hours': labor_hours,
            'labor_rate': labor_rate,
            'labor_cost': labor_cost
        })
        return self

    def set_calculations(
        self,
        materials_subtotal: float,
        subtotal: float,
        markup_pct: float,
        markup_value: float,
        price_before_vat: float,
        vat_pct: float,
        vat_value: float,
        total: float,
        currency: str = "GBP"
    ) -> 'QuoteDataBuilder':
        """Set all calculations"""
        self.data.update({
            'materials_subtotal': materials_subtotal,
            'subtotal': subtotal,
            'markup_pct': markup_pct,
            'markup_value': markup_value,
            'price_before_vat': price_before_vat,
            'vat_pct': vat_pct,
            'vat_value': vat_value,
            'total': total,
            'currency': currency
        })
        return self

    def set_notes(self, notes: str = "") -> 'QuoteDataBuilder':
        """Set notes/comments"""
        self.data['notes'] = notes
        return self

    def build(self) -> dict[str, Any]:
        """Build final data dictionary"""
        required = [
            'quote_id', 'company_name', 'customer_name',
            'job_type', 'quantity', 'total', 'currency'
        ]

        missing = [f for f in required if f not in self.data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        return self.data
