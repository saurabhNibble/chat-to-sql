"""
CLI tool for automated CSV to PostgreSQL ingestion.

Usage:
    python scripts/import_csv.py <path_to_csv> [--db DB_NAME] [--table TABLE_NAME] [--mode replace|fail|append]
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings
from app.core.logging import logger
from app.services.csv_ingestion import csv_ingestion_service


def main():
    parser = argparse.ArgumentParser(
        description="Auto-detect schema and stream CSV data into PostgreSQL."
    )
    parser.add_argument("csv_path", type=str, help="Path to the .csv file")
    parser.add_argument("--db", type=str, default=None, help="Target PostgreSQL database name")
    parser.add_argument("--table", type=str, default=None, help="Target table name (defaults to CSV base name)")
    parser.add_argument(
        "--mode",
        type=str,
        default="replace",
        choices=["replace", "fail", "append"],
        help="Conflict mode: replace (default), fail, or append",
    )

    args = parser.parse_args()
    csv_file = Path(args.csv_path)

    if not csv_file.exists():
        logger.error(f"File not found: {csv_file}")
        sys.exit(1)

    settings = get_settings()
    db_name = args.db or settings.DB_NAME
    table_name = args.table or csv_file.stem

    logger.info(f"Reading {csv_file.name} ({csv_file.stat().st_size} bytes)...")
    with open(csv_file, "rb") as f:
        file_bytes = f.read()

    # Step 1: Preview & Auto-detect
    logger.info("Detecting columns and inferring PostgreSQL data types...")
    preview = csv_ingestion_service.parse_and_preview(file_bytes, filename=csv_file.name)
    logger.info(f"Detected {preview['total_columns']} columns:")
    for col in preview["columns"]:
        logger.info(f"  • {col['sanitized_name']}: {col['inferred_type']}")

    # Step 2: Ingest
    logger.info(f"Starting streaming COPY into '{db_name}.{table_name}' (mode: {args.mode})...")
    result = csv_ingestion_service.ingest_csv(
        file_bytes=file_bytes,
        table_name=table_name,
        db_name=db_name,
        mode=args.mode,
    )

    logger.info("==================================================")
    logger.info(f"SUCCESS! Streamed {result['rows_inserted']} rows into {result['database']}.{result['table']}")
    logger.info("==================================================")


if __name__ == "__main__":
    main()
