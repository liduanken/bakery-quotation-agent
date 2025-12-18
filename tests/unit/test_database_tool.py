"""Tests for database tool"""
import pytest

from src.tools.database_tool import (
    DatabaseTool,
    MaterialCost,
    MaterialNotFoundError,
)


def test_initialization(temp_database):
    """Test database tool initialization"""
    db = DatabaseTool(temp_database)
    assert db.database_path == temp_database


def test_get_material_cost(temp_database):
    """Test getting a single material cost"""
    db = DatabaseTool(temp_database)

    flour = db.get_material_cost('flour')
    assert flour is not None
    assert isinstance(flour, MaterialCost)
    assert flour.name == 'flour'
    assert flour.unit == 'kg'
    assert flour.unit_cost == 0.90
    assert flour.currency == 'GBP'


def test_get_material_not_found(temp_database):
    """Test querying non-existent material"""
    db = DatabaseTool(temp_database)
    result = db.get_material_cost('chocolate')
    assert result is None


def test_get_material_cost_strict(temp_database):
    """Test strict material retrieval"""
    db = DatabaseTool(temp_database)

    # Should succeed
    flour = db.get_material_cost_strict('flour')
    assert flour.name == 'flour'

    # Should raise exception
    with pytest.raises(MaterialNotFoundError) as exc_info:
        db.get_material_cost_strict('chocolate')
    assert 'chocolate' in str(exc_info.value)


def test_get_materials_bulk(temp_database):
    """Test bulk material retrieval"""
    db = DatabaseTool(temp_database)

    materials = db.get_materials_bulk(['flour', 'sugar', 'eggs'])
    assert len(materials) == 3
    assert 'flour' in materials
    assert 'sugar' in materials
    assert 'eggs' in materials

    # Check structure (returns dict for compatibility)
    assert materials['flour']['unit'] == 'kg'
    assert materials['flour']['unit_cost'] == 0.90


def test_get_materials_bulk_with_missing(temp_database):
    """Test bulk retrieval with missing materials"""
    db = DatabaseTool(temp_database)

    materials = db.get_materials_bulk(['flour', 'chocolate', 'sugar'])
    assert len(materials) == 2
    assert 'flour' in materials
    assert 'sugar' in materials
    assert 'chocolate' not in materials


def test_get_materials_bulk_empty(temp_database):
    """Test bulk retrieval with empty list"""
    db = DatabaseTool(temp_database)
    materials = db.get_materials_bulk([])
    assert materials == {}


def test_list_all_materials(temp_database):
    """Test listing all materials"""
    db = DatabaseTool(temp_database)
    materials = db.list_all_materials()

    assert len(materials) == 9
    assert all(isinstance(m, MaterialCost) for m in materials)

    # Check ordering (should be alphabetical)
    names = [m.name for m in materials]
    assert names == sorted(names)


def test_search_materials(temp_database):
    """Test material search"""
    db = DatabaseTool(temp_database)

    # Search for materials containing 'u'
    results = db.search_materials('u')
    assert len(results) >= 2  # flour, sugar, butter

    # Search for exact match
    results = db.search_materials('flour')
    assert len(results) == 1
    assert results[0].name == 'flour'

    # Search for non-existent
    results = db.search_materials('xyz')
    assert len(results) == 0


def test_material_exists(temp_database):
    """Test material existence check"""
    db = DatabaseTool(temp_database)

    assert db.material_exists('flour') is True
    assert db.material_exists('chocolate') is False


def test_get_available_units(temp_database):
    """Test getting available units"""
    db = DatabaseTool(temp_database)
    units = db.get_available_units()

    assert 'kg' in units
    assert 'each' in units
    assert 'L' in units
    assert 'ml' in units
    assert len(units) == 4


def test_get_material_count(temp_database):
    """Test material count"""
    db = DatabaseTool(temp_database)
    count = db.get_material_count()
    assert count == 9


def test_get_database_info(temp_database):
    """Test database info retrieval"""
    db = DatabaseTool(temp_database)
    info = db.get_database_info()

    assert info['total_materials'] == 9
    assert 'kg' in info['units']
    assert 'GBP' in info['currencies']
    assert info['last_updated'] == '2025-09-01'
    assert info['path'] == temp_database


def test_add_material(temp_database):
    """Test adding a new material"""
    db = DatabaseTool(temp_database)

    # Add new material (yeast doesn't exist yet)
    success = db.add_material('yeast', 'kg', 2.50, 'GBP')
    assert success is True

    # Verify it was added
    yeast = db.get_material_cost('yeast')
    assert yeast is not None
    assert yeast.unit_cost == 2.50

    # Try to add duplicate
    success = db.add_material('cocoa', 'kg', 7.00, 'GBP')
    assert success is False


def test_update_material_cost(temp_database):
    """Test updating material cost"""
    db = DatabaseTool(temp_database)

    # Update existing
    success = db.update_material_cost('flour', 0.95)
    assert success is True

    # Verify update
    flour = db.get_material_cost('flour')
    assert flour.unit_cost == 0.95

    # Update non-existent
    success = db.update_material_cost('chocolate', 10.00)
    assert success is False


def test_delete_material(temp_database):
    """Test deleting a material"""
    db = DatabaseTool(temp_database)

    # Delete existing
    success = db.delete_material('flour')
    assert success is True

    # Verify deletion
    flour = db.get_material_cost('flour')
    assert flour is None

    # Delete non-existent
    success = db.delete_material('chocolate')
    assert success is False


def test_material_cost_to_dict(temp_database):
    """Test MaterialCost to_dict conversion"""
    db = DatabaseTool(temp_database)
    flour = db.get_material_cost('flour')

    flour_dict = flour.to_dict()
    assert isinstance(flour_dict, dict)
    assert flour_dict['name'] == 'flour'
    assert flour_dict['unit'] == 'kg'
    assert flour_dict['unit_cost'] == 0.90


def test_case_insensitive_search(temp_database):
    """Test case-insensitive material search"""
    db = DatabaseTool(temp_database)

    # Test different cases
    flour1 = db.get_material_cost('flour')
    flour2 = db.get_material_cost('FLOUR')
    flour3 = db.get_material_cost('Flour')

    assert flour1 is not None
    assert flour2 is not None
    assert flour3 is not None
    assert flour1.name == flour2.name == flour3.name
