import time
from typing import Any

from app.core.config import get_settings
from app.core.logging import logger
from app.db.connection import get_db_connection, get_readonly_connection

settings = get_settings()

_cached_schema: dict[str, list[str]] | None = None
_cached_time: float = 0.0


def extract_schema(force_refresh: bool = False) -> dict[str, list[str]]:
    """
    Introspect the database public schema and cache the table -> column mappings.
    Caches results according to SCHEMA_CACHE_TTL_SECONDS.
    """
    global _cached_schema, _cached_time
    now = time.time()
    if not force_refresh and _cached_schema is not None and (now - _cached_time) < settings.SCHEMA_CACHE_TTL_SECONDS:
        return _cached_schema

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name;
                """
            )
            tables = [row[0] for row in cursor.fetchall()]

            schema: dict[str, list[str]] = {}
            for table in tables:
                cursor.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = %s
                    ORDER BY ordinal_position;
                    """,
                    (table,),
                )
                schema[table] = [row[0] for row in cursor.fetchall()]

            _cached_schema = schema
            _cached_time = now
            logger.info(f"Schema introspection completed. Discovered {len(schema)} tables.")
            return schema


def execute_readonly_sql(sql: str) -> tuple[list[str], list[list[Any]]]:
    """
    Execute a validated SELECT query inside a PostgreSQL READ ONLY transaction.
    Returns (column_names, rows).
    """
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("A SQL query string is required.")

    with get_readonly_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            if cursor.description is None:
                return [], []
            columns = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()
            # Convert tuples to lists for JSON serialization
            rows = [list(row) for row in raw_rows]
            return columns, rows
