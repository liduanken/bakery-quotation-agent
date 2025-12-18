#!/usr/bin/env python3
"""Verification script to check project setup"""
import sys
from pathlib import Path

def check_file_exists(path: str, description: str) -> bool:
    """Check if a file exists"""
    if Path(path).exists():
        print(f"✓ {description}: {path}")
        return True
    else:
        print(f"✗ {description}: {path} (MISSING)")
        return False

def main():
    """Run verification checks"""
    print("=" * 60)
    print("Bakery Quotation Agent - Setup Verification")
    print("=" * 60)
    print()
    
    # Check for uv (optional but recommended)
    print("Package Manager:")
    try:
        import subprocess
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ uv detected: {result.stdout.strip()}")
        else:
            print("⚠ uv not found (optional but recommended)")
            print("  Install: curl -LsSf https://astral.sh/uv/install.sh | sh")
    except FileNotFoundError:
        print("⚠ uv not found (optional but recommended)")
        print("  Install: curl -LsSf https://astral.sh/uv/install.sh | sh")
    print()
    
    # Check configuration files
    print("Configuration Files:")
    has_pyproject = check_file_exists("pyproject.toml", "Project config (pyproject.toml)")
    has_requirements = check_file_exists("requirements.txt", "Legacy requirements")
    has_env_example = check_file_exists(".env.example", "Environment template")
    print()
    
    checks = []
    
    # Core source files
    print("Core Source Files:")
    checks.append(check_file_exists("src/__init__.py", "Package init"))
    checks.append(check_file_exists("src/config.py", "Configuration"))
    checks.append(check_file_exists("src/models.py", "Data models"))
    checks.append(check_file_exists("src/calculator.py", "Pricing calculator"))
    checks.append(check_file_exists("src/converter.py", "Unit converter"))
    checks.append(check_file_exists("src/main.py", "Main entry point"))
    print()
    
    # Agent files
    print("Agent Components:")
    checks.append(check_file_exists("src/agent/__init__.py", "Agent package"))
    checks.append(check_file_exists("src/agent/orchestrator.py", "Agent orchestrator"))
    checks.append(check_file_exists("src/agent/prompts.py", "System prompts"))
    print()
    
    # Tools
    print("Tools:")
    checks.append(check_file_exists("src/tools/__init__.py", "Tools package"))
    checks.append(check_file_exists("src/tools/database_tool.py", "Database tool"))
    checks.append(check_file_exists("src/tools/bom_tool.py", "BOM API tool"))
    checks.append(check_file_exists("src/tools/template_tool.py", "Template tool"))
    print()
    
    # Resources
    print("Resources:")
    checks.append(check_file_exists("resources/materials.sqlite", "Materials database"))
    checks.append(check_file_exists("resources/quote_template.md", "Quote template"))
    checks.append(check_file_exists("resources/bakery_pricing_tool/app.py", "BOM API"))
    checks.append(check_file_exists("resources/bakery_pricing_tool/docker-compose.yml", "Docker compose"))
    print()
    
    # Configuration
    print("Configuration:")
    checks.append(check_file_exists(".env.example", "Example environment"))
    checks.append(check_file_exists("requirements.txt", "Dependencies"))
    checks.append(check_file_exists("README.md", "README"))
    checks.append(check_file_exists(".gitignore", "Git ignore"))
    print()
    
    # Documentation
    print("Documentation:")
    checks.append(check_file_exists("documentation/Implementation_Plan.md", "Implementation plan"))
    checks.append(check_file_exists("documentation/01_Agent_Orchestrator.md", "Agent docs"))
    checks.append(check_file_exists("documentation/02_Database_Tool.md", "Database docs"))
    checks.append(check_file_exists("documentation/03_BOM_API_Tool.md", "BOM API docs"))
    print()
    
    # Summary
    print("=" * 60)
    total = len(checks)
    passed = sum(checks)
    print(f"Verification: {passed}/{total} checks passed")
    
    if passed == total:
        print("✓ All checks passed! Project setup is complete.")
        print()
        print("Next steps:")
        print("1. Copy .env.example to .env and add your OpenAI API key")
        print("2. Start BOM API: cd resources/bakery_pricing_tool && docker compose up")
        print("3. Install dependencies: pip install -r requirements.txt")
        print("4. Run agent: python src/main.py")
        return 0
    else:
        print(f"✗ {total - passed} checks failed. Please review the setup.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
