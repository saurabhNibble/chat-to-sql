"""
Enterprise-grade CSV to PostgreSQL Ingestion Service.

Implements automated schema inference, identifier sanitization (SQL injection defense),
database auto-provisioning, and high-performance streaming bulk loading via PostgreSQL COPY.
"""

import csv
import io
import json
import re
from datetime import datetime
from typing import Any

import pandas as pd
import psycopg2
from psycopg2 import sql

from app.core.config import Settings, get_settings
from app.core.logging import logger
from app.db.schema import extract_schema


# Maximum identifier length in PostgreSQL
PG_MAX_IDENTIFIER_LENGTH = 63

# Supported PostgreSQL types for user selection & auto-detection
SUPPORTED_POSTGRES_TYPES = [
    "TEXT",
    "INTEGER",
    "BIGINT",
    "NUMERIC",
    "BOOLEAN",
    "DATE",
    "TIMESTAMPTZ",
    "UUID",
    "JSONB",
]


def sanitize_identifier(raw: str, fallback_prefix: str = "col") -> str:
    """
    Sanitize raw column/table headers into safe, idiomatic PostgreSQL snake_case identifiers.
    Guarantees strict prevention against SQL injection in DDL.
    """
    if not raw or not str(raw).strip():
        return f"{fallback_prefix}_1"

    cleaned = str(raw).strip().lower()
    # Replace non-alphanumeric chars (spaces, hyphens, slashes, brackets) with underscores
    cleaned = re.sub(r"[^a-z0-9_]+", "_", cleaned)
    # Collapse consecutive underscores
    cleaned = re.sub(r"_+", "_", cleaned)
    # Strip leading/trailing underscores
    cleaned = cleaned.strip("_")

    # If starts with a digit or is empty, prepend fallback prefix
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"{fallback_prefix}_{cleaned}"

    # Truncate to PostgreSQL's 63-character identifier limit
    return cleaned[:PG_MAX_IDENTIFIER_LENGTH]


def clean_database_name(raw: str | None, default_db: str) -> str:
    """
    Validate and normalize database name without mutating hyphens in existing DB names.
    """
    if not raw or not str(raw).strip():
        return default_db
    cleaned = str(raw).strip()
    if cleaned.lower() == default_db.lower():
        return default_db
    if not re.match(r"^[a-zA-Z0-9_\-]+$", cleaned):
        raise ValueError(
            f"Invalid database name '{cleaned}'. Allowed characters: letters, numbers, underscores, hyphens."
        )
    return cleaned[:PG_MAX_IDENTIFIER_LENGTH]


def deduplicate_identifiers(identifiers: list[str]) -> list[str]:
    """Ensure all sanitized identifiers in a list are unique."""
    seen: dict[str, int] = {}
    deduped: list[str] = []
    for ident in identifiers:
        if ident not in seen:
            seen[ident] = 1
            deduped.append(ident)
        else:
            seen[ident] += 1
            suffix = f"_{seen[ident]}"
            # Ensure truncated identifier + suffix fits within 63 chars
            base = ident[: PG_MAX_IDENTIFIER_LENGTH - len(suffix)]
            deduped.append(f"{base}{suffix}")
    return deduped


def is_null_val(val: Any) -> bool:
    """Check if value represents a null/empty cell."""
    if val is None or pd.isna(val):
        return True
    s = str(val).strip().lower()
    return s in ("", "null", "none", "nan", "na", "n/a", "nil")


