from typing import Any
from pydantic import BaseModel, Field


class ColumnMeta(BaseModel):
    original_name: str
    sanitized_name: str
    inferred_type: str


class CsvPreviewResponse(BaseModel):
    suggested_table_name: str
    total_columns: int
    estimated_rows: int
    columns: list[ColumnMeta]
    sample_rows: list[dict[str, Any]]
    supported_types: list[str]


class CsvImportResponse(BaseModel):
    status: str
    database: str
    table: str
    rows_inserted: int
    columns: list[dict[str, str]]


class TableInfo(BaseModel):
    table_name: str
    columns: list[str]
    row_count: int


class DatabaseInfo(BaseModel):
    database_name: str
    is_current: bool
