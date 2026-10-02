"""
Enterprise-grade Data Ingestion Service (CSV & Multi-Sheet Excel).

Implements automated schema inference, identifier sanitization (SQL injection defense),
multi-sheet Excel extraction, database auto-provisioning, and high-performance streaming
bulk loading via PostgreSQL native COPY command.
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


def is_excel_file(filename: str, file_bytes: bytes | None = None) -> bool:
    """Determine whether a file is an Excel spreadsheet (.xlsx, .xls) by extension or magic header."""
    fn = filename.lower()
    if fn.endswith((".xlsx", ".xls", ".xlsm", ".xlsb")):
        return True
    if file_bytes and len(file_bytes) >= 4:
        # PK\x03\x04 is standard ZIP archive header used by modern .xlsx files
        if file_bytes.startswith(b"PK\x03\x04") or file_bytes.startswith(b"\xd0\xcf\x11\xe0"):
            return True
    return False


def sanitize_identifier(raw: str, fallback_prefix: str = "col") -> str:
    """
    Sanitize raw column/table headers into safe, idiomatic PostgreSQL snake_case identifiers.
    Converts camelCase/PascalCase (e.g. carCategories -> car_categories) and handles symbols.
    Guarantees strict prevention against SQL injection in DDL.
    """
    if not raw or not str(raw).strip():
        return f"{fallback_prefix}_1"

    text = str(raw).strip()
    # 1. Insert underscore between lowercase/digit and uppercase (carCategories -> car_Categories)
    s1 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    # 2. Insert underscore between consecutive uppercase and lowercase (XMLParser -> XML_Parser)
    s2 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s1)
    cleaned = s2.lower()

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
        sheet_name: str | None = None,
        sample_size: int = 500,
    ) -> dict[str, Any]:
        """
        Preview uploaded CSV or multi-sheet Excel data:
        - Detects format (CSV vs Excel workbook)
        - Discovers sheets if Excel
        - Suggests sanitized table name
        - Sanitizes columns & infers robust PostgreSQL column types
        - Returns top 5 sample rows for user confirmation
        """
        is_excel = is_excel_file(filename, file_bytes)
        sheet_names: list[str] = []
        active_sheet: str | None = None

        if is_excel:
            try:
                excel = pd.ExcelFile(io.BytesIO(file_bytes))
                sheet_names = list(excel.sheet_names)
            except Exception as exc:
                raise ValueError(f"Failed to read Excel workbook: {exc}")

            if not sheet_names:
                raise ValueError("Excel file contains no readable sheets.")

            target_sheet = sheet_name if (sheet_name and sheet_name in sheet_names) else sheet_names[0]
            active_sheet = target_sheet

            try:
                df = pd.read_excel(
                    excel,
                    sheet_name=target_sheet,
                    nrows=sample_size,
                    dtype=str,
                    keep_default_na=False,
                )
            except Exception as exc:
                raise ValueError(f"Failed to read sheet '{target_sheet}': {exc}")

            # Suggest table name from sheet name (e.g. carCategories -> car_categories)
            if len(sheet_names) > 1 or target_sheet.lower() not in ("sheet1", "sheet 1"):
                suggested_table = sanitize_identifier(target_sheet, fallback_prefix="table")
            else:
                raw_base_name = re.sub(r"\.[^.]+$", "", filename)
                suggested_table = sanitize_identifier(raw_base_name, fallback_prefix="table")

            # Fast row count estimate
            try:
                full_sheet = pd.read_excel(excel, sheet_name=target_sheet, usecols=[0], keep_default_na=False)
                total_rows_est = len(full_sheet)
            except Exception:
                total_rows_est = len(df)

        else:
            # CSV Parsing
            decoded = None
            for enc in ("utf-8-sig", "utf-8", "latin1", "cp1252"):
                try:
                    decoded = file_bytes.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue

            if decoded is None:
                raise ValueError("Unable to decode CSV file. Please ensure it is saved in UTF-8 format.")

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

            raw_base_name = re.sub(r"\.[^.]+$", "", filename)
            suggested_table = sanitize_identifier(raw_base_name, fallback_prefix="table")
            total_lines = decoded.count("\n")
            total_rows_est = max(0, total_lines - 1)

        if df.empty or len(df.columns) == 0:
            msg = f"Sheet '{active_sheet}' is empty." if is_excel else "The uploaded file is empty or has no columns."
            raise ValueError(msg)

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
        preview_df.columns = unique_cols
        sample_rows = preview_df.to_dict(orient="records")

        return {
            "suggested_table_name": suggested_table,
            "total_columns": len(unique_cols),
            "estimated_rows": total_rows_est,
            "columns": column_meta,
            "sample_rows": sample_rows,
            "supported_types": SUPPORTED_POSTGRES_TYPES,
            "is_excel": is_excel,
            "sheet_names": sheet_names,
            "active_sheet": active_sheet,
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
        sheet_name: str | None = None,
        filename: str = "",
    ) -> dict[str, Any]:
        """
        Full industry-standard data to PostgreSQL ingestion pipeline (CSV & Excel):
        1. Ensures target database exists.
        2. Reads CSV or specific Excel sheet into DataFrame.
        3. Sanitizes table & column names.
        4. Generates and executes DDL (CREATE TABLE).
        5. Streams data using PostgreSQL native COPY command.
        6. Validates inserted row count.
        7. Invalidates schema cache so table is immediately queryable.
        """
        target_db = clean_database_name(db_name, self.settings.DB_NAME)
        clean_table = sanitize_identifier(table_name, fallback_prefix="table")

        # 1. Ensure target DB exists
        self.ensure_database_exists(target_db)

        # 2. Load DataFrame from CSV or Excel
        is_excel = is_excel_file(filename, file_bytes)
        if is_excel:
            try:
                excel = pd.ExcelFile(io.BytesIO(file_bytes))
                target_sheet = sheet_name or excel.sheet_names[0]
                df = pd.read_excel(excel, sheet_name=target_sheet, dtype=str, keep_default_na=False)
            except Exception as exc:
                raise ValueError(f"Failed to read Excel data: {exc}")
        else:
            decoded = None
            for enc in ("utf-8-sig", "utf-8", "latin1", "cp1252"):
                try:
                    decoded = file_bytes.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue

            if decoded is None:
                raise ValueError("Unable to decode CSV file into valid text.")

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
            raise ValueError("Dataset contains no data rows or columns.")

        # 3. Resolve columns and types
        raw_cols = list(df.columns)
        sanitized_cols = [sanitize_identifier(c, fallback_prefix="col") for c in raw_cols]
        unique_cols = deduplicate_identifiers(sanitized_cols)

        # Inferred / custom type map
        col_type_map: dict[str, str] = {}
        for orig, clean in zip(raw_cols, unique_cols, strict=False):
            if custom_column_types and clean in custom_column_types:
                chosen_type = custom_column_types[clean].upper()
                if chosen_type not in SUPPORTED_POSTGRES_TYPES:
                    chosen_type = "TEXT"
                col_type_map[clean] = chosen_type
            else:
                col_type_map[clean] = infer_column_type(df[orig].tolist())

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
                formatted_df = df.copy()
                for col in unique_cols:
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

                columns_identifiers = sql.SQL(", ").join([sql.Identifier(c) for c in unique_cols])
                copy_sql = sql.SQL(
                    "COPY {} ({}) FROM STDIN WITH (FORMAT CSV, HEADER FALSE, NULL '', ESCAPE '\\');"
                ).format(sql.Identifier(clean_table), columns_identifiers)

                cur.copy_expert(copy_sql.as_string(conn), csv_buffer)
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
                "sheet_name": sheet_name,
                "columns": [
                    {"name": col, "type": col_type_map[col]}
                    for col in unique_cols
                ],
            }

        except Exception as exc:
            conn.rollback()
            logger.error(f"Failed to ingest dataset into PostgreSQL: {exc}")
            raise
        finally:
            conn.close()

    def ingest_all_sheets(
        self,
        file_bytes: bytes,
        filename: str,
        db_name: str | None = None,
        mode: str = "replace",
    ) -> dict[str, Any]:
        """
        Ingest all sheets from an Excel workbook into PostgreSQL as relational tables.
        """
        target_db = clean_database_name(db_name, self.settings.DB_NAME)
        self.ensure_database_exists(target_db)

        try:
            excel = pd.ExcelFile(io.BytesIO(file_bytes))
            sheet_names = list(excel.sheet_names)
        except Exception as exc:
            raise ValueError(f"Failed to read Excel workbook: {exc}")

        if not sheet_names:
            raise ValueError("Workbook contains no readable sheets.")

        results = []
        total_rows = 0

        for sheet in sheet_names:
            table_name = sanitize_identifier(sheet, fallback_prefix="table")
            res = self.ingest_csv(
                file_bytes=file_bytes,
                table_name=table_name,
                db_name=target_db,
                mode=mode,
                sheet_name=sheet,
                filename=filename,
            )
            results.append(res)
            total_rows += res["rows_inserted"]

        return {
            "status": "success",
            "database": target_db,
            "tables": results,
            "total_rows_inserted": total_rows,
        }

    def ingest_multiple_files(
        self,
        files: list[tuple[str, bytes]],
        db_name: str | None = None,
        mode: str = "replace",
    ) -> dict[str, Any]:
        """
        Batch ingest multiple CSV (or Excel) files into PostgreSQL as separate tables.
        """
        target_db = clean_database_name(db_name, self.settings.DB_NAME)
        self.ensure_database_exists(target_db)

        if not files:
            raise ValueError("No files provided for ingestion.")

        results = []
        total_rows = 0

        for filename, content in files:
            if is_excel_file(filename, content):
                res = self.ingest_all_sheets(
                    file_bytes=content,
                    filename=filename,
                    db_name=target_db,
                    mode=mode,
                )
                results.extend(res["tables"])
                total_rows += res["total_rows_inserted"]
            else:
                import os

                stem = os.path.splitext(filename)[0]
                table_name = sanitize_identifier(stem, fallback_prefix="table")
                res = self.ingest_csv(
                    file_bytes=content,
                    table_name=table_name,
                    db_name=target_db,
                    mode=mode,
                    filename=filename,
                )
                results.append(res)
                total_rows += res["rows_inserted"]

        return {
            "status": "success",
            "database": target_db,
            "tables": results,
            "total_rows_inserted": total_rows,
        }


csv_ingestion_service = CsvIngestionService()

