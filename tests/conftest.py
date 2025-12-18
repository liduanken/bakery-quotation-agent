"""Pytest configuration and shared fixtures"""
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_database():
    """Create a temporary test database with sample data"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    # Initialize schema and data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create schema
    cursor.execute("""
        CREATE TABLE materials (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            unit TEXT NOT NULL,
            unit_cost REAL NOT NULL,
            currency TEXT NOT NULL,
            last_updated TEXT NOT NULL
        )
    """)

    # Insert test data
    cursor.executemany(
        "INSERT INTO materials (name, unit, unit_cost, currency, last_updated) VALUES (?, ?, ?, ?, ?)",
        [
            ('flour', 'kg', 0.90, 'GBP', '2025-09-01'),
            ('sugar', 'kg', 0.70, 'GBP', '2025-09-01'),
            ('butter', 'kg', 4.50, 'GBP', '2025-09-01'),
            ('eggs', 'each', 0.18, 'GBP', '2025-09-01'),
            ('milk', 'L', 0.60, 'GBP', '2025-09-01'),
            ('vanilla', 'ml', 0.05, 'GBP', '2025-09-01'),
            ('baking_powder', 'kg', 3.00, 'GBP', '2025-09-01'),
            ('cocoa', 'kg', 6.00, 'GBP', '2025-09-01'),
            ('salt', 'kg', 0.40, 'GBP', '2025-09-01'),
        ]
    )

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    import os
    try:
        os.unlink(db_path)
    except:
        pass