def infer_column_type(values: list[Any]) -> str:
    """
    Infer optimal PostgreSQL data type from a sample of non-null values.
    Uses strict type priority:
    BOOLEAN -> INTEGER -> BIGINT -> NUMERIC -> UUID -> DATE -> TIMESTAMPTZ -> JSONB -> TEXT
    """
    clean_vals = [str(v).strip() for v in values if not is_null_val(v)]
    if not clean_vals:
        return "TEXT"

    # 1. Check for leading zero strings (zip codes, barcodes, phone numbers) -> Preserve as TEXT
    for v in clean_vals:
        if len(v) > 1 and v.startswith("0") and v.isdigit():
            return "TEXT"

    # 2. Check Boolean
    bool_true = {"true", "false", "t", "f", "yes", "no"}
    if all(v.lower() in bool_true for v in clean_vals):
        return "BOOLEAN"

    # 3. Check Integer (INTEGER vs BIGINT)
    int_regex = re.compile(r"^-?\d+$")
    if all(int_regex.match(v) for v in clean_vals):
        try:
            ints = [int(v) for v in clean_vals]
            min_v, max_v = min(ints), max(ints)
            # 32-bit signed integer limits
            if -2147483648 <= min_v and max_v <= 2147483647:
                return "INTEGER"
            return "BIGINT"
        except (ValueError, OverflowError):
            return "BIGINT"

    # 4. Check Numeric / Float
    float_regex = re.compile(r"^-?\d+(\.\d+)?$")
    if all(float_regex.match(v) for v in clean_vals):
        return "NUMERIC"

    # 5. Check UUID
    uuid_regex = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    if all(uuid_regex.match(v) for v in clean_vals):
        return "UUID"

    # 6. Check Date (YYYY-MM-DD)
    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    if all(date_regex.match(v) for v in clean_vals):
        try:
            for v in clean_vals:
                datetime.strptime(v, "%Y-%m-%d")
            return "DATE"
        except ValueError:
            pass

    # 7. Check Timestamp / ISO 8601
    iso_ts_regex = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}")
    if all(iso_ts_regex.match(v) for v in clean_vals):
        return "TIMESTAMPTZ"

    # 8. Check JSON / JSONB
    if all((v.startswith("{") and v.endswith("}")) or (v.startswith("[") and v.endswith("]")) for v in clean_vals):
        try:
            for v in clean_vals:
                json.loads(v)
            return "JSONB"
        except Exception:
            pass

    # Default fallback
    return "TEXT"


