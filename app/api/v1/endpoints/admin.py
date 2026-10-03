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
    DeleteResponse,
    DeleteRowRequest,
    MultiCsvImportResponse,
    MultiSheetImportResponse,
    SwitchDatabaseRequest,
    SwitchDatabaseResponse,
    TableInfo,
    TableRecordsResponse,
    TableSchemaResponse,
)
from app.services.csv_ingestion import csv_ingestion_service, is_excel_file
from app.services.db_explorer import db_explorer_service

router = APIRouter()
settings = get_settings()

VALID_EXTENSIONS = (".csv", ".xlsx", ".xls", ".xlsm")


def is_valid_dataset_file(filename: str, content: bytes) -> bool:
    fn = filename.lower()
    if any(fn.endswith(ext) for ext in VALID_EXTENSIONS):
        return True
    if is_excel_file(filename, content):
        return True
    # Fallback: check if content looks like delimited text/csv
    try:
        sample = content[:4096].decode("utf-8", errors="ignore")
        if any(sep in sample for sep in (",", ";", "\t", "|")):
            return True
    except Exception:
        pass
    return False


@router.post(
    "/preview-csv",
    response_model=CsvPreviewResponse,
    summary="Upload CSV or Excel file to auto-detect schema, sheets, columns, and data types",
)
async def preview_csv(
    file: UploadFile = File(..., description="CSV or Excel file to inspect"),
    sheet_name: str | None = Form(default=None, description="Optional sheet name for multi-sheet Excel files"),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File filename is required.",
        )

    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        if not is_valid_dataset_file(file.filename, content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Please upload a valid .csv, .xlsx, or .xls file.",
            )

        preview = csv_ingestion_service.parse_and_preview(
            file_bytes=content,
            filename=file.filename,
            sheet_name=sheet_name,
        )
        return preview
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"Error parsing file preview: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview file: {str(exc)}",
        )


@router.post(
    "/import-csv",
    response_model=CsvImportResponse,
    summary="Create table and bulk import CSV/Excel data into PostgreSQL",
)
async def import_csv(
    file: UploadFile = File(..., description="CSV or Excel file to import"),
    table_name: str = Form(..., description="Target PostgreSQL table name"),
    db_name: str | None = Form(default=None, description="Target PostgreSQL database name"),
    mode: str = Form(default="replace", description="Conflict mode: 'replace', 'fail', or 'append'"),
    column_types: str | None = Form(default=None, description="Optional JSON map of column name to PostgreSQL type"),
    sheet_name: str | None = Form(default=None, description="Optional sheet name if file is an Excel workbook"),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File filename is required.",
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
                detail="Uploaded file is empty.",
            )

        if not is_valid_dataset_file(file.filename, content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Please upload a valid .csv, .xlsx, or .xls file.",
            )

        result = csv_ingestion_service.ingest_csv(
            file_bytes=content,
            table_name=table_name,
            db_name=db_name or settings.DB_NAME,
            mode=mode,
            custom_column_types=parsed_col_types,
            sheet_name=sheet_name,
            filename=file.filename,
        )
        return result
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"Failed to import file: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest file into database: {str(exc)}",
        )


@router.post(
    "/import-all-sheets",
    response_model=MultiSheetImportResponse,
    summary="Batch import all sheets of an Excel workbook as separate relational PostgreSQL tables",
)
async def import_all_sheets(
    file: UploadFile = File(..., description="Excel workbook (.xlsx, .xls) to import"),
    db_name: str | None = Form(default=None, description="Target PostgreSQL database name"),
    mode: str = Form(default="replace", description="Conflict mode: 'replace', 'fail', or 'append'"),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File filename is required.",
        )

    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        if not is_excel_file(file.filename, content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an Excel workbook (.xlsx or .xls) to import multiple sheets.",
            )

        result = csv_ingestion_service.ingest_all_sheets(
            file_bytes=content,
            filename=file.filename,
            db_name=db_name or settings.DB_NAME,
            mode=mode,
        )
        return result
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"Failed to import Excel sheets: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch import Excel sheets: {str(exc)}",
        )


@router.get(
    "/databases",
    response_model=list[DatabaseInfo],
    summary="List available PostgreSQL databases on the server",
)
def list_databases():
    try:
        return db_explorer_service.list_databases()
    except Exception as exc:
        logger.error(f"Failed to list databases: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list databases: {str(exc)}",
        )


@router.get(
    "/tables",
    response_model=list[TableInfo],
    summary="List all tables, column lists, and row counts in specified or active PostgreSQL DB",
)
def list_tables(db_name: str | None = None):
    try:
        return db_explorer_service.list_tables(db_name)
    except Exception as exc:
        logger.error(f"Failed to list tables: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tables: {str(exc)}",
        )


@router.get(
    "/tables/{table_name}/schema",
    response_model=TableSchemaResponse,
    summary="Inspect detailed column schema (types, nullability, defaults, primary keys)",
)
def get_table_schema(table_name: str, db_name: str | None = None):
    try:
        return db_explorer_service.get_table_schema(db_name, table_name)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"Failed to inspect table schema: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to inspect table schema: {str(exc)}",
        )


