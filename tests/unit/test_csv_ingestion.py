import pytest

from app.services.csv_ingestion import (
    deduplicate_identifiers,
    infer_column_type,
    sanitize_identifier,
    CsvIngestionService,
)


def test_sanitize_identifier():
    assert sanitize_identifier("Customer Name") == "customer_name"
    assert sanitize_identifier("Order ID (#)") == "order_id"
    assert sanitize_identifier("123abc") == "col_123abc"
    assert sanitize_identifier("Price ($ USD)") == "price_usd"
    assert sanitize_identifier("  --bad-symbols!!--  ") == "bad_symbols"
    assert sanitize_identifier("") == "col_1"


def test_deduplicate_identifiers():
    cols = ["id", "name", "id", "id", "price"]
    deduped = deduplicate_identifiers(cols)
    assert deduped == ["id", "name", "id_2", "id_3", "price"]


def test_infer_column_type_boolean():
    assert infer_column_type(["true", "false", "true"]) == "BOOLEAN"
    assert infer_column_type(["yes", "no", "yes"]) == "BOOLEAN"
    assert infer_column_type(["t", "f"]) == "BOOLEAN"


def test_infer_column_type_integer():
    assert infer_column_type(["1", "25", "-40", "999"]) == "INTEGER"
    # Large 64-bit int
    assert infer_column_type(["3000000000", "4000000000"]) == "BIGINT"


def test_infer_column_type_numeric():
    assert infer_column_type(["19.99", "100.50", "-5.25"]) == "NUMERIC"


def test_infer_column_type_leading_zeros_preserved_as_text():
    # Zip codes, phone numbers, or account numbers starting with 0 must not become integers!
    assert infer_column_type(["01234", "05678", "09999"]) == "TEXT"


def test_infer_column_type_dates_and_timestamps():
    assert infer_column_type(["2025-01-15", "2025-06-30"]) == "DATE"
    assert infer_column_type(["2025-01-15 14:30:00", "2025-06-30T10:00:00Z"]) == "TIMESTAMPTZ"


def test_infer_column_type_uuid():
    assert infer_column_type(["550e8400-e29b-41d4-a716-446655440000"]) == "UUID"


def test_parse_and_preview():
    csv_bytes = b"Product Name,Price,In Stock,Release Date\nLaptop,999.99,true,2025-01-10\nPhone,499.00,false,2025-02-15\n"
    service = CsvIngestionService()
    preview = service.parse_and_preview(csv_bytes, filename="Products List.csv")

    assert preview["suggested_table_name"] == "products_list"
    assert preview["total_columns"] == 4
    assert len(preview["columns"]) == 4

    col_map = {c["sanitized_name"]: c["inferred_type"] for c in preview["columns"]}
    assert col_map["product_name"] == "TEXT"
    assert col_map["price"] == "NUMERIC"
    assert col_map["in_stock"] == "BOOLEAN"
    assert col_map["release_date"] == "DATE"
    assert len(preview["sample_rows"]) == 2
