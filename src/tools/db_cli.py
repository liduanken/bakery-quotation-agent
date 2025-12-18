"""CLI tool for material database management"""
import sys
from pathlib import Path

import click

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.tools.database_tool import DatabaseTool


@click.group()
@click.option('--db', default='resources/materials.sqlite', help='Database path')
@click.pass_context
def cli(ctx, db):
    """Material database management CLI"""
    try:
        ctx.obj = DatabaseTool(db)
    except Exception as e:
        click.echo(f"❌ Error initializing database: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_obj
def list(db: DatabaseTool):
    """List all materials"""
    materials = db.list_all_materials()

    click.echo(f"\n{'Name':<20} {'Unit':<8} {'Cost':<10} {'Currency':<8} {'Updated'}")
    click.echo("─" * 70)

    for m in materials:
        click.echo(f"{m.name:<20} {m.unit:<8} {m.unit_cost:<10.2f} {m.currency:<8} {m.last_updated}")

    click.echo(f"\nTotal: {len(materials)} materials")


@cli.command()
@click.argument('name')
@click.pass_obj
def get(db: DatabaseTool, name: str):
    """Get a specific material"""
    material = db.get_material_cost(name)
    if material:
        click.echo(f"\n✓ Material: {material.name}")
        click.echo(f"  Unit: {material.unit}")
        click.echo(f"  Cost: {material.unit_cost} {material.currency}")
        click.echo(f"  Last Updated: {material.last_updated}\n")
    else:
        click.echo(f"❌ Material '{name}' not found", err=True)

        # Suggest similar
        similar = db.search_materials(name[:3])
        if similar:
            click.echo(f"\nDid you mean: {', '.join([m.name for m in similar[:5]])}?")
        sys.exit(1)


@cli.command()
@click.argument('name')
@click.argument('unit')
@click.argument('cost', type=float)
@click.option('--currency', default='GBP', help='Currency code')
@click.pass_obj
def add(db: DatabaseTool, name: str, unit: str, cost: float, currency: str):
    """Add a new material"""
    success = db.add_material(name, unit, cost, currency)
    if success:
        click.echo(f"✅ Added: {name} ({cost} {currency}/{unit})")
    else:
        click.echo(f"❌ Material '{name}' already exists", err=True)
        sys.exit(1)


@cli.command()
@click.argument('name')
@click.argument('cost', type=float)
@click.pass_obj
def update(db: DatabaseTool, name: str, cost: float):
    """Update material cost"""
    success = db.update_material_cost(name, cost)
    if success:
        click.echo(f"✅ Updated: {name} = {cost}")
    else:
        click.echo(f"❌ Material '{name}' not found", err=True)
        sys.exit(1)


@cli.command()
@click.argument('name')
@click.confirmation_option(prompt='Are you sure you want to delete this material?')
@click.pass_obj
def delete(db: DatabaseTool, name: str):
    """Delete a material"""
    success = db.delete_material(name)
    if success:
        click.echo(f"✅ Deleted: {name}")
    else:
        click.echo(f"❌ Material '{name}' not found", err=True)
        sys.exit(1)


@cli.command()
@click.argument('pattern')
@click.pass_obj
def search(db: DatabaseTool, pattern: str):
    """Search materials by name pattern"""
    materials = db.search_materials(pattern)

    if materials:
        click.echo(f"\nFound {len(materials)} material(s) matching '{pattern}':\n")
        for m in materials:
            click.echo(f"  • {m.name:<20} {m.unit_cost} {m.currency}/{m.unit}")
    else:
        click.echo(f"No materials found matching '{pattern}'")


@cli.command()
@click.pass_obj
def info(db: DatabaseTool):
    """Show database information"""
    info = db.get_database_info()

    click.echo("\n📊 Database Information")
    click.echo("─" * 50)
    click.echo(f"  Path: {info['path']}")
    click.echo(f"  Total Materials: {info['total_materials']}")
    click.echo(f"  Units: {', '.join(info['units'])}")
    click.echo(f"  Currencies: {', '.join(info['currencies'])}")
    click.echo(f"  Last Updated: {info['last_updated']}\n")


@cli.command()
@click.pass_obj
def units(db: DatabaseTool):
    """List all available units"""
    units = db.get_available_units()
    click.echo(f"\nAvailable units: {', '.join(units)}\n")


if __name__ == '__main__':
    cli()
