"""Database tool - SQLite interface for material costs

Full implementation based on documentation/02_Database_Tool.md
"""
import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


# Custom Exceptions
class DatabaseError(Exception):
    """Base exception for database errors"""
    pass


class MaterialNotFoundError(DatabaseError):
    """Material not found in database"""
    def __init__(self, material_name: str):
        self.material_name = material_name
        super().__init__(f"Material '{material_name}' not found in database")


class DatabaseConnectionError(DatabaseError):
    """Cannot connect to database"""
    pass


@dataclass
class MaterialCost:
    """Material cost data from database"""
    name: str
    unit: str
    unit_cost: float
    currency: str
    last_updated: str

    @classmethod
    def from_row(cls, row: sqlite3.Row):
        """Create from database row"""
        return cls(
            name=row['name'],
            unit=row['unit'],
            unit_cost=row['unit_cost'],
            currency=row['currency'],
            last_updated=row['last_updated']
        )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'unit': self.unit,
            'unit_cost': self.unit_cost,
            'currency': self.currency,
            'last_updated': self.last_updated
        }


class DatabaseTool:
    """Interface to SQLite material costs database"""

    def __init__(self, database_path: str):
        """
        Initialize database connection.
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self._verify_database()
        logger.info(f"DatabaseTool initialized with path: {database_path}")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
        finally:
            conn.close()

    def _verify_database(self):
        """Verify database exists and has correct schema"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='materials'
                """)
                if not cursor.fetchone():
                    raise ValueError(f"Table 'materials' not found in {self.database_path}")

                logger.info(f"Database verified: {self.database_path}")
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Cannot connect to database: {e}")

    # Query Methods

    def get_material_cost(self, material_name: str) -> MaterialCost | None:
        """
        Get cost data for a single material.
        
        Args:
            material_name: Name of the material (e.g., 'flour')
            
        Returns:
            MaterialCost object or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM materials WHERE name = ? COLLATE NOCASE",
                (material_name,)
            )
            row = cursor.fetchone()

            if row:
                logger.debug(f"Found material: {material_name}")
                return MaterialCost.from_row(row)
            else:
                logger.warning(f"Material not found: {material_name}")
                return None

    def get_material_cost_strict(self, material_name: str) -> MaterialCost:
        """
        Get material cost, raising exception if not found.
        
        Args:
            material_name: Name of the material
            
        Returns:
            MaterialCost object
            
        Raises:
            MaterialNotFoundError: If material doesn't exist
        """
        result = self.get_material_cost(material_name)
        if result is None:
            raise MaterialNotFoundError(material_name)
        return result

    def get_materials_bulk(self, material_names: list[str]) -> dict[str, dict]:
        """
        Get cost data for multiple materials in one query (optimized).
        
        Args:
            material_names: List of material names to query
            
        Returns:
            Dictionary mapping material name to cost data (as dict for compatibility)
        """
        if not material_names:
            return {}

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Use parameterized query with IN clause
            placeholders = ','.join('?' * len(material_names))
            query = f"""
                SELECT * FROM materials 
                WHERE name IN ({placeholders}) COLLATE NOCASE
            """

            cursor.execute(query, material_names)
            rows = cursor.fetchall()

            # Build result dictionary (convert to dict for compatibility)
            results = {
                row['name']: MaterialCost.from_row(row).to_dict()
                for row in rows
            }

            # Log missing materials
            found = set(results.keys())
            requested = set(material_names)
            missing = requested - found

            if missing:
                logger.warning(f"Missing materials: {missing}")

            logger.info(f"Retrieved {len(results)}/{len(material_names)} materials")
            return results

    def get_materials_bulk_objects(self, material_names: list[str]) -> dict[str, MaterialCost]:
        """
        Get cost data for multiple materials as MaterialCost objects.
        
        Args:
            material_names: List of material names
            
        Returns:
            Dictionary mapping material name to MaterialCost object
        """
        if not material_names:
            return {}

        with self._get_connection() as conn:
            cursor = conn.cursor()

            placeholders = ','.join('?' * len(material_names))
            query = f"""
                SELECT * FROM materials 
                WHERE name IN ({placeholders}) COLLATE NOCASE
            """

            cursor.execute(query, material_names)
            rows = cursor.fetchall()

            results = {
                row['name']: MaterialCost.from_row(row)
                for row in rows
            }

            return results

    def list_all_materials(self) -> list[MaterialCost]:
        """
        Get all materials from database.
        
        Returns:
            List of all MaterialCost objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM materials ORDER BY name")
            rows = cursor.fetchall()

            materials = [MaterialCost.from_row(row) for row in rows]
            logger.info(f"Retrieved {len(materials)} materials")
            return materials

    def search_materials(self, pattern: str) -> list[MaterialCost]:
        """
        Search materials by name pattern.
        
        Args:
            pattern: Search pattern (will be wrapped with % for LIKE)
            
        Returns:
            List of matching MaterialCost objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM materials WHERE name LIKE ? COLLATE NOCASE ORDER BY name",
                (f"%{pattern}%",)
            )
            rows = cursor.fetchall()

            materials = [MaterialCost.from_row(row) for row in rows]
            logger.debug(f"Found {len(materials)} materials matching '{pattern}'")
            return materials

    # Validation & Helper Methods

    def material_exists(self, material_name: str) -> bool:
        """
        Check if a material exists in the database.
        
        Args:
            material_name: Name of the material
            
        Returns:
            True if material exists, False otherwise
        """
        return self.get_material_cost(material_name) is not None

    def get_available_units(self) -> list[str]:
        """
        Get list of all units used in database.
        
        Returns:
            List of unique unit strings
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT unit FROM materials ORDER BY unit")
            rows = cursor.fetchall()
            return [row['unit'] for row in rows]

    def get_material_count(self) -> int:
        """Get total number of materials in database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM materials")
            return cursor.fetchone()['count']

    def get_database_info(self) -> dict:
        """
        Get summary information about the database.
        
        Returns:
            Dictionary with database statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total materials
            cursor.execute("SELECT COUNT(*) as count FROM materials")
            total = cursor.fetchone()['count']

            # Units
            cursor.execute("SELECT DISTINCT unit FROM materials")
            units = [row['unit'] for row in cursor.fetchall()]

            # Currencies
            cursor.execute("SELECT DISTINCT currency FROM materials")
            currencies = [row['currency'] for row in cursor.fetchall()]

            # Last updated
            cursor.execute("SELECT MAX(last_updated) as latest FROM materials")
            latest = cursor.fetchone()['latest']

            return {
                'total_materials': total,
                'units': units,
                'currencies': currencies,
                'last_updated': latest,
                'path': self.database_path
            }

    # Administrative Functions

    def add_material(
        self,
        name: str,
        unit: str,
        unit_cost: float,
        currency: str = "GBP",
        last_updated: str | None = None
    ) -> bool:
        """
        Add a new material to the database.
        
        Args:
            name: Material name (must be unique)
            unit: Unit of measurement
            unit_cost: Cost per unit
            currency: Currency code
            last_updated: ISO date string (defaults to today)
            
        Returns:
            True if successful, False if material already exists
        """
        if last_updated is None:
            last_updated = datetime.now().strftime("%Y-%m-%d")

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO materials (name, unit, unit_cost, currency, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, unit, unit_cost, currency, last_updated)
                )
                conn.commit()
                logger.info(f"Added material: {name}")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"Material already exists: {name}")
            return False

    def update_material_cost(
        self,
        name: str,
        unit_cost: float,
        last_updated: str | None = None
    ) -> bool:
        """
        Update the cost of an existing material.
        
        Args:
            name: Material name
            unit_cost: New cost per unit
            last_updated: ISO date string (defaults to today)
            
        Returns:
            True if updated, False if material not found
        """
        if last_updated is None:
            last_updated = datetime.now().strftime("%Y-%m-%d")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE materials 
                SET unit_cost = ?, last_updated = ?
                WHERE name = ?
                """,
                (unit_cost, last_updated, name)
            )
            conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"Updated material cost: {name} = {unit_cost}")
                return True
            else:
                logger.warning(f"Material not found for update: {name}")
                return False

    def delete_material(self, name: str) -> bool:
        """
        Delete a material from the database.
        
        Args:
            name: Material name
            
        Returns:
            True if deleted, False if material not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM materials WHERE name = ?", (name,))
            conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"Deleted material: {name}")
                return True
            else:
                logger.warning(f"Material not found for deletion: {name}")
                return False
