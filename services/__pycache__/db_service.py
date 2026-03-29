import sqlite3
import os
from typing import Dict, Optional
from utils.logger import get_logger
from config.settings import settings

logger = get_logger("DB_SERVICE")

SEED_DATA = [
    ("WidgetA", 15),
    ("WidgetB", 10),
    ("GadgetX", 5),
    ("FakeItem", 0),
]

class DBService:
    def __init__(self):
        self.db_path = settings.db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        logger.info("Database initialized at %s" % self.db_path)

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    item_name TEXT PRIMARY KEY,
                    stock INTEGER NOT NULL DEFAULT 0
                )
            """)
            conn.commit()
            # Seed only if empty
            cursor = conn.execute("SELECT COUNT(*) FROM inventory")
            if cursor.fetchone()[0] == 0:
                conn.executemany(
                    "INSERT INTO inventory (item_name, stock) VALUES (?, ?)",
                    SEED_DATA
                )
                conn.commit()
                logger.info("Inventory seeded with default items.")

    def get_item(self, item_name: str) -> Optional[Dict]:
        """Returns item info or None if not found."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT item_name, stock FROM inventory WHERE item_name = ? COLLATE NOCASE",
                (item_name,)
            )
            row = cursor.fetchone()
            if row:
                return {"item_name": row[0], "stock": row[1], "exists": True}
            return {"item_name": item_name, "stock": 0, "exists": False}

    def get_all_items(self) -> list:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT item_name, stock FROM inventory")
            return [{"item_name": r[0], "stock": r[1]} for r in cursor.fetchall()]


db_service = DBService()
