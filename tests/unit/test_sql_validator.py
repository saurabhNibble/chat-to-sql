from app.services.sql_validator import SqlValidator, validate_sql


def test_validator_valid_select():
    sql = "SELECT id, name FROM customers WHERE id = 1 LIMIT 10;"
    is_valid, error = SqlValidator.validate_query(sql)
    assert is_valid
    assert error is None
    assert validate_sql(sql)


def test_validator_valid_with_cte():
    sql = "WITH top_cust AS (SELECT customer_id FROM orders) SELECT * FROM top_cust LIMIT 10;"
    is_valid, error = SqlValidator.validate_query(sql)
    assert is_valid
    assert error is None


def test_validator_reject_insert():
    sql = "INSERT INTO customers (name) VALUES ('Hacker');"
    is_valid, error = SqlValidator.validate_query(sql)
    assert not is_valid
    assert "Forbidden" in error or "SELECT" in error


def test_validator_reject_drop():
    sql = "DROP TABLE customers;"
    is_valid, error = SqlValidator.validate_query(sql)
    assert not is_valid


def test_validator_reject_delete():
    sql = "DELETE FROM customers WHERE id = 1;"
    is_valid, error = SqlValidator.validate_query(sql)
    assert not is_valid


def test_validator_reject_update():
    sql = "UPDATE products SET price = 0;"
    is_valid, error = SqlValidator.validate_query(sql)
    assert not is_valid


def test_validator_reject_multi_statement():
    sql = "SELECT * FROM customers; DROP TABLE orders;"
    is_valid, error = SqlValidator.validate_query(sql)
    assert not is_valid
    assert "Multi-statement" in error


def test_validator_reject_select_into():
    sql = "SELECT * INTO new_table FROM customers;"
    is_valid, error = SqlValidator.validate_query(sql)
    assert not is_valid


def test_validator_reject_forbidden_function():
    sql = "SELECT pg_sleep(10) FROM customers;"
    is_valid, error = SqlValidator.validate_query(sql)
    assert not is_valid
    assert "pg_sleep" in error
