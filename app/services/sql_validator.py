import re

import sqlglot
from sqlglot import exp

# Blacklisted AST expressions that perform mutation, DDL, or administrative tasks
FORBIDDEN_EXPRESSION_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.TruncateTable,
    exp.Into,          # Disallow SELECT ... INTO
    exp.Command,
    exp.Set,
    exp.Transaction,
    exp.Commit,
    exp.Rollback,
    exp.Grant,
    exp.Revoke,
)

# Dangerous database internal functions
FORBIDDEN_FUNCTIONS: set[str] = {
    "pg_sleep",
    "pg_read_file",
    "pg_read_binary_file",
    "pg_write_file",
    "pg_write_binary_file",
    "dblink",
    "dblink_exec",
    "lo_export",
    "lo_import",
    "system",
    "eval",
}


class SqlValidator:
    """Enterprise-grade SQL safety validation using Abstract Syntax Tree (AST) analysis."""

    @staticmethod
    def validate_query(sql: str) -> tuple[bool, str | None]:
        if not isinstance(sql, str) or not sql.strip():
            return False, "Query cannot be empty."

        clean_sql = sql.strip().rstrip(";")

        # Basic preliminary regex check
        if not re.match(r"^(SELECT|WITH)\b", clean_sql, flags=re.IGNORECASE):
            return False, "Query must begin with a SELECT or WITH statement."

        try:
            parsed_statements = sqlglot.parse(clean_sql, read="postgres")
        except Exception as exc:
            clean_msg = re.sub(r"\x1b\[[0-9;]*[mK]", "", str(exc))
            if "Required keyword: 'this' missing for <class 'sqlglot.expressions.query.Where'>" in clean_msg:
                return False, "Incomplete SQL: Your WHERE clause is missing a condition expression (e.g., 'WHERE price > 450')."
            return False, f"Failed to parse SQL: {clean_msg}"

        if not parsed_statements:
            return False, "No valid SQL statement found."

        # Strictly disallow multi-statement queries (e.g. SELECT 1; DROP TABLE users;)
        if len(parsed_statements) > 1:
            return False, "Multi-statement execution is strictly prohibited."

        statement = parsed_statements[0]
        if statement is None:
            return False, "Unable to inspect SQL statement structure."

        # The root statement must be a Select or Union
        if not isinstance(statement, (exp.Select, exp.Union)):
            return False, f"Statement type '{type(statement).__name__}' is not permitted. Only read-only queries are allowed."

        # Traverse AST for forbidden mutation or DDL operations
        for node in statement.walk():
            if isinstance(node, FORBIDDEN_EXPRESSION_TYPES):
                return False, f"Forbidden SQL operation detected: {type(node).__name__}."

            if isinstance(node, exp.Anonymous):
                func_name = (node.this or "").lower()
                if func_name in FORBIDDEN_FUNCTIONS:
                    return False, f"Forbidden function call detected: '{func_name}'."

        return True, None


def validate_sql(sql: str) -> bool:
    """Convenience wrapper compatible with legacy calls."""
    is_valid, _ = SqlValidator.validate_query(sql)
    return is_valid
