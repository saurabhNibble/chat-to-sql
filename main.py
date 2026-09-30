"""
Text-to-SQL Clarification Engine API Entrypoint.
This module delegates to the enterprise modular application factory in app.main.
"""
from app.db import execute_readonly_sql, extract_schema, ping_database
from app.main import app, create_app
from app.services import check_clarification, generate_sql, validate_sql

__all__ = [
    "app",
    "create_app",
    "extract_schema",
    "execute_readonly_sql",
    "ping_database",
    "check_clarification",
    "generate_sql",
    "validate_sql",
]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