@router.get(
    "/tables/{table_name}/records",
    response_model=TableRecordsResponse,
    summary="Fetch paginated live records from the selected table in read-only mode",
)
def get_table_records(
    table_name: str,
    db_name: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    try:
        return db_explorer_service.get_table_records(db_name, table_name, limit=limit, offset=offset)
    except Exception as exc:
        logger.error(f"Failed to fetch table records: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch table records: {str(exc)}",
        )


@router.post(
    "/switch-db",
    response_model=SwitchDatabaseResponse,
    summary="Switch the active database for the ChatSQL engine and connection pool",
)
def switch_database(req: SwitchDatabaseRequest):
    try:
        from app.db.connection import switch_active_database

        clean_name = req.database_name.strip()
        switch_active_database(clean_name)
        return SwitchDatabaseResponse(
            status="success",
            active_database=clean_name,
            message=f"Active database successfully switched to '{clean_name}'. ChatSQL is now querying this database.",
        )
    except Exception as exc:
        logger.error(f"Failed to switch database: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to switch database: {str(exc)}",
        )


@router.post(
    "/import-multiple-csvs",
    response_model=MultiCsvImportResponse,
    summary="Batch upload and import multiple CSV or Excel files into PostgreSQL as separate tables",
)
async def import_multiple_csvs(
    files: list[UploadFile] = File(..., description="List of CSV or Excel files to import"),
    db_name: str | None = Form(default=None, description="Target PostgreSQL database name"),
    mode: str = Form(default="replace", description="Conflict mode: 'replace', 'fail', or 'append'"),
):
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required.",
        )

    prepared_files: list[tuple[str, bytes]] = []
    for f in files:
        if not f.filename:
            continue
        content = await f.read()
        if not content:
            continue
        if not is_valid_dataset_file(f.filename, content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{f.filename}' is not a valid CSV or Excel file.",
            )
        prepared_files.append((f.filename, content))

    if not prepared_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid file contents received.",
        )

    try:
        result = csv_ingestion_service.ingest_multiple_files(
            files=prepared_files,
            db_name=db_name or settings.DB_NAME,
            mode=mode,
        )
        return result
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"Failed to batch import files: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch import files: {str(exc)}",
        )


@router.delete(
    "/databases/{database_name}",
    response_model=DeleteResponse,
    summary="Drop a PostgreSQL database after terminating active client connections",
)
def delete_database(database_name: str):
    try:
        db_explorer_service.drop_database(database_name)
        return DeleteResponse(
            status="success",
            message=f"Database '{database_name}' was successfully dropped.",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"Failed to drop database '{database_name}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to drop database: {str(exc)}",
        )


@router.delete(
    "/tables/{table_name}",
    response_model=DeleteResponse,
    summary="Drop a table from the specified or active PostgreSQL database",
)
def delete_table(table_name: str, db_name: str | None = None, cascade: bool = True):
    try:
        db_explorer_service.drop_table(db_name, table_name, cascade=cascade)
        return DeleteResponse(
            status="success",
            message=f"Table '{table_name}' was successfully dropped.",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"Failed to drop table '{table_name}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to drop table: {str(exc)}",
        )


@router.delete(
    "/tables/{table_name}/columns/{column_name}",
    response_model=DeleteResponse,
    summary="Drop a column from a table in the specified or active database",
)
def delete_column(
    table_name: str,
    column_name: str,
    db_name: str | None = None,
    cascade: bool = True,
):
    try:
        db_explorer_service.drop_column(db_name, table_name, column_name, cascade=cascade)
        return DeleteResponse(
            status="success",
            message=f"Column '{column_name}' was successfully dropped from '{table_name}'.",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"Failed to drop column '{column_name}' from '{table_name}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to drop column: {str(exc)}",
        )


@router.post(
    "/tables/{table_name}/rows/delete",
    response_model=DeleteResponse,
    summary="Delete specific rows matching a condition from a table",
)
def delete_rows(table_name: str, req: DeleteRowRequest):
    try:
        affected = db_explorer_service.delete_rows(req.database, table_name, req.condition)
        return DeleteResponse(
            status="success",
            message=f"Successfully deleted {affected} row(s) from '{table_name}'.",
            affected_count=affected,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"Failed to delete rows from '{table_name}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete rows: {str(exc)}",
        )


@router.post(
    "/tables/{table_name}/truncate",
    response_model=DeleteResponse,
    summary="Truncate (clear all rows) from a table",
)
def truncate_table(table_name: str, db_name: str | None = None, cascade: bool = True):
    try:
        db_explorer_service.truncate_table(db_name, table_name, cascade=cascade)
        return DeleteResponse(
            status="success",
            message=f"Table '{table_name}' was successfully truncated.",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"Failed to truncate table '{table_name}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to truncate table: {str(exc)}",
        )