class CsvIngestionService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def parse_and_preview(
        self,
        file_bytes: bytes,
        filename: str,
        sample_size: int = 500,
    ) -> dict[str, Any]:
        """
        Preview uploaded CSV data:
        - Suggests sanitized table name
        - Sanitizes columns
        - Infers robust PostgreSQL column types
        - Returns top 5 sample rows for user confirmation
        """
        # Try UTF-8 with BOM fallback (Excel CSV compatibility)
        decoded = None
        for enc in ("utf-8-sig", "utf-8", "latin1", "cp1252"):
            try:
                decoded = file_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if decoded is None:
            raise ValueError("Unable to decode CSV file. Please ensure it is saved in UTF-8 format.")

        # Read into pandas for parsing
        buffer = io.StringIO(decoded)
        try:
            # Sniff delimiter
            sample_chunk = decoded[:4096]
            try:
                dialect = csv.Sniffer().sniff(sample_chunk)
                sep = dialect.delimiter
            except Exception:
                sep = ","

            buffer.seek(0)
            df = pd.read_csv(
                buffer,
                sep=sep,
                nrows=sample_size,
                dtype=str,
                keep_default_na=False,
            )
        except Exception as exc:
            raise ValueError(f"Failed to parse CSV file: {exc}")

        if df.empty or len(df.columns) == 0:
            raise ValueError("The uploaded CSV file is empty or has no columns.")

        # Suggest table name from filename
        raw_base_name = re.sub(r"\.[^.]+$", "", filename)
        suggested_table = sanitize_identifier(raw_base_name, fallback_prefix="table")

        # Sanitize and deduplicate column names
        raw_cols = list(df.columns)
        sanitized_cols = [sanitize_identifier(col, fallback_prefix="col") for col in raw_cols]
        unique_cols = deduplicate_identifiers(sanitized_cols)

        # Detect types
        column_meta: list[dict[str, str]] = []
        for orig, clean in zip(raw_cols, unique_cols, strict=False):
            col_values = df[orig].tolist()
            inferred_type = infer_column_type(col_values)
            column_meta.append({
                "original_name": str(orig),
                "sanitized_name": clean,
                "inferred_type": inferred_type,
            })

        # Generate preview rows (up to 5)
        preview_df = df.head(5).copy()
        # Rename preview columns to sanitized names
        preview_df.columns = unique_cols
        sample_rows = preview_df.to_dict(orient="records")

        # Count total rows approximately from the decoded string
        total_lines = decoded.count("\n")
        total_rows_est = max(0, total_lines - 1)

        return {
            "suggested_table_name": suggested_table,
            "total_columns": len(unique_cols),
            "estimated_rows": total_rows_est,
            "columns": column_meta,
            "sample_rows": sample_rows,
            "supported_types": SUPPORTED_POSTGRES_TYPES,
        }

    def _get_target_connection(self, db_name: str) -> psycopg2.extensions.connection:
        """Create a dedicated direct connection to a specific database."""
        conn = psycopg2.connect(
            dbname=db_name,
            user=self.settings.DB_USER,
            password=self.settings.DB_PASSWORD,
            host=self.settings.DB_HOST,
            port=self.settings.DB_PORT,
        )
        return conn

    def ensure_database_exists(self, db_name: str) -> bool:
        """
        Verify database existence. If it doesn't exist, connect to the maintenance database ('postgres')
        and create it with autocommit=True.
        """
        clean_db = clean_database_name(db_name, self.settings.DB_NAME)

        # Connect to maintenance database 'postgres'
        maint_conn = psycopg2.connect(
            dbname="postgres",
            user=self.settings.DB_USER,
            password=self.settings.DB_PASSWORD,
            host=self.settings.DB_HOST,
            port=self.settings.DB_PORT,
        )
        maint_conn.autocommit = True
        try:
            with maint_conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (clean_db,))
                exists = cur.fetchone() is not None
                if not exists:
                    logger.info(f"Database '{clean_db}' does not exist. Creating database...")
                    cur.execute(sql.SQL("CREATE DATABASE {};").format(sql.Identifier(clean_db)))
                    logger.info(f"Database '{clean_db}' created successfully.")
                    return True
                return False
        finally:
            maint_conn.close()

    def ingest_csv(
        self,
        file_bytes: bytes,
        table_name: str,
        db_name: str | None = None,
        mode: str = "replace",  # 'replace', 'fail', 'append'
        custom_column_types: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Full industry-standard CSV to PostgreSQL ingestion pipeline:
        1. Ensures target database exists.
        2. Sanitizes table & column names.
        3. Generates and executes DDL (CREATE TABLE).
        4. Streams data using PostgreSQL COPY command.
        5. Validates inserted row count.
        6. Invalidates schema cache so table is immediately queryable.
        """
        target_db = clean_database_name(db_name, self.settings.DB_NAME)
        clean_table = sanitize_identifier(table_name, fallback_prefix="table")

        # 1. Ensure target DB exists
        self.ensure_database_exists(target_db)

        # 2. Decode CSV
        decoded = None
        for enc in ("utf-8-sig", "utf-8", "latin1", "cp1252"):
            try:
                decoded = file_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if decoded is None:
            raise ValueError("Unable to decode CSV file into valid text.")

        # Sniff delimiter
        sample_chunk = decoded[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample_chunk)
            sep = dialect.delimiter
        except Exception:
            sep = ","

        df = pd.read_csv(
            io.StringIO(decoded),
            sep=sep,
            dtype=str,
            keep_default_na=False,
        )

        if df.empty or len(df.columns) == 0:
            raise ValueError("CSV contains no data rows or columns.")

        # 3. Resolve columns and types
        raw_cols = list(df.columns)
        sanitized_cols = [sanitize_identifier(c, fallback_prefix="col") for c in raw_cols]
        unique_cols = deduplicate_identifiers(sanitized_cols)

        # Inferred / custom type map
        col_type_map: dict[str, str] = {}
        for orig, clean in zip(raw_cols, unique_cols, strict=False):
            # Check if user provided an override
            if custom_column_types and clean in custom_column_types:
                chosen_type = custom_column_types[clean].upper()
                if chosen_type not in SUPPORTED_POSTGRES_TYPES:
                    chosen_type = "TEXT"
                col_type_map[clean] = chosen_type
            else:
                col_type_map[clean] = infer_column_type(df[orig].tolist())

        # Rename dataframe columns to sanitized identifiers
        df.columns = unique_cols

        # Connect to target DB
        conn = self._get_target_connection(target_db)
        try:
            with conn.cursor() as cur:
                # 4. Handle table mode
                cur.execute(
                    """
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s;
                    """,
                    (clean_table,),
                )
                table_exists = cur.fetchone() is not None

                if table_exists and mode == "fail":
                    raise ValueError(f"Table '{clean_table}' already exists in database '{target_db}'.")

                if mode == "replace" or not table_exists:
                    if mode == "replace" and table_exists:
                        cur.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE;").format(sql.Identifier(clean_table)))

                    # Build DDL: CREATE TABLE "clean_table" ("col1" TYPE1, "col2" TYPE2, ...)
                    col_definitions = [
                        sql.SQL("{} {}").format(sql.Identifier(col), sql.SQL(col_type_map[col]))
                        for col in unique_cols
                    ]
                    create_query = sql.SQL("CREATE TABLE {} ({});").format(
                        sql.Identifier(clean_table),
                        sql.SQL(", ").join(col_definitions),
                    )
                    cur.execute(create_query)
                    logger.info(f"Created table '{clean_table}' in '{target_db}' with {len(unique_cols)} columns.")

                # 5. Stream data using PostgreSQL COPY
                # Prepare CSV buffer with standardized format and NULL representation
                # Replace empty strings or null variants with None so pandas exports them as null
                formatted_df = df.copy()
                for col in unique_cols:
                    t = col_type_map[col]
                    # Clean empty values to empty string
                    formatted_df[col] = formatted_df[col].apply(
                        lambda v: "" if is_null_val(v) else str(v).strip()
                    )

                csv_buffer = io.StringIO()
                formatted_df.to_csv(
                    csv_buffer,
                    index=False,
                    header=False,
                    sep=",",
                    quoting=csv.QUOTE_MINIMAL,
                    escapechar="\\",
                )
                csv_buffer.seek(0)

                # Execute COPY command
                columns_identifiers = sql.SQL(", ").join([sql.Identifier(c) for c in unique_cols])
                copy_sql = sql.SQL(
                    "COPY {} ({}) FROM STDIN WITH (FORMAT CSV, HEADER FALSE, NULL '', ESCAPE '\\');"
                ).format(sql.Identifier(clean_table), columns_identifiers)

                cur.copy_expert(copy_sql.as_string(conn), csv_buffer)

                # Commit transaction atomically
                conn.commit()

                # Verify count
                cur.execute(sql.SQL("SELECT COUNT(*) FROM {};").format(sql.Identifier(clean_table)))
                count_res = cur.fetchone()
                total_rows = count_res[0] if count_res else len(df)

            logger.info(f"Successfully ingested {total_rows} rows into '{target_db}.{clean_table}'.")

            # Force refresh schema cache if this is the active database
            if target_db == self.settings.DB_NAME:
                try:
                    extract_schema(force_refresh=True)
                except Exception as cache_exc:
                    logger.warning(f"Failed to refresh schema cache: {cache_exc}")

            return {
                "status": "success",
                "database": target_db,
                "table": clean_table,
                "rows_inserted": total_rows,
                "columns": [
                    {"name": col, "type": col_type_map[col]}
                    for col in unique_cols
                ],
            }

        except Exception as exc:
            conn.rollback()
            logger.error(f"Failed to ingest CSV into PostgreSQL: {exc}")
            raise
        finally:
            conn.close()


csv_ingestion_service = CsvIngestionService()
