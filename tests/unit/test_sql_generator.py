from app.services.sql_generator import SqlGeneratorService


def test_generator_table_and_column_selection():
    schema = {
        "products": ["product_id", "product_name", "price", "stock"],
        "customers": ["customer_id", "name", "email"],
    }
    sql = SqlGeneratorService.generate_sql("list products and their price", schema)
    assert "products" in sql
    assert "price" in sql
    assert "LIMIT" in sql


def test_generator_enforces_limit_when_missing():
    schema = {"orders": ["order_id", "total_amount"]}
    sql = SqlGeneratorService.generate_sql("show orders", schema)
    assert "LIMIT 10" in sql


def test_generator_count_query():
    schema = {"orders": ["order_id", "total_amount"]}
    sql = SqlGeneratorService.generate_sql("how many orders are there", schema)
    assert "COUNT(*)" in sql
