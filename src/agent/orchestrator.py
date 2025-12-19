"""Bakery Quotation Agent Orchestrator - LangChain Implementation"""
import logging
from typing import Any

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ..calculator import PricingCalculator
from ..config import Config
from ..converter import UnitConverter
from ..models import APIConnectionError, QuoteState
from ..tools.bom_tool import BOMAPITool

# Import tools (will be created next)
from ..tools.database_tool import DatabaseTool
from ..tools.template_tool import TemplateTool
from .prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class BakeryQuotationAgent:
    """Main agent orchestrator for bakery quotations"""

    def __init__(self, config: Config):
        """
        Initialize the Bakery Quotation Agent
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.config.validate()

        # Initialize LLM
        self.llm = self._initialize_llm()

        # Initialize tool instances
        self.db_tool = DatabaseTool(self.config.database_path)
        self.bom_tool = BOMAPITool(self.config.bom_api_url)
        self.template_tool = TemplateTool(
            self.config.template_path,
            self.config.output_dir
        )

        # Initialize tools for LangChain
        self.tools = self._initialize_tools()

        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )

        # Create agent
        self.agent = self._create_agent()

        # Create executor
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=self.config.agent_verbose,
            max_iterations=self.config.agent_max_iterations,
            handle_parsing_errors=True
        )

        # Quote state
        self.quote_state = QuoteState()
        self.quote_state.labor_rate = self.config.labor_rate
        self.quote_state.markup_pct = self.config.markup_pct
        self.quote_state.vat_pct = self.config.vat_pct
        self.quote_state.currency = self.config.currency
        self.quote_state.company_name = self.config.company_name

        logger.info("BakeryQuotationAgent initialized successfully")

    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize the language model"""
        if self.config.openai_api_key:
            logger.info(f"Initializing OpenAI model: {self.config.model_name}")
            return ChatOpenAI(
                model=self.config.model_name,
                temperature=self.config.model_temperature,
                openai_api_key=self.config.openai_api_key
            )
        elif self.config.anthropic_api_key:
            # For Anthropic support, would use:
            # from langchain_anthropic import ChatAnthropic
            # return ChatAnthropic(...)
            raise NotImplementedError("Anthropic support not yet implemented")
        else:
            raise ValueError("No API key provided")

    def _create_agent(self):
        """Create the LangChain agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT.format(
                markup_pct=self.config.markup_pct,
                vat_pct=self.config.vat_pct
            )),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        return create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

    def _initialize_tools(self) -> list[StructuredTool]:
        """Initialize all tools for the agent"""
        tools = [
            self._create_job_types_tool(),
            self._create_bom_estimate_tool(),
            self._create_material_costs_tool(),
            self._create_render_quote_tool(),
        ]

        logger.info(f"Initialized {len(tools)} tools")
        return tools

    # Tool 1: Get Job Types
    def _create_job_types_tool(self) -> StructuredTool:
        """Create tool to get available job types"""

        def get_job_types_impl() -> str:
            """Get list of available bakery job types"""
            try:
                types = self.bom_tool.get_job_types()
                logger.info(f"Retrieved job types: {types}")
                return f"Available job types: {', '.join(types)}"
            except Exception as e:
                logger.error(f"Error fetching job types: {e}")
                return f"Error fetching job types: {str(e)}"

        return StructuredTool.from_function(
            func=get_job_types_impl,
            name="get_job_types",
            description="Get the list of available bakery job types (cupcakes, cake, pastry_box)"
        )

    # Tool 2: Get BOM Estimate
    def _create_bom_estimate_tool(self) -> StructuredTool:
        """Create tool to get BOM estimate"""

        class GetBOMEstimateInput(BaseModel):
            job_type: str = Field(
                description="Type of bakery item (cupcakes, cake, or pastry_box)"
            )
            quantity: int = Field(
                description="Number of items to produce",
                gt=0
            )

        def get_bom_estimate_impl(job_type: str, quantity: int) -> str:
            """Get bill of materials and labor estimate"""
            # Fallback recipes if BOM API is unavailable
            FALLBACK_RECIPES = {
                "cupcakes": {
                    "materials": [
                        {"name": "flour", "qty": 0.5, "unit": "kg"},
                        {"name": "sugar", "qty": 0.3, "unit": "kg"},
                        {"name": "eggs", "qty": 6, "unit": "each"},
                        {"name": "butter", "qty": 0.2, "unit": "kg"},
                        {"name": "milk", "qty": 0.2, "unit": "L"}
                    ],
                    "labor_hours": 1.5
                },
                "cake": {
                    "materials": [
                        {"name": "flour", "qty": 1.0, "unit": "kg"},
                        {"name": "sugar", "qty": 0.8, "unit": "kg"},
                        {"name": "eggs", "qty": 8, "unit": "each"},
                        {"name": "butter", "qty": 0.5, "unit": "kg"},
                        {"name": "milk", "qty": 0.4, "unit": "L"}
                    ],
                    "labor_hours": 3.0
                },
                "pastry_box": {
                    "materials": [
                        {"name": "flour", "qty": 0.8, "unit": "kg"},
                        {"name": "sugar", "qty": 0.4, "unit": "kg"},
                        {"name": "butter", "qty": 0.4, "unit": "kg"},
                        {"name": "eggs", "qty": 4, "unit": "each"}
                    ],
                    "labor_hours": 2.0
                }
            }
            
            try:
                logger.info(f"Getting BOM estimate for {quantity} × {job_type}")
                estimate = self.bom_tool.estimate(job_type, quantity)

                # Store in state (convert to dict for compatibility)
                self.quote_state.bom_data = estimate.to_dict()
                self.quote_state.job_type = job_type
                self.quote_state.quantity = quantity

                # Format response (use attribute access on Pydantic model)
                materials_list = "\n".join([
                    f"  - {m.name}: {m.qty} {m.unit}"
                    for m in estimate.materials
                ])

                return f"""BOM Estimate for {quantity} × {job_type}:

