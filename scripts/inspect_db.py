#!/usr/bin/env python3
"""
Database Schema Inspection Utility.
Introspects and displays all public tables, columns, and data types.
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.connection import get_db_connection  # noqa: E402


def inspect_schema() -> None:
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name;
                """
            )
            tables = [r[0] for r in cursor.fetchall()]

            print(f"--- Found {len(tables)} Tables ---")
            for t in tables:
                cursor.execute(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position;
                    """,
                    (t,),
                )
                cols = cursor.fetchall()
                print(f"\nTable: {t}")
                for c, dtype in cols:
                    print(f"  - {c} ({dtype})")


if __name__ == "__main__":
    inspect_schema()
