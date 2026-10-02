"""
CLI tool for automated CSV & Multi-Sheet Excel to PostgreSQL ingestion.

Usage:
    python scripts/import_csv.py <path_to_file> [--db DB_NAME] [--table TABLE_NAME] [--sheet SHEET] [--all-sheets] [--mode replace|fail|append]
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings
from app.core.logging import logger
from app.services.csv_ingestion import csv_ingestion_service, is_excel_file


def main():
    parser = argparse.ArgumentParser(
        description="Auto-detect schema and stream CSV or multi-sheet Excel data into PostgreSQL."
    )
    parser.add_argument("file_path", type=str, help="Path to the .csv or .xlsx file")
    parser.add_argument("--db", type=str, default=None, help="Target PostgreSQL database name")
    parser.add_argument("--table", type=str, default=None, help="Target table name (defaults to file/sheet name)")
    parser.add_argument("--sheet", type=str, default=None, help="Specific sheet name for Excel workbooks")
    parser.add_argument(
        "--all-sheets",
        action="store_true",
        help="Import ALL sheets from an Excel workbook as separate relational tables",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="replace",
        choices=["replace", "fail", "append"],
        help="Conflict mode: replace (default), fail, or append",
    )

    args = parser.parse_args()
    data_file = Path(args.file_path)

    if not data_file.exists():
        logger.error(f"File not found: {data_file}")
        sys.exit(1)

    settings = get_settings()
    db_name = args.db or settings.DB_NAME

    logger.info(f"Reading {data_file.name} ({data_file.stat().st_size} bytes)...")
    with open(data_file, "rb") as f:
        file_bytes = f.read()

    # If --all-sheets requested for Excel
    if args.all_sheets:
        if not is_excel_file(data_file.name, file_bytes):
            logger.error("--all-sheets option can only be used with Excel workbooks (.xlsx, .xls).")
            sys.exit(1)

        logger.info(f"Batch importing ALL sheets from {data_file.name} into database '{db_name}'...")
        batch_res = csv_ingestion_service.ingest_all_sheets(
            file_bytes=file_bytes,
            filename=data_file.name,
            db_name=db_name,
            mode=args.mode,
        )

        logger.info("==================================================")
        logger.info(f"SUCCESS! Ingested {len(batch_res['tables'])} tables ({batch_res['total_rows_inserted']} total rows):")
        for t in batch_res["tables"]:
            logger.info(f"  • Sheet '{t.get('sheet_name')}' -> Table '{t['table']}': {t['rows_inserted']} rows")
        logger.info("==================================================")
        return

    # Single sheet or CSV flow
    preview = csv_ingestion_service.parse_and_preview(
        file_bytes,
        filename=data_file.name,
        sheet_name=args.sheet,
    )

    if preview.get("is_excel") and preview.get("sheet_names"):
        logger.info(f"Excel workbook detected with sheets: {', '.join(preview['sheet_names'])}")
        logger.info(f"Active Sheet: {preview['active_sheet']}")

    table_name = args.table or preview["suggested_table_name"]

    logger.info(f"Detected {preview['total_columns']} columns for '{table_name}':")
    for col in preview["columns"]:
        logger.info(f"  • {col['sanitized_name']}: {col['inferred_type']}")

    logger.info(f"Starting streaming COPY into '{db_name}.{table_name}' (mode: {args.mode})...")
    result = csv_ingestion_service.ingest_csv(
        file_bytes=file_bytes,
        table_name=table_name,
        db_name=db_name,
        mode=args.mode,
        sheet_name=preview.get("active_sheet"),
        filename=data_file.name,
    )

    logger.info("==================================================")
    logger.info(f"SUCCESS! Streamed {result['rows_inserted']} rows into {result['database']}.{result['table']}")
    logger.info("==================================================")


if __name__ == "__main__":
    main()
