"""
Enterprise Database Explorer & Metadata Service.

Provides secure, read-only introspection of PostgreSQL databases, tables,
detailed schemas (column types, nullability, primary keys), and paginated record views.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
import uuid

import psycopg2
from psycopg2 import sql

from app.core.config import get_settings
from app.core.logging import logger
from app.db.connection import (
    get_db_connection_for,
    get_readonly_connection_for,
    switch_active_database,
)
from app.db.schema import extract_schema
from app.models.admin import (
    ColumnDetail,
    DatabaseInfo,
    TableInfo,
    TableRecordsResponse,
    TableSchemaResponse,
)
from app.services.csv_ingestion import clean_database_name, sanitize_identifier

settings = get_settings()

FORBIDDEN_DATABASES = {"postgres", "template0", "template1"}


def serialize_cell(val: Any) -> Any:
    """Serialize database values into JSON-safe representations."""
    if val is None:
        return None
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val) if val % 1 else int(val)
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    return val


class DatabaseExplorerService:
    @classmethod
    def list_databases(cls) -> list[DatabaseInfo]:
        """List all non-template databases available on the PostgreSQL cluster."""
        try:
            with get_readonly_connection_for("postgres") as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT datname
                        FROM pg_database
                        WHERE datistemplate = false
                        ORDER BY datname;
                        """
                    )
                    db_names = [row[0] for row in cur.fetchall()]
                    current_db = settings.DB_NAME
                    return [
                        DatabaseInfo(
                            database_name=d,
                            is_current=(d.lower() == current_db.lower()),
                        )
                        for d in db_names
                    ]
        except Exception as exc:
            logger.warning(f"Could not list databases from maintenance connection: {exc}")
            # Fallback to current database
            return [DatabaseInfo(database_name=settings.DB_NAME, is_current=True)]

    @classmethod
    def list_tables(cls, db_name: str | None = None) -> list[TableInfo]:
        """List all public base tables in the specified database with column lists and row counts."""
        target_db = clean_database_name(db_name, settings.DB_NAME)
        with get_readonly_connection_for(target_db) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                    """
                )
                tables = [r[0] for r in cur.fetchall()]

                result: list[TableInfo] = []
                for table in tables:
                    # Get columns
                    cur.execute(
                        """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = %s
                        ORDER BY ordinal_position;
                        """,
                        (table,),
                    )
                    cols = [r[0] for r in cur.fetchall()]

                    # Get row count safely
                    try:
                        cur.execute(sql.SQL("SELECT COUNT(*) FROM {};").format(sql.Identifier(table)))
                        cnt = cur.fetchone()[0]
                    except Exception:
                        cnt = 0

                    result.append(
                        TableInfo(
                            table_name=table,
                            columns=cols,
                            row_count=cnt,
                        )
                    )
                return result

    @classmethod
    def get_table_schema(cls, db_name: str | None, table_name: str) -> TableSchemaResponse:
        """Fetch column definitions, PostgreSQL data types, nullability, defaults, and primary keys."""
        target_db = clean_database_name(db_name, settings.DB_NAME)
        clean_table = table_name.strip()

        with get_readonly_connection_for(target_db) as conn:
            with conn.cursor() as cur:
                # 1. Fetch Primary Keys
                cur.execute(
                    """
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                     AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                      AND tc.table_schema = 'public'
                      AND tc.table_name = %s;
                    """,
                    (clean_table,),
                )
                pk_columns = {row[0] for row in cur.fetchall()}

                # 2. Fetch Columns metadata
                cur.execute(
                    """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position;
                    """,
                    (clean_table,),
                )
                rows = cur.fetchall()
                if not rows:
                    raise ValueError(f"Table '{clean_table}' not found in database '{target_db}'.")

                columns = [
                    ColumnDetail(
                        name=r[0],
                        type=r[1].upper(),
                        is_nullable=(r[2].upper() == "YES"),
                        default_value=r[3],
                        is_primary_key=(r[0] in pk_columns),
                    )
                    for r in rows
                ]

                return TableSchemaResponse(
                    database=target_db,
                    table=clean_table,
                    columns=columns,
                )

    @classmethod
    def get_table_records(
        cls,
        db_name: str | None,
        table_name: str,
        limit: int = 50,
        offset: int = 0,
    ) -> TableRecordsResponse:
        """Fetch paginated live records from the selected table in read-only mode."""
        target_db = clean_database_name(db_name, settings.DB_NAME)
        clean_table = table_name.strip()

        # Enforce safe bounds
        safe_limit = min(max(1, limit), 100)
        safe_offset = max(0, offset)

        with get_readonly_connection_for(target_db) as conn:
            with conn.cursor() as cur:
                # Count total records
                cur.execute(sql.SQL("SELECT COUNT(*) FROM {};").format(sql.Identifier(clean_table)))
                total_records = cur.fetchone()[0]

                # Fetch paginated rows
                query = sql.SQL("SELECT * FROM {} LIMIT %s OFFSET %s;").format(
                    sql.Identifier(clean_table)
                )
                cur.execute(query, (safe_limit, safe_offset))
                col_names = [desc[0] for desc in cur.description] if cur.description else []
                raw_rows = cur.fetchall()

                # Clean cell serialization
                serialized_rows = [
                    [serialize_cell(cell) for cell in row]
                    for row in raw_rows
                ]

                return TableRecordsResponse(
                    database=target_db,
                    table=clean_table,
                    columns=col_names,
                    rows=serialized_rows,
                    total_records=total_records,
                    limit=safe_limit,
                    offset=safe_offset,
                )

    @classmethod
    def drop_database(cls, db_name: str) -> None:
        """Drop a PostgreSQL database after terminating active backend connections."""
        target_db = (db_name or "").strip()
        if not target_db:
            raise ValueError("Database name is required.")
        if target_db.lower() in FORBIDDEN_DATABASES:
            raise ValueError(
                f"System and maintenance databases ({', '.join(sorted(FORBIDDEN_DATABASES))}) cannot be deleted."
            )

        was_active = target_db.lower() == settings.DB_NAME.lower()

        with get_db_connection_for("postgres") as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                # Terminate open connections to the target database
                cur.execute(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = %s AND pid <> pg_backend_pid();
                    """,
                    (target_db,),
                )
                cur.execute(sql.SQL("DROP DATABASE IF EXISTS {};").format(sql.Identifier(target_db)))

        logger.warning(f"Database '{target_db}' was dropped by admin.")

        # Fall back to default maintenance database if the active database was dropped
        if was_active:
            switch_active_database("postgres")

    @classmethod
    def drop_table(cls, db_name: str | None, table_name: str, cascade: bool = True) -> None:
        """Drop a table in the specified database."""
        target_db = clean_database_name(db_name, settings.DB_NAME)
        clean_table = table_name.strip()
        if not clean_table:
            raise ValueError("Table name is required.")

        with get_db_connection_for(target_db) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cascade_kw = sql.SQL(" CASCADE") if cascade else sql.SQL("")
                cur.execute(
                    sql.SQL("DROP TABLE IF EXISTS {}{};").format(
                        sql.Identifier(clean_table), cascade_kw
                    )
                )

        logger.warning(f"Table '{target_db}.{clean_table}' was dropped by admin.")

        if target_db.lower() == settings.DB_NAME.lower():
            try:
                extract_schema(force_refresh=True)
            except Exception as exc:
                logger.warning(f"Failed to refresh schema cache after dropping table: {exc}")

    @classmethod
    def drop_column(
        cls, db_name: str | None, table_name: str, column_name: str, cascade: bool = True
    ) -> None:
        """Drop a column from a table in the specified database."""
        target_db = clean_database_name(db_name, settings.DB_NAME)
        clean_table = table_name.strip()
        clean_col = column_name.strip()
        if not clean_table or not clean_col:
            raise ValueError("Table name and column name are required.")

        with get_db_connection_for(target_db) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cascade_kw = sql.SQL(" CASCADE") if cascade else sql.SQL("")
                cur.execute(
                    sql.SQL("ALTER TABLE {} DROP COLUMN IF EXISTS {}{};").format(
                        sql.Identifier(clean_table),
                        sql.Identifier(clean_col),
                        cascade_kw,
                    )
                )

        logger.warning(f"Column '{clean_col}' in '{target_db}.{clean_table}' was dropped by admin.")

        if target_db.lower() == settings.DB_NAME.lower():
            try:
                extract_schema(force_refresh=True)
            except Exception as exc:
                logger.warning(f"Failed to refresh schema cache after dropping column: {exc}")

    @classmethod
    def delete_rows(cls, db_name: str | None, table_name: str, condition: dict[str, Any]) -> int:
        """Delete specific rows matching a condition dictionary from the table."""
        target_db = clean_database_name(db_name, settings.DB_NAME)
        clean_table = table_name.strip()
        if not clean_table:
            raise ValueError("Table name is required.")
        if not condition:
            raise ValueError("Delete condition must specify at least one column filter.")

        where_clauses = []
        param_values = []
        for col, val in condition.items():
            where_clauses.append(sql.SQL("{} = %s").format(sql.Identifier(col.strip())))
            param_values.append(val)

        where_sql = sql.SQL(" AND ").join(where_clauses)
        query = sql.SQL("DELETE FROM {} WHERE {};").format(sql.Identifier(clean_table), where_sql)

        with get_db_connection_for(target_db) as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(param_values))
                affected = cur.rowcount
            conn.commit()

        logger.info(f"Deleted {affected} row(s) from '{target_db}.{clean_table}'.")
        return affected

    @classmethod
    def truncate_table(cls, db_name: str | None, table_name: str, cascade: bool = True) -> None:
        """Truncate all rows from the specified table."""
        target_db = clean_database_name(db_name, settings.DB_NAME)
        clean_table = table_name.strip()
        if not clean_table:
            raise ValueError("Table name is required.")

        with get_db_connection_for(target_db) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cascade_kw = sql.SQL(" CASCADE") if cascade else sql.SQL("")
                cur.execute(
                    sql.SQL("TRUNCATE TABLE {}{};").format(sql.Identifier(clean_table), cascade_kw)
                )

        logger.warning(f"Table '{target_db}.{clean_table}' was truncated by admin.")


db_explorer_service = DatabaseExplorerService()