Materials needed:
{materials_list}

Labor hours: {estimate.labor_hours} hours

Next step: Query material costs from database."""

            except APIConnectionError as e:
                logger.warning(f"BOM API not available: {e}")
                # Use fallback recipe data
                job_type_normalized = job_type.lower().replace(' ', '_')
                if job_type_normalized not in FALLBACK_RECIPES:
                    return f"❌ Unknown job type: {job_type}. Available types: cupcakes, cake, pastry_box"
                
                recipe = FALLBACK_RECIPES[job_type_normalized]
                # Scale materials by quantity
                scaled_materials = []
                for mat in recipe["materials"]:
                    scaled_materials.append({
                        "name": mat["name"],
                        "qty": mat["qty"] * quantity,
                        "unit": mat["unit"]
                    })
                
                scaled_labor = recipe["labor_hours"] * quantity
                
                # Store in state
                self.quote_state.bom_data = {
                    "job_type": job_type_normalized,
                    "quantity": quantity,
                    "materials": scaled_materials,
                    "labor_hours": scaled_labor
                }
                self.quote_state.job_type = job_type_normalized
                self.quote_state.quantity = quantity
                
                # Format response
                materials_list = "\n".join([
                    f"  - {m['name']}: {m['qty']} {m['unit']}"
                    for m in scaled_materials
                ])
                
                return f"""BOM Estimate for {quantity} × {job_type_normalized} (using standard recipe):

Materials needed:
{materials_list}

Labor hours: {scaled_labor} hours

Next step: Query material costs from database."""
                
            except Exception as e:
                logger.warning(f"Error getting BOM estimate: {e}")
                # Try fallback
                job_type_normalized = job_type.lower().replace(' ', '_')
                if job_type_normalized not in FALLBACK_RECIPES:
                    return f"❌ Cannot get BOM data for {job_type}. Please ensure job type is one of: cupcakes, cake, pastry_box"
                    
                recipe = FALLBACK_RECIPES[job_type_normalized]
                scaled_materials = []
                for mat in recipe["materials"]:
                    scaled_materials.append({
                        "name": mat["name"],
                        "qty": mat["qty"] * quantity,
                        "unit": mat["unit"]
                    })
                
                scaled_labor = recipe["labor_hours"] * quantity
                
                self.quote_state.bom_data = {
                    "job_type": job_type_normalized,
                    "quantity": quantity,
                    "materials": scaled_materials,
                    "labor_hours": scaled_labor
                }
                self.quote_state.job_type = job_type_normalized
                self.quote_state.quantity = quantity
                
                materials_list = "\n".join([
                    f"  - {m['name']}: {m['qty']} {m['unit']}"
                    for m in scaled_materials
                ])
                
                return f"""BOM Estimate for {quantity} × {job_type_normalized}:

