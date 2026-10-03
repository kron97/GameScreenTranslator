import sqlite3
import os
import time

class TranslationCache:
    """SQLite-based local translation cache for 0ms ultra-fast lookup and quota saving."""
    def __init__(self, db_path="translation_cache.db"):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_path)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS translation_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_text TEXT UNIQUE NOT NULL,
                    target_text TEXT NOT NULL,
                    engine TEXT DEFAULT 'deepl',
                    usage_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_text ON translation_cache(source_text);")
            conn.commit()

    def lookup(self, source_text: str):
        """Looks up cached translation. Returns translated string if found, else None."""
        if not source_text:
            return None
        
        normalized = source_text.strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT target_text, usage_count FROM translation_cache WHERE source_text = ?",
                (normalized,)
            )
            row = cursor.fetchone()
            if row:
                target_text, count = row
                # Update usage stats
                cursor.execute(
                    "UPDATE translation_cache SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP WHERE source_text = ?",
                    (normalized,)
                )
                conn.commit()
                return target_text
        return None

    def store(self, source_text: str, target_text: str, engine: str = "deepl"):
        """Stores or updates translation in local cache."""
        if not source_text or not target_text:
            return

        normalized_source = source_text.strip()
        normalized_target = target_text.strip()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO translation_cache (source_text, target_text, engine, usage_count, last_used)
                VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(source_text) DO UPDATE SET
                    target_text = excluded.target_text,
                    engine = excluded.engine,
                    usage_count = usage_count + 1,
                    last_used = CURRENT_TIMESTAMP
            """, (normalized_source, normalized_target, engine))
            conn.commit()

    def get_stats(self):
        """Returns total cached entries count."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM translation_cache")
            total = cursor.fetchone()[0]
            return total
