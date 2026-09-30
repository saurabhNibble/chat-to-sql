"""Seed database script for ChatSQL Pro cloud deployment.

Executes schema_seed.sql against the configured database (DATABASE_URL or individual DB parameters).
"""

import sys
from pathlib import Path

import psycopg2

from app.core.config import get_settings
from app.core.logging import logger


def seed():
    settings = get_settings()
    seed_file = Path(__file__).resolve().parent / "schema_seed.sql"
    if not seed_file.exists():
        logger.error(f"Seed file not found at {seed_file}")
        sys.exit(1)

    with open(seed_file, encoding="utf-8") as f:
        sql_content = f.read()

    logger.info("Connecting to target PostgreSQL database...")
    try:
        if settings.DATABASE_URL:
            masked = settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "DSN"
            logger.info(f"Using DATABASE_URL -> {masked}")
            conn = psycopg2.connect(dsn=settings.DATABASE_URL)
        else:
            logger.info(f"Using host={settings.DB_HOST} db={settings.DB_NAME}")
            conn = psycopg2.connect(
                dbname=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
            )

        conn.autocommit = True
        with conn.cursor() as cur:
            logger.info("Executing schema_seed.sql statements...")
            cur.execute(sql_content)
        conn.close()
        logger.info("Database successfully seeded with schema, indexes, and sample data!")
    except Exception as exc:
        logger.error(f"Failed to seed database: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    seed()