Materials needed:
{materials_list}

Labor hours: {scaled_labor} hours

Next step: Query material costs from database."""

        return StructuredTool.from_function(
            func=get_bom_estimate_impl,
            name="get_bom_estimate",
            description="Get bill of materials (BOM) and labor hours for a bakery job. Requires job_type and quantity.",
            args_schema=GetBOMEstimateInput
        )

    # Tool 3: Query Material Costs
    def _create_material_costs_tool(self) -> StructuredTool:
        """Create tool to query material costs"""

        class QueryMaterialCostsInput(BaseModel):
            material_names: list[str] = Field(
                description="List of material names to look up in database"
            )

        def query_material_costs_impl(material_names: list[str]) -> str:
            """Query material unit costs from database"""
            try:
                logger.info(f"Querying costs for materials: {material_names}")
                costs = self.db_tool.get_materials_bulk(material_names)

                # Store in state
                self.quote_state.material_costs = costs

                # Check for missing materials
                found = set(costs.keys())
                requested = set(material_names)
                missing = requested - found

                if missing:
                    msg = f"⚠️  Missing materials in database: {', '.join(missing)}\n"
                    msg += f"Found: {len(found)}/{len(requested)} materials\n\n"
                    if found:
                        costs_list = "\n".join([
                            f"  - {name}: {data['unit_cost']} {data['currency']}/{data['unit']}"
                            for name, data in costs.items()
                        ])
                        msg += f"Available materials:\n{costs_list}"
                    return msg

                # Format response
                costs_list = "\n".join([
                    f"  - {name}: {data['unit_cost']} {data['currency']}/{data['unit']}"
                    for name, data in costs.items()
                ])

                return f"""Material costs retrieved:
{costs_list}

All materials found. Ready to calculate quote totals."""

            except Exception as e:
                logger.error(f"Error querying material costs: {e}")
                return f"Error querying material costs: {str(e)}"

        return StructuredTool.from_function(
            func=query_material_costs_impl,
            name="query_material_costs",
            description="Query unit costs for materials from the SQLite database. Takes a list of material names.",
            args_schema=QueryMaterialCostsInput
        )

    # Tool 4: Render Quote
    def _create_render_quote_tool(self) -> StructuredTool:
        """Create tool to render final quote"""

        class RenderQuoteInput(BaseModel):
            customer_name: str = Field(description="Customer name")
            due_date: str = Field(description="Delivery date in YYYY-MM-DD format")
            company_name: str = Field(
                default="The Artisan Bakery",
                description="Bakery company name"
            )
            notes: str = Field(default="", description="Special notes or instructions")

        def render_quote_impl(
            customer_name: str,
            due_date: str,
            company_name: str = "The Artisan Bakery",
            notes: str = ""
        ) -> str:
            """Calculate totals and render the quote document"""
            try:
                logger.info(f"Rendering quote for {customer_name}")

                # Update state
                self.quote_state.customer_name = customer_name
                self.quote_state.due_date = due_date
                self.quote_state.company_name = company_name
                self.quote_state.notes = notes

                # Validate we have required data
                if not self.quote_state.bom_data:
                    return "❌ Error: No BOM data available. Please call get_bom_estimate first."

                if not self.quote_state.material_costs:
                    return "❌ Error: No material costs available. Please call query_material_costs first."

                # Calculate totals
                calc = self._calculate_quote_totals()
                self.quote_state.calculations = calc

                # Prepare template data
                quote_data = self._prepare_template_data(calc)

                # Render template
                output_path = self.template_tool.render_and_save(quote_data)
                
                # Generate PDF
                pdf_path = self._generate_pdf(output_path)
                
                # Get filename and construct full URL
                pdf_filename = pdf_path.split('/')[-1]
                # Use backend server URL from config
                backend_url = self.config.backend_url

                # Format summary
                summary = f"""
✅ Quote Generated Successfully!

