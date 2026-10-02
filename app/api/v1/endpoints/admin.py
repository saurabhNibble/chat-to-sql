import json
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.core.logging import logger
from app.db.connection import get_db_connection
from app.models.admin import (
    CsvImportResponse,
    CsvPreviewResponse,
    DatabaseInfo,
    TableInfo,
)
from app.services.csv_ingestion import csv_ingestion_service

router = APIRouter()
settings = get_settings()


@router.post(
    "/preview-csv",
    response_model=CsvPreviewResponse,
    summary="Upload CSV to auto-detect schema, columns, and data types",
)
async def preview_csv(
    file: UploadFile = File(..., description="CSV file to inspect"),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a valid .csv file.",
        )

    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded CSV file is empty.",
            )

        preview = csv_ingestion_service.parse_and_preview(
            file_bytes=content,
            filename=file.filename,
        )
        return preview
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"Error parsing CSV preview: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview CSV: {str(exc)}",
        )


@router.post(
    "/import-csv",
    response_model=CsvImportResponse,
    summary="Create table and bulk import CSV data into PostgreSQL",
)
async def import_csv(
    file: UploadFile = File(..., description="CSV file to import"),
    table_name: str = Form(..., description="Target PostgreSQL table name"),
    db_name: str | None = Form(default=None, description="Target PostgreSQL database name"),
    mode: str = Form(default="replace", description="Conflict mode: 'replace', 'fail', or 'append'"),
    column_types: str | None = Form(default=None, description="Optional JSON map of column name to PostgreSQL type"),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a valid .csv file.",
        )

    parsed_col_types: dict[str, str] = {}
    if column_types:
        try:
            parsed = json.loads(column_types)
            if isinstance(parsed, dict):
                parsed_col_types = {str(k): str(v) for k, v in parsed.items()}
        except Exception:
            logger.warning(f"Failed to parse column_types JSON: {column_types}")

    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded CSV file is empty.",
            )

        result = csv_ingestion_service.ingest_csv(
            file_bytes=content,
            table_name=table_name,
            db_name=db_name or settings.DB_NAME,
            mode=mode,
            custom_column_types=parsed_col_types,
        )
        return result
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"Failed to import CSV: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest CSV into database: {str(exc)}",
        )


@router.get(
    "/tables",
    response_model=list[TableInfo],
    summary="List all tables, column lists, and row counts in current PostgreSQL DB",
)
def list_tables():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT t.table_name
                    FROM information_schema.tables t
                    WHERE t.table_schema = 'public'
                      AND t.table_type = 'BASE TABLE'
                    ORDER BY t.table_name;
                    """
                )
                tables = [r[0] for r in cur.fetchall()]

                table_infos: list[TableInfo] = []
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

                    # Get approximate/exact row count
                    try:
                        cur.execute(f'SELECT COUNT(*) FROM "{table}";')
                        count = cur.fetchone()[0]
                    except Exception:
                        count = 0

                    table_infos.append(
                        TableInfo(
                            table_name=table,
                            columns=cols,
                            row_count=count,
                        )
                    )
                return table_infos
    except Exception as exc:
        logger.error(f"Failed to list tables: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tables: {str(exc)}",
        )


@router.get(
    "/databases",
    response_model=list[DatabaseInfo],
    summary="List available PostgreSQL databases on the server",
)
def list_databases():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT datname
                    FROM pg_database
                    WHERE datistemplate = false
                    ORDER BY datname;
                    """
                )
                dbs = [r[0] for r in cur.fetchall()]
                current_db = settings.DB_NAME
                return [
                    DatabaseInfo(
                        database_name=d,
                        is_current=(d.lower() == current_db.lower()),
                    )
                    for d in dbs
                ]
    except Exception as exc:
        logger.warning(f"Failed to list databases: {exc}")
        return [DatabaseInfo(database_name=settings.DB_NAME, is_current=True)]
