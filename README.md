# Bakery Quotation Agent

AI-powered quotation system using LangChain and GPT-4/Claude for intelligent bakery order quoting.

## Overview

An intelligent agent that generates professional bakery quotations through natural conversation. Built with **LangChain**, it orchestrates three tools to:
- Query material costs from SQLite database
- Fetch bill of materials from pricing API
- Generate formatted quote documents

## Features

- 🤖 Natural language conversation with LLM
- 🔧 Three integrated tools (BOM API, Database, Template Renderer)
- 💰 Automatic cost calculation with markup and VAT
- 📄 Professional Markdown quote generation
- 🔄 Context-aware conversation memory
- ✨ Rich CLI interface

## Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- Docker & Docker Compose (for BOM API)
- OpenAI API key (or Anthropic API key)

### Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
# or: brew install uv

# Clone and navigate to project
cd bakery-quotation-agent

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# For development (includes pytest, black, ruff, mypy)
uv pip install -e ".[dev]"

# For Anthropic Claude support
uv pip install -e ".[anthropic]"
```

### Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API key
# OPENAI_API_KEY=sk-proj-...
```

### Start BOM API

```bash
# In a new terminal
cd resources/bakery_pricing_tool
docker compose up --build
```

### Run Agent

```bash
# Using the installed script
bakery-agent

# Or directly with Python
python -m src.main
```

### Database Management

```bash
# List all materials
bakery-db list

# Get specific material
bakery-db get flour

# Add new material
bakery-db add chocolate kg 8.50 --currency GBP

# Update material cost
bakery-db update flour 0.95

# Delete material
bakery-db delete "old-material"

# Search materials
bakery-db search "sugar"

# Show database info
bakery-db info
```

## Usage Example

```
Agent: Hello! I'll help you create a bakery quotation.

You: I need 24 cupcakes

Agent: [Gets BOM estimate] Great! For 24 cupcakes, we'll need flour, sugar, 
       butter, eggs, milk, vanilla, and baking powder. About 1.2 hours of labor.
       May I have the customer's name?

You: Jane Doe

Agent: Thank you! When would you like these delivered? (YYYY-MM-DD format)

You: 2025-12-20

Agent: Perfect! Here's the summary:
       - 24 cupcakes for Jane Doe
       - Materials: £10.23
       - Labor: £18.00
       - Total with markup and VAT: £44.04
       
       Shall I generate the quote?

You: yes

Agent: ✅ Quote Generated Successfully!
       📄 File: out/quote_Q20251218_143022.md
```

## Configuration

### Business Settings (.env)

```bash
LABOR_RATE=15.00          # GBP per hour
MARKUP_PCT=30             # Percentage
VAT_PCT=20                # Percentage
DEFAULT_CURRENCY=GBP
```

### LLM Provider

**OpenAI (Default):**
```bash
OPENAI_API_KEY=sk-proj-your-key
MODEL_NAME=gpt-4-turbo-preview
```

**Anthropic (Alternative):**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key
MODEL_NAME=claude-3-opus-20240229
```

## Project Structure

```
├── src/
│   ├── agent/
│   │   ├── orchestrator.py     # Main agent logic
│   │   └── prompts.py          # System prompts
│   ├── tools/
│   │   ├── database_tool.py    # SQLite interface
│   │   ├── bom_tool.py         # BOM API client
│   │   └── template_tool.py    # Template renderer
│   ├── calculator.py           # Pricing calculations
│   ├── converter.py            # Unit conversions
│   ├── config.py               # Configuration
│   ├── models.py               # Data models
│   └── main.py                 # Entry point
├── resources/
│   ├── materials.sqlite        # Material costs DB
│   ├── quote_template.md       # Quote template
│   └── bakery_pricing_tool/    # BOM API (Docker)
├── out/                        # Generated quotes
├── requirements.txt            # Legacy pip format
└── pyproject.toml              # Modern Python project config
```

## Architecture

- **Framework:** LangChain with OpenAI/Anthropic
- **Agent:** Function-calling agent with conversation memory
- **Tools:** Four custom tools for data access
- **Storage:** SQLite for materials, filesystem for quotes
- **Package Manager:** uv for fast dependency management

## Commands

### Agent Commands
- `bakery-agent` - Start the agent (or `python -m src.main`)
- Type `exit`, `quit`, or `q` to exit
- Type `reset`, `restart`, or `new` to start a new quote

### Database Commands
- `bakery-db list` - List all materials
- `bakery-db get <name>` - Get material details
- `bakery-db add <name> <unit> <cost>` - Add new material
- `bakery-db update <name> <cost>` - Update material cost
- `bakery-db search <pattern>` - Search materials
- `bakery-db info` - Show database statistics

## Troubleshooting

### "Cannot connect to BOM API"

Ensure Docker container is running:
```bash
docker ps  # Should show bakery_pricing_tool
cd resources/bakery_pricing_tool
docker compose up --build
```

### "Invalid API key"

Check `.env` file:
- OpenAI keys start with `sk-proj-`
- Anthropic keys start with `sk-ant-`

### Missing materials

Add using the CLI tool:
```bash
bakery-db add "new-ingredient" kg 5.50 --currency GBP
```

Or manually with SQLite:
```bash
sqlite3 resources/materials.sqlite
INSERT INTO materials (name, unit, unit_cost, currency, last_updated)
VALUES ('new_ingredient', 'kg', 5.50, 'GBP', date('now'));
```

## Development

### Environment Setup

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/
```

### Dependency Management

```bash
# Add new dependency
uv add package-name

# Add dev dependency  
uv add --dev package-name

# Update dependencies
uv lock

# Sync environment
uv pip sync
```

### Adding New Materials

```sql
sqlite3 resources/materials.sqlite
INSERT INTO materials VALUES (
    NULL, 'chocolate_chips', 'kg', 5.50, 'GBP', '2025-12-18'
);
```

### Adding New Job Types

Edit `resources/bakery_pricing_tool/app.py`:
```python
JOBS = {
    # ... existing jobs
    "cookies": {
        "materials": [...],
        "labor_hours_per_unit": 0.02
    }
}
```
Restart Docker container.

## License

MIT

## Next Steps

See `documentation/Implementation_Plan.md` for detailed implementation guide and architecture decisions.