📄 [Download PDF]({backend_url}/api/v1/quotes/{pdf_filename})

Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{self.quote_state.quantity} × {self.quote_state.job_type}
Materials Subtotal:    {calc['materials_subtotal']:>8.2f} {self.quote_state.currency}
Labor ({calc['labor_hours']}h @ £{self.quote_state.labor_rate}/h): {calc['labor_cost']:>8.2f} {self.quote_state.currency}
Subtotal:              {calc['subtotal']:>8.2f} {self.quote_state.currency}
Markup ({self.quote_state.markup_pct}%):        {calc['markup_value']:>8.2f} {self.quote_state.currency}
Subtotal before VAT:   {calc['price_before_vat']:>8.2f} {self.quote_state.currency}
VAT ({self.quote_state.vat_pct}%):             {calc['vat_value']:>8.2f} {self.quote_state.currency}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL:                 {calc['total']:>8.2f} {self.quote_state.currency}

Unit Price: {calc['unit_price']:.2f} {self.quote_state.currency} per {self.quote_state.job_type}
Valid until: {quote_data['valid_until']}
"""
                logger.info(f"Quote generated successfully: {output_path}")
                return summary

            except Exception as e:
                logger.error(f"Error rendering quote: {e}", exc_info=True)
                return f"Error rendering quote: {str(e)}"

        return StructuredTool.from_function(
            func=render_quote_impl,
            name="render_quote",
            description="Calculate final pricing and render the quotation document. Requires customer_name and due_date.",
            args_schema=RenderQuoteInput
        )

    def _calculate_quote_totals(self) -> dict[str, Any]:
        """Calculate all quote totals with unit conversion"""
        converter = UnitConverter()
        calculator = PricingCalculator(
            labor_rate=self.quote_state.labor_rate,
            markup_pct=self.quote_state.markup_pct / 100,
            vat_pct=self.quote_state.vat_pct / 100
        )

        # Build material lines with costs
        lines = []
        for material in self.quote_state.bom_data['materials']:
            name = material['name']
            qty = material['qty']
            bom_unit = material['unit']

            # Get cost from database
            cost_data = self.quote_state.material_costs[name]
            db_unit = cost_data['unit']
            unit_cost = cost_data['unit_cost']

            # Convert units if needed
            if bom_unit != db_unit:
                qty_converted = converter.convert(qty, bom_unit, db_unit)
            else:
                qty_converted = qty

            line_cost = qty_converted * unit_cost

            lines.append({
                'name': name,
                'qty': qty,
                'unit': bom_unit,
                'unit_cost': unit_cost,
                'line_cost': line_cost
            })

        # Calculate using calculator
        labor_hours = self.quote_state.bom_data['labor_hours']
        calculations = calculator.calculate_quote(lines, labor_hours)

        # Convert to dict and add additional fields
        calc_dict = calculations.to_dict()
        calc_dict['unit_price'] = calculations.total / self.quote_state.quantity
        calc_dict['lines'] = lines  # Use original dicts with line_cost
        calc_dict['labor_hours'] = labor_hours

        return calc_dict

    def _prepare_template_data(self, calculations: dict[str, Any]) -> dict[str, Any]:
        """Prepare data for template rendering"""
        # Generate quote ID and dates
        quote_id = self.quote_state.generate_quote_id()
        quote_date = self.quote_state.get_quote_date()
        valid_until = self.quote_state.get_valid_until(self.config.quote_valid_days)

        # Format material lines for template
        lines = [
            {
                'name': line['name'],
                'qty': f"{line['qty']:.2f}",
                'unit': line['unit'],
                'unit_cost': f"{line['unit_cost']:.2f}",
                'line_cost': f"{line['line_cost']:.2f}"
            }
            for line in calculations['lines']
        ]

        return {
            'quote_id': quote_id,
            'quote_date': quote_date,
            'valid_until': valid_until,
            'company_name': self.quote_state.company_name,
            'customer_name': self.quote_state.customer_name,
            'job_type': self.quote_state.job_type,
            'quantity': self.quote_state.quantity,
            'due_date': self.quote_state.due_date,
            'lines': lines,
            'labor_hours': f"{calculations['labor_hours']:.1f}",
            'labor_rate': f"{self.quote_state.labor_rate:.2f}",
            'labor_cost': f"{calculations['labor_cost']:.2f}",
            'materials_subtotal': f"{calculations['materials_subtotal']:.2f}",
            'subtotal': f"{calculations['subtotal']:.2f}",
            'markup_pct': f"{self.quote_state.markup_pct:.0f}%",
            'markup_value': f"{calculations['markup_value']:.2f}",
            'price_before_vat': f"{calculations['price_before_vat']:.2f}",
            'vat_pct': f"{self.quote_state.vat_pct:.0f}%",
            'vat_value': f"{calculations['vat_value']:.2f}",
            'total': f"{calculations['total']:.2f}",
            'currency': self.quote_state.currency,
            'notes': self.quote_state.notes or "Thank you for your business!"
        }

    def invoke(self, user_input: str) -> dict[str, Any]:
        """Invoke the agent with user input"""
        try:
            response = self.executor.invoke({"input": user_input})
            return response
        except Exception as e:
            logger.error(f"Error invoking agent: {e}", exc_info=True)
            raise

    def _generate_pdf(self, markdown_path: str) -> str:
        """Generate PDF from markdown file using ReportLab"""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        from pathlib import Path
        import re
        
        # Read markdown
        md_path = Path(markdown_path)
        md_content = md_path.read_text()
        
        # Generate PDF path
        pdf_path = str(md_path).replace('.md', '.pdf')
        
        # Create PDF
        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
        )
        bold_style = ParagraphStyle(
            'Bold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
        )
        
        # Build content
        story = []
        lines = md_content.split('\n')
        
        table_data = []
        in_table = False
        
        def escape_html(text):
            """Escape special HTML characters"""
            return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        def convert_markdown_bold(text):
            """Convert markdown **bold** to HTML <b>bold</b>"""
            # Replace **text** with <b>text</b>
            parts = text.split('**')
            result = []
            for i, part in enumerate(parts):
                if i % 2 == 1:  # odd indices are bold
                    result.append(f'<b>{escape_html(part)}</b>')
                else:
                    result.append(escape_html(part))
            return ''.join(result)
        
        for line in lines:
            line = line.strip()
            if not line or line == '---':
                if in_table and table_data:
                    # Create table
                    t = Table(table_data)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),  # Right-align numbers
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 12))
                    table_data = []
                    in_table = False
                continue
                
            if line.startswith('# '):
                text = convert_markdown_bold(line[2:])
                story.append(Paragraph(text, title_style))
            elif line.startswith('## '):
                text = convert_markdown_bold(line[3:])
                story.append(Paragraph(text, heading_style))
            elif '|' in line and not line.startswith('|--') and not line.startswith('|:'):
                # Table row
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                # Remove markdown bold syntax from table cells
                cells = [cell.replace('**', '') for cell in cells]
                table_data.append(cells)
                in_table = True
            elif line.startswith('**') or '**' in line:
                # Bold text line
                text = convert_markdown_bold(line)
                story.append(Paragraph(text, styles['Normal']))
                story.append(Spacer(1, 6))
            elif line.startswith('*') and not line.startswith('**'):
                # Italic text
                text = escape_html(line)
                story.append(Paragraph(f'<i>{text[1:-1]}</i>', styles['Normal']))
                story.append(Spacer(1, 6))
            elif line.startswith('- '):
                # List item
                text = convert_markdown_bold(line[2:])
                story.append(Paragraph(f'• {text}', styles['Normal']))
                story.append(Spacer(1, 6))
            else:
                text = convert_markdown_bold(line)
                story.append(Paragraph(text, styles['Normal']))
                story.append(Spacer(1, 6))
        
        # Handle remaining table
        if in_table and table_data:
            t = Table(table_data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(t)
        
        # Build PDF
        doc.build(story)
        logger.info(f"PDF generated: {pdf_path}")
        
        # Upload to GCS if enabled
        logger.info(f"GCS config: enabled={self.config.gcs_enabled}, bucket={self.config.gcs_bucket_name}")
        if self.config.gcs_enabled and self.config.gcs_bucket_name:
            try:
                self._upload_to_gcs(pdf_path)
            except Exception as e:
                logger.error(f"Failed to upload PDF to GCS: {e}", exc_info=True)
        
        return pdf_path
    
    def _upload_to_gcs(self, file_path: str) -> None:
        """Upload file to Google Cloud Storage"""
        from google.cloud import storage
        from pathlib import Path
        
        filename = Path(file_path).name
        bucket_name = self.config.gcs_bucket_name
        
        logger.info(f"Uploading {filename} to gs://{bucket_name}/quotes/")
        
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(f"quotes/{filename}")
        
        blob.upload_from_filename(file_path)
        blob.content_type = "application/pdf"
        
        logger.info(f"Successfully uploaded {filename} to GCS")

    def reset(self) -> None:
        """Reset the agent state for a new quote"""
        self.quote_state.reset()
        self.memory.clear()
        logger.info("Agent state reset")
