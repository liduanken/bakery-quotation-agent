"""Quotation service - business logic for quote generation."""

import logging
from datetime import datetime, timedelta
from pathlib import Path

from src.app.config import settings
from src.app.data_models.common import QuoteRequest, QuoteResponse, StatusEnum

# Import existing tools
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.calculator import PricingCalculator
from src.converter import UnitConverter
from src.tools.bom_tool import BOMAPITool
from src.tools.database_tool import DatabaseTool
from src.tools.template_tool import QuoteDataBuilder, TemplateTool

logger = logging.getLogger(__name__)


class QuotationService:
    """Service for generating bakery quotations."""

    def __init__(self):
        """Initialize quotation service with all dependencies."""
        self.db_tool = DatabaseTool(settings.database_path)
        self.bom_tool = BOMAPITool(settings.bom_api_url)
        self.template_tool = TemplateTool(
            template_path=settings.template_path,
            output_dir=settings.output_dir
        )
        self.calculator = PricingCalculator(
            labor_rate=settings.labor_rate,
            markup_pct=settings.markup_pct / 100,
            vat_pct=settings.vat_pct / 100
        )
        self.converter = UnitConverter()

    async def generate_quote(self, request: QuoteRequest) -> QuoteResponse:
        """
        Generate a complete quotation.

        Args:
            request: Quote request with customer details

        Returns:
            QuoteResponse with generated quote information

        Raises:
            ValueError: If materials not found or BOM unavailable
        """
        logger.info(f"Generating quote for {request.quantity} × {request.job_type}")

        # 1. Get BOM estimate
        estimate = self.bom_tool.estimate(request.job_type, request.quantity)
        material_names = [m.name for m in estimate.materials]

        # 2. Query material costs
        costs = self.db_tool.get_materials_bulk(material_names)
        missing = set(material_names) - set(costs.keys())
        if missing:
            raise ValueError(f"Materials not found in database: {', '.join(missing)}")

        # 3. Calculate costs
        materials_list = []
        materials_total = 0.0

        for material in estimate.materials:
            cost_data = costs[material.name]
            qty_needed = material.qty
            
            # Convert units if needed
            if material.unit != cost_data['unit']:
                qty_needed = self.converter.convert(
                    material.qty,
                    material.unit,
                    cost_data['unit']
                )

            line_cost = qty_needed * cost_data['unit_cost']
            materials_total += line_cost

            materials_list.append({
                'name': material.name,
                'qty': qty_needed,
                'unit': cost_data['unit'],
                'unit_cost': cost_data['unit_cost'],
                'line_cost': line_cost
            })

        # 4. Calculate pricing
        calculations = self.calculator.calculate_quote(materials_list, estimate.labor_hours)

        # 5. Generate quote ID and dates
        quote_id = f"Q{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        quote_date = datetime.now().strftime("%Y-%m-%d")
        valid_until = (datetime.now() + timedelta(days=settings.quote_validity_days)).strftime("%Y-%m-%d")

        # 6. Build quote data
        builder = QuoteDataBuilder()
        data = (builder
                .set_header(quote_id, request.company_name, request.customer_name, quote_date, settings.quote_validity_days)
                .set_project(request.job_type, request.quantity, request.due_date)
                .set_materials(materials_list)
                .set_labor(calculations.labor_hours, calculations.labor_rate, calculations.labor_cost)
                .set_calculations(
                    materials_subtotal=calculations.materials_subtotal,
                    subtotal=calculations.subtotal,
                    markup_pct=settings.markup_pct,
                    markup_value=calculations.markup_value,
                    price_before_vat=calculations.price_before_vat,
                    vat_pct=settings.vat_pct,
                    vat_value=calculations.vat_value,
                    total=calculations.total,
                    currency=settings.default_currency
                )
                .set_notes(request.notes or "Thank you for your business!")
                .build())

        # 7. Render and save
        output_path = self.template_tool.render_and_save(data)

        logger.info(f"Quote generated: {output_path}")

        return QuoteResponse(
            status=StatusEnum.SUCCESS,
            quote_id=quote_id,
            file_path=str(output_path),
            total=calculations.total,
            currency=settings.default_currency
        )
