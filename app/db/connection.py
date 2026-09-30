from collections.abc import Generator
from contextlib import contextmanager

from psycopg2 import pool
from psycopg2.extensions import connection as PgConnection

from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

_pool: pool.ThreadedConnectionPool | None = None


def init_db_pool() -> pool.ThreadedConnectionPool:
    global _pool
    if _pool is None or _pool.closed:
        if settings.DATABASE_URL:
            # Mask credentials when logging
            masked_url = settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "configured DSN"
            logger.info(
                f"Initializing PostgreSQL connection pool ({settings.DB_POOL_MIN_CONN}-{settings.DB_POOL_MAX_CONN} connections) via DATABASE_URL to {masked_url}"
            )
            _pool = pool.ThreadedConnectionPool(
                minconn=settings.DB_POOL_MIN_CONN,
                maxconn=settings.DB_POOL_MAX_CONN,
                dsn=settings.DATABASE_URL,
            )
        else:
            logger.info(
                f"Initializing PostgreSQL connection pool ({settings.DB_POOL_MIN_CONN}-{settings.DB_POOL_MAX_CONN} connections) to {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            )
            _pool = pool.ThreadedConnectionPool(
                minconn=settings.DB_POOL_MIN_CONN,
                maxconn=settings.DB_POOL_MAX_CONN,
                dbname=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
            )
    return _pool


def close_db_pool() -> None:
    global _pool
    if _pool is not None and not _pool.closed:
        logger.info("Closing PostgreSQL connection pool")
        _pool.closeall()
        _pool = None


def get_pool() -> pool.ThreadedConnectionPool:
    if _pool is None or _pool.closed:
        return init_db_pool()
    return _pool


@contextmanager
def get_db_connection() -> Generator[PgConnection, None, None]:
    """Provide a pooled connection, returning it to the pool when finished."""
    current_pool = get_pool()
    conn = current_pool.getconn()
    try:
        yield conn
    finally:
        current_pool.putconn(conn)


@contextmanager
def get_readonly_connection() -> Generator[PgConnection, None, None]:
    """
    Provide a pooled connection strictly configured in READ ONLY mode with a statement timeout.
    This guarantees defense-in-depth at the database session level.
    """
    current_pool = get_pool()
    conn = current_pool.getconn()
    try:
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor() as cursor:
            cursor.execute(f"SET statement_timeout = {settings.DB_STATEMENT_TIMEOUT_MS};")
        yield conn
    finally:
        try:
            # Reset connection state before returning to pool
            conn.set_session(readonly=False, autocommit=False)
        except Exception:
            pass
        current_pool.putconn(conn)


def ping_database() -> bool:
    """Check database liveness."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
                row = cursor.fetchone()
                return row is not None and row[0] == 1
    except Exception as exc:
        logger.warning(f"Database ping failed: {exc}")
        return False
