"""Sample test data factory"""
from typing import Dict, Any, List


class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_bom_estimate(
        job_type: str = 'cupcakes',
        quantity: int = 24
    ) -> Dict[str, Any]:
        """Create BOM estimate data"""
        materials_per_unit = {
            'cupcakes': [
                {'name': 'flour', 'unit': 'kg', 'qty_per_unit': 0.08},
                {'name': 'sugar', 'unit': 'kg', 'qty_per_unit': 0.06},
                {'name': 'butter', 'unit': 'kg', 'qty_per_unit': 0.04},
                {'name': 'eggs', 'unit': 'each', 'qty_per_unit': 0.5},
                {'name': 'milk', 'unit': 'L', 'qty_per_unit': 0.05},
                {'name': 'vanilla', 'unit': 'ml', 'qty_per_unit': 1.0},
                {'name': 'baking_powder', 'unit': 'kg', 'qty_per_unit': 0.001},
            ],
            'cake': [
                {'name': 'flour', 'unit': 'kg', 'qty_per_unit': 0.50},
                {'name': 'sugar', 'unit': 'kg', 'qty_per_unit': 0.40},
                {'name': 'butter', 'unit': 'kg', 'qty_per_unit': 0.30},
                {'name': 'eggs', 'unit': 'each', 'qty_per_unit': 4.0},
                {'name': 'milk', 'unit': 'L', 'qty_per_unit': 0.25},
            ],
            'pastry_box': [
                {'name': 'flour', 'unit': 'kg', 'qty_per_unit': 0.60},
                {'name': 'butter', 'unit': 'kg', 'qty_per_unit': 0.40},
                {'name': 'sugar', 'unit': 'kg', 'qty_per_unit': 0.20},
            ],
        }
        
        labor_per_unit = {
            'cupcakes': 0.05,
            'cake': 0.80,
            'pastry_box': 0.60
        }
        
        materials = [
            {
                'name': m['name'],
                'unit': m['unit'],
                'qty': m['qty_per_unit'] * quantity
            }
            for m in materials_per_unit.get(job_type, [])
        ]
        
        return {
            'job_type': job_type,
            'quantity': quantity,
            'materials': materials,
            'labor_hours': labor_per_unit.get(job_type, 0) * quantity
        }
    
    @staticmethod
    def create_material_costs() -> List[Dict[str, Any]]:
        """Create sample material cost data"""
        return [
            {'name': 'flour', 'unit': 'kg', 'unit_cost': 0.90, 'currency': 'GBP'},
            {'name': 'sugar', 'unit': 'kg', 'unit_cost': 0.70, 'currency': 'GBP'},
            {'name': 'butter', 'unit': 'kg', 'unit_cost': 4.50, 'currency': 'GBP'},
            {'name': 'eggs', 'unit': 'each', 'unit_cost': 0.18, 'currency': 'GBP'},
            {'name': 'milk', 'unit': 'L', 'unit_cost': 0.60, 'currency': 'GBP'},
            {'name': 'cocoa', 'unit': 'kg', 'unit_cost': 6.00, 'currency': 'GBP'},
            {'name': 'vanilla', 'unit': 'ml', 'unit_cost': 0.05, 'currency': 'GBP'},
            {'name': 'baking_powder', 'unit': 'kg', 'unit_cost': 3.00, 'currency': 'GBP'},
            {'name': 'salt', 'unit': 'kg', 'unit_cost': 0.40, 'currency': 'GBP'},
            {'name': 'yeast', 'unit': 'kg', 'unit_cost': 2.50, 'currency': 'GBP'},
        ]
    
    @staticmethod
    def create_quote_data(
        quote_id: str = 'TEST001',
        job_type: str = 'cupcakes',
        quantity: int = 24
    ) -> Dict[str, Any]:
        """Create complete quote data"""
        return {
            'quote_id': quote_id,
            'quote_date': '2025-12-18',
            'valid_until': '2026-01-17',
            'company_name': 'Test Bakery',
            'customer_name': 'Test Customer',
            'job_type': job_type,
            'quantity': quantity,
            'due_date': '2025-12-25',
            'lines': [
                {'name': 'flour', 'qty': 1.92, 'unit': 'kg', 'unit_cost': 0.90, 'line_cost': 1.73},
                {'name': 'sugar', 'qty': 1.44, 'unit': 'kg', 'unit_cost': 0.70, 'line_cost': 1.01},
            ],
            'labor_hours': 1.2,
            'labor_rate': 15.0,
            'labor_cost': 18.0,
            'materials_subtotal': 2.74,
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
    
    @staticmethod
    def create_template_content() -> str:
        """Create sample template content"""
        return """# {{company_name}} — Quotation

**Quote ID:** {{quote_id}}  
**Date:** {{quote_date}}  
**Valid Until:** {{valid_until}}  
**Customer:** {{customer_name}}  
**Project:** {{quantity}} × {{job_type}}  
**Due Date:** {{due_date}}

---

## Bill of Materials

| Item | Qty | Unit | Unit Cost ({{currency}}) | Line Cost ({{currency}}) |
|------|----:|:----:|-------------------------:|-------------------------:|
{{#lines}}
| {{name}} | {{qty}} | {{unit}} | {{unit_cost}} | {{line_cost}} |
{{/lines}}

**Materials Subtotal:** {{currency}}{{materials_subtotal}}

---

## Labor & Costs

- **Labor Hours:** {{labor_hours}}h @ {{currency}}{{labor_rate}}/h = {{currency}}{{labor_cost}}
- **Subtotal:** {{currency}}{{subtotal}}
- **Markup ({{markup_pct}}%):** {{currency}}{{markup_value}}
- **Price before VAT:** {{currency}}{{price_before_vat}}
- **VAT ({{vat_pct}}%):** {{currency}}{{vat_value}}

---

## **TOTAL: {{currency}}{{total}}**

{{#notes}}
### Notes
{{notes}}
{{/notes}}

---
*Generated by Bakery Quotation System*
"""
